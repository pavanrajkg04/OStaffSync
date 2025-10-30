import datetime
import reflex as rx
from datetime import date, datetime, timezone, timedelta
from components import dashboard_navbar, admin_dash_side_nav
import duckdb

conn = duckdb.connect(database="hrms.duckdb")

# ---------- REUSABLE CARD COMPONENT ----------
def metric_card(icon_tag: str, value: rx.Var, label: str, change: str, color: str) -> rx.Component:
    """Reusable stats card for HR dashboard metrics."""
    return rx.card(
        rx.flex(
            rx.box(
                rx.icon(tag=icon_tag, color=f"{color}.600", size=22),
                bg=f"{color}.100",
                p="3",
                border_radius="full",
                mb="3",
            ),
            rx.heading(value, size="6", font_weight="bold", color="gray.800"),
            rx.text(label, font_size="2", color="gray.600"),
            rx.flex(
                rx.icon(tag="trending-up" if "▲" in change else "trending-down", size=12),
                rx.text(
                    change.replace("▲ ", "").replace("▼ ", ""),
                    font_size="2",
                    font_weight="semibold",
                ),
                direction="row",
                align="center",
                gap="1",
                mt="1",
            ),
            direction="column",
            align="center",
            justify="center",
            gap="1",
            p="4",
        ),
        bg="white",
        shadow="sm",
        border_radius="10",
        width="250px",
        height="200px",
        text_align="center",
        _hover={
            "shadow": "md",
            "transform": "scale(1.03)",
            "transition": "all 0.25s ease",
        },
    )


