import datetime
import reflex as rx
from datetime import date, datetime, timezone, timedelta
from components import dashboard_navbar, employee_dash_side_nav  # Assuming employee side nav exists or adapt
import duckdb

conn = duckdb.connect(database="hrms.duckdb")

# ---------- REUSABLE CARD COMPONENT ----------
# Reusing the same metric_card from admin dashboard
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
        shadow="2",
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
class EmployeeDashboardState(employee_dash_side_nav.EmployeeState):  # Assuming EmployeeState base
    """Stateful HR Employee Dashboard."""
    date_now: datetime = datetime.now(timezone.utc)
    isLogin: bool = True

    # Personal metrics
    My_Attendance_Rate: float = 0.0
    Leaves_Taken: int = 0
    Leaves_Remaining: int = 0  # Assuming annual leaves entitlement is 20, adjust as needed
    Present_Days_This_Month: int = 0

    # Attendance history data
    attendance_data: list[dict] = []

    check_in: datetime | None = None
    check_out: datetime | None = None

    @rx.var
    def formatted_date(self) -> str:
        return self.date_now.strftime("%B %d, %Y")

    def on_mount(self):
        """Runs when the dashboard mounts."""
        print("Mounting employee dashboard...")
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

    def get_attendance_history(self):
        """Fetch personal attendance history for the last 30 days."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            print("tenant_id or user_id not ready yet; skipping attendance load")
            return

        thirty_days_ago = date.today() - timedelta(days=30)
        rows = conn.execute(
            """
            SELECT date, check_in, check_out, status
            FROM attendance
            WHERE tenant_id = ? AND user_id = ? AND date >= ?
            ORDER BY date DESC
            """,
            (self.tenant_id, self.user_id, thirty_days_ago),
        ).fetchall()

        data = []
        for row in rows:
            date_str, check_in, check_out, status = row
            data.append({
                'date': date_str.strftime('%Y-%m-%d') if isinstance(date_str, date) else str(date_str),
                'check_in': check_in.strftime('%H:%M') if check_in else 'N/A',
                'check_out': check_out.strftime('%H:%M') if check_out else 'N/A',
                'status': status or 'N/A',
                'hours_worked': 'N/A'  # Can calculate if needed: (check_out - check_in).total_seconds() / 3600
            })
        self.attendance_data = data
        print(f"[ATTENDANCE] Loaded {len(data)} records for user {self.user_id}")

    def get_metrics(self):
        """Fetch personal metrics live from the database."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            print("tenant_id or user_id not ready yet; skipping metrics load")
            return

        today = datetime.today()
        month_start = datetime(today.year, today.month, 1)
        year_start = datetime(today.year, 1, 1)

        # --- Present Days This Month ---
        self.Present_Days_This_Month = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE tenant_id = ? AND user_id = ? AND status = 'present' AND date >= ?",
            (self.tenant_id, self.user_id, month_start),
        ).fetchone()[0]

        # --- Attendance Rate This Month ---
        total_days = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE tenant_id = ? AND user_id = ? AND date >= ?",
            (self.tenant_id, self.user_id, month_start),
        ).fetchone()[0]
        self.My_Attendance_Rate = round((self.Present_Days_This_Month / total_days) * 100, 2) if total_days > 0 else 0.0

        # --- Leaves Taken This Year ---
        self.Leaves_Taken = conn.execute(
            "SELECT COUNT(*) FROM leaves WHERE tenant_id = ? AND user_id = ? AND status = 'approved' AND start_date >= ?",
            (self.tenant_id, self.user_id, year_start),
        ).fetchone()[0]

        # --- Leaves Remaining (assuming 20 annual entitlement) ---
        self.Leaves_Remaining = 20 - self.Leaves_Taken  # Hardcoded; make dynamic if entitlement in DB

        print(
            f"[METRICS] User={self.user_id}, Present Days={self.Present_Days_This_Month}, "
            f"Attendance Rate={self.My_Attendance_Rate}%, Leaves Taken={self.Leaves_Taken}, "
            f"Leaves Remaining={self.Leaves_Remaining}"
        )

        # Load attendance data after metrics
        self.get_attendance_history()


# ---------- EMPLOYEE DASHBOARD PAGE ----------
def employee_dashboard_page() -> rx.Component:
    """Main HR Employee Dashboard layout."""
    cards = [
        metric_card("clock", EmployeeDashboardState.Present_Days_This_Month, "Present Days (This Month)", "▲ 3.2%", "blue"),
        metric_card("calendar-x", EmployeeDashboardState.Leaves_Taken, "Leaves Taken (This Year)", "▼ 2.1%", "orange"),
        metric_card("calendar-check", EmployeeDashboardState.Leaves_Remaining, "Leaves Remaining", "▲ 18.0%", "green"),
        metric_card("activity", EmployeeDashboardState.My_Attendance_Rate, "My Attendance Rate %", "▲ 0.8%", "teal"),
    ]

    top_left_section = rx.hstack(
        rx.text(EmployeeDashboardState.formatted_date, font_weight="bold"),
        rx.button(
            rx.cond(
                EmployeeDashboardState.isLogin,
                rx.text("Sign-out", color="red"),
                rx.text("Sign-in", color="blue"),
            ),
            on_click=EmployeeDashboardState.LoginStateUpdate,
        ),
        rx.vstack(
            rx.text(f"Login time: {EmployeeDashboardState.check_in}"),
            rx.text(f"Logout time: {EmployeeDashboardState.check_out}"),
        ),
        align="end",
        spacing="4",
        mb="6",
    )

    table_content_for_attendance_history = rx.vstack(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date", width="120px"),
                    rx.table.column_header_cell("Check-in", width="100px"),
                    rx.table.column_header_cell("Check-out", width="100px"),
                    rx.table.column_header_cell("Status", width="100px"),
                    rx.table.column_header_cell("Hours Worked", width="120px"),
                )
            ),
            rx.table.body(
                rx.cond(
                    EmployeeDashboardState.attendance_data.length() > 0,
                    rx.foreach(
                        EmployeeDashboardState.attendance_data,
                        lambda att: rx.table.row(
                            rx.table.row_header_cell(att['date']),
                            rx.table.cell(att['check_in']),
                            rx.table.cell(att['check_out']),
                            rx.table.cell(att['status']),
                            rx.table.cell(att['hours_worked']),
                        ),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell(
                            rx.text("No attendance records found."),
                            col_span=5,
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
        rx.text(f"Welcome, {EmployeeDashboardState.user_id}!"),  # Personal greeting; enhance with name from DB if needed
        top_left_section,
        rx.grid(
            *cards,
            columns="repeat(auto-fit, minmax(230px, 1fr))",
            spacing="6",
            justify_items="center",
            width="100%",
        ),
        table_content_for_attendance_history,
        p="8",
        border_radius="12",
        shadow="2",
        width="100%",
    )

    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            employee_dash_side_nav.Sidebar(),  # Assuming employee side nav
            rx.box(
                main_content,
                width="100%",
                height="100vh",
                overflow_y="auto",
                p="6",
                on_mount=EmployeeDashboardState.on_mount,
            ),
            align="start",
            width="100%",
        ),
        spacing="0",
    )