# ---------- STATE CLASS ----------
class AdminDashboardState(admin_dash_side_nav.AdminState):
    """Stateful HR Admin Dashboard."""
    date_now: datetime = datetime.now(timezone.utc)
    isLogin: bool = True

    # Dashboard metrics
    Total_Employees: int = 0
    New_Hires: int = 0
    Attrition: int = 0
    Leave_Requests: int = 0
    Attendance_Rate: float = 0.0
    Departments: int = 0

    # Employee table data
    employees_data: list[dict] = []

    check_in: datetime | None = None
    check_out: datetime | None = None

    @rx.var
    def formatted_date(self) -> str:
        return self.date_now.strftime("%B %d, %Y")

    def on_mount(self):
        """Runs when the dashboard mounts."""
        print("Mounting dashboard...")
        self.sync_login_state()
        self.get_metrics()

    def sync_login_state(self):
        """Sync isLogin based on today's attendance record."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            return
        today_date = datetime.today().date()
        row = conn.execute(
            """
            SELECT check_in, check_out 
            FROM attendance 
            WHERE tenant_id = ? AND user_id = ? AND date = ?
            ORDER BY check_in DESC
            """,
            (self.tenant_id, self.user_id, today_date),
        ).fetchone()

        if row:
            self.check_in, self.check_out = row
            self.isLogin = self.check_out is None
        else:
            self.check_in = None
            self.check_out = None
            self.isLogin = False

    def LoginStateUpdate(self):
        """Toggle between check-in/check-out."""
        today_date = datetime.today().date()
        now_time = datetime.now()

        if not self.isLogin:
            conn.execute(
                "INSERT INTO attendance (tenant_id, user_id, date, status, check_in) VALUES (?, ?, ?, ?, ?)",
                (self.tenant_id, self.user_id, today_date, "present", now_time),
            )
            self.check_in = now_time
            self.isLogin = True
        else:
            self.check_out = now_time
            duration = self.check_out - self.check_in  # timedelta
            hours_worked = duration.total_seconds() / 3600  # convert to hours

            if hours_worked >= 5 and hours_worked <=7 :
                conn.execute(
                    "UPDATE attendance SET check_out = ?, status = ? WHERE tenant_id = ? AND user_id = ? AND date = ?",
                    (self.check_out, "Half day", self.tenant_id, self.user_id, today_date),
                )
            if hours_worked < 5:
                conn.execute(
                    "UPDATE attendance SET check_out = ?, status = ? WHERE tenant_id = ? AND user_id = ? AND date = ?",
                    (self.check_out, "absent", self.tenant_id, self.user_id, today_date),
                )
            conn.execute(
                "UPDATE attendance SET check_out = ? WHERE tenant_id = ? AND user_id = ? AND date = ?",
                (now_time, self.tenant_id, self.user_id, today_date),
            )
            self.check_out = now_time
            self.isLogin = False

        self.get_metrics()  # refresh dashboard after check-in/out

    def get_employees(self):
        """Fetch employee list with today's attendance status."""
        if not hasattr(self, "tenant_id") or not self.tenant_id:
            print("tenant_id not ready yet; skipping employees load")
            return

        today = date.today()
        rows = conn.execute(
                        """
                        SELECT 
                            u.user_id, 
                            u.name, 
                            u.email, 
                            u.role, 
                            u.date_joined,
                            a.check_in, 
                            a.check_out,
                            a.status
                        FROM users u
                        LEFT JOIN (
                            SELECT tenant_id, user_id, check_in, check_out, status
                            FROM attendance
                            WHERE date = ?
                            AND rowid IN (
                                SELECT MAX(rowid)  -- latest inserted row for that user
                                FROM attendance
                                WHERE date = ?
                                GROUP BY user_id
                            )
                        ) a ON u.user_id = a.user_id AND u.tenant_id = a.tenant_id
                        WHERE u.tenant_id = ? AND u.status = 'active'
                        ORDER BY u.name;
                        """,
                        (today, today, self.tenant_id)  # ✅ match all three placeholders
                    ).fetchall()


        data = []
        for row in rows:
            user_id, name, email, role, date_joined, check_in, check_out,status = row
            check_in_today = check_in is not None
            check_out_today = check_out is not None
            days_since = (today - date_joined.date()).days if date_joined else 0
            data.append({
                'name': name,
                'email': email,
                'role': role or 'N/A',
                'check_in': 'Yes' if check_in_today else 'No',
                'check_out': 'Yes' if check_out_today else 'No',
                'date_joined': date_joined.strftime('%Y-%m-%d') if date_joined else 'N/A',
                'days_since': days_since,
                'status': status
            })
        self.employees_data = data
        print(f"[EMPLOYEES] Loaded {len(data)} active employees for tenant {self.tenant_id}")

    def get_metrics(self, atenant_id=None):
        """Fetch metrics live from the database."""
        if atenant_id is None:
            atenant_id = str(self.tenant_id)
        if not atenant_id or atenant_id == "None":
            print("tenant_id not ready yet; skipping metrics load")
            return

        today = datetime.today()
        month_start = datetime(today.year, today.month, 1)

        # --- Total Employees ---
        self.Total_Employees = conn.execute(
            "SELECT COUNT(user_id) FROM users WHERE tenant_id = ?", (atenant_id,)
        ).fetchone()[0]

        # --- New Hires (this month) ---
        self.New_Hires = conn.execute(
            "SELECT COUNT(user_id) FROM users WHERE tenant_id = ? AND date_joined >= ?",
            (atenant_id, month_start),
        ).fetchone()[0]

        # --- Attrition ---
        self.Attrition = conn.execute(
            "SELECT COUNT(user_id) FROM users WHERE tenant_id = ? AND status = 'inactive'",
            (atenant_id,),
        ).fetchone()[0]

        # --- Departments ---
        self.Departments = conn.execute(
            "SELECT COUNT(dept_id) FROM departments WHERE tenant_id = ?", (atenant_id,)
        ).fetchone()[0]

        # --- Leave Requests (this month) ---
        self.Leave_Requests = conn.execute(
            "SELECT COUNT(leave_id) FROM leaves WHERE tenant_id = ? AND start_date >= ?",
            (atenant_id, month_start),
        ).fetchone()[0]

        # --- Attendance Rate (present days / total workdays) ---
        attendance_stats = conn.execute(
            """
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END),
                COUNT(*)
            FROM attendance
            WHERE tenant_id = ? AND date >= ?
            """,
            (atenant_id, month_start),
        ).fetchone()
        present_days, total_days = attendance_stats
        self.Attendance_Rate = round((present_days / total_days) * 100, 2) if total_days > 0 else 0.0

        print(
            f"[METRICS] Tenant={atenant_id}, Employees={self.Total_Employees}, "
            f"New Hires={self.New_Hires}, Attrition={self.Attrition}, "
            f"Leaves={self.Leave_Requests}, Attendance={self.Attendance_Rate}%, "
            f"Departments={self.Departments}"
        )

        # Load employee data after metrics
        self.get_employees()


# ---------- DASHBOARD PAGE ----------
def dashboard_page() -> rx.Component:
    """Main HR Admin Dashboard layout."""
    cards = [
        metric_card("users", AdminDashboardState.Total_Employees, "Total Employees", "▲ 0%", "blue"),
        metric_card("user-plus", AdminDashboardState.New_Hires, "New Hires (This Month)", "▲ 0%", "green"),
        metric_card("user-x", AdminDashboardState.Attrition, "Attrition", "▼ 1.1%", "red"),
        metric_card("calendar", AdminDashboardState.Leave_Requests, "Leave Requests", "▲ 0%", "purple"),
        metric_card("clock", AdminDashboardState.Attendance_Rate, "Attendance Rate %", "▲ 0%", "teal"),
    ]

    top_left_section = rx.hstack(
        rx.text(AdminDashboardState.formatted_date, font_weight="bold"),
        rx.button(
            rx.cond(
                AdminDashboardState.isLogin,
                rx.text("Sign-out", color="red"),
                rx.text("Sign-in", color="blue"),
            ),
            on_click=AdminDashboardState.LoginStateUpdate,
        ),
        rx.vstack(
            rx.text(f"Login time: {AdminDashboardState.check_in}"),
            rx.text(f"Logout time: {AdminDashboardState.check_out}"),
        ),
        align="end",
        spacing="4",
        mb="6",
    )

    table_content_for_employee_list = rx.vstack(
            rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Name", width="150px"),
                    rx.table.column_header_cell("Email", width="200px"),
                    rx.table.column_header_cell("Role", width="100px"),
                    rx.table.column_header_cell("Check-in Today", width="120px"),
                    rx.table.column_header_cell("Check-out Today", width="120px"),
                    rx.table.column_header_cell("status today",width='100px'),
                    rx.table.column_header_cell("Date of Joining", width="140px"),
                    rx.table.column_header_cell("Days Since Joining", width="140px"),
                )
            ),
            rx.table.body(
                rx.cond(
                    AdminDashboardState.employees_data.length() > 0,
                    rx.foreach(
                        AdminDashboardState.employees_data,
                        lambda emp: rx.table.row(
                            rx.table.row_header_cell(emp['name']),
                            rx.table.cell(emp['email']),
                            rx.table.cell(emp['role']),
                            rx.table.cell(emp['check_in']),
                            rx.table.cell(emp['check_out']),
                            rx.table.cell(emp['status']),
                            rx.table.cell(emp['date_joined']),
                            rx.table.cell(emp['days_since']),
                        ),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell(
                            rx.text("No active employees found."),
                            col_span=8,
                            text_align="center",
                            py="4",
                        )
                    ),
                )
            ),
            width="100%",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
            overflow_x="auto",
        ),
            spacing="2",
            mt="8",
        )



    main_content = rx.vstack(
        rx.text(AdminDashboardState.tenant_id),
        top_left_section,
        rx.grid(
            *cards,
            columns="repeat(auto-fit, minmax(230px, 1fr))",
            spacing="6",
            justify_items="center",
            width="100%",
        ),
        table_content_for_employee_list,
        p="8",
        border_radius="12",
        shadow="sm",
        width="100%",
    )

    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            admin_dash_side_nav.Sidebar(),
            rx.box(
                main_content,
                width="100%",
                height="100vh",
                overflow_y="auto",
                p="6",
                on_mount=AdminDashboardState.on_mount,
            ),
            align="start",
            width="100%",
        ),
        spacing="0",
    )
