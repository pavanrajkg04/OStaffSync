# admin_attendance_dashboard.py
import datetime
from datetime import date, timedelta
import reflex as rx
from components import dashboard_navbar, admin_dash_side_nav
import duckdb

# ---------------- DATABASE CONNECTION ----------------
conn = duckdb.connect(database="hrms.duckdb")


# ---------- REUSABLE CARD COMPONENT ----------
def metric_card(icon_tag: str, value: rx.Var | str | int | float, label: str, color: str) -> rx.Component:
    value_display = value.to_string() if hasattr(value, "to_string") else str(value)
    return rx.card(
        rx.flex(
            rx.box(
                rx.icon(tag=icon_tag, color=f"{color}.600", size=22),
                bg=f"{color}.100",
                p="3",
                border_radius="full",
                mb="3",
            ),
            rx.heading(value_display, size="6", font_weight="bold", color="gray.800"),
            rx.text(label, font_size="2", color="gray.600"),
            direction="column",
            align="center",
            justify="center",
            gap="1",
            p="4",
        ),
        bg="white",
        shadow="sm",
        border_radius="12",
        width="220px",
        height="150px",
        text_align="center",
        _hover={"shadow": "md", "transform": "scale(1.03)", "transition": "all 0.25s ease"},
    )


# ---------- ATTENDANCE DASHBOARD STATE ----------
class AttendanceDashboardState(admin_dash_side_nav.AdminState):
    date_selected: str = date.today().strftime("%Y-%m-%d")
    attendance_data: list[dict] = []

    selected_user_id: int | None = None
    selected_user_name: str = ""
    monthly_attendance: list[dict] = []

    start_date: str = date.today().replace(day=1).strftime("%Y-%m-%d")
    end_date: str = date.today().strftime("%Y-%m-%d")
    report_data: list[dict] = []
    show_report: bool = False

    total_employees: int = 0
    present_today: int = 0
    absent_today: int = 0
    attendance_rate: float = 0.0

    # Leave management
    leave_requests: list[dict] = []

    # ----------------- Reactive helpers -----------------
    @rx.var
    def formatted_date(self) -> str:
        dt = datetime.datetime.strptime(self.date_selected, "%Y-%m-%d").date()
        return dt.strftime("%B %d, %Y")

    @rx.var
    def current_month(self) -> str:
        dt = datetime.datetime.strptime(self.date_selected, "%Y-%m-%d").date()
        return dt.strftime("%B %Y")

    @rx.var
    def monthly_header(self) -> str:
        return f"Monthly Attendance for {self.selected_user_name or '—'} - {self.current_month}"

    # ----------------- Lifecycle / Actions -----------------
    def on_mount(self):
        self.load_attendance()
        self.load_leave_requests()

    def on_date_change(self, new_date: str):
        self.date_selected = new_date
        self.selected_user_id = None
        self.selected_user_name = ""
        self.monthly_attendance = []
        self.load_attendance()

    def set_selected_user_id(self, value):
        try:
            if value is None or value == "":
                self.selected_user_id = None
                self.selected_user_name = ""
                self.monthly_attendance = []
                return
            user_id = int(value)
        except Exception:
            self.selected_user_id = None
            self.selected_user_name = ""
            self.monthly_attendance = []
            return

        self.selected_user_id = user_id
        for emp in self.attendance_data:
            if emp.get("user_id") == user_id:
                self.selected_user_name = emp.get("name", "")
                break
        self.get_monthly_attendance()

    def set_start_date(self, value: str):
        self.start_date = value

    def set_end_date(self, value: str):
        self.end_date = value

    def generate_report(self):
        if not getattr(self, "tenant_id", None):
            print("[REPORT] tenant_id not set; cannot generate report.")
            return

        try:
            start_dt = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").date()
            end_dt = datetime.datetime.strptime(self.end_date, "%Y-%m-%d").date()
        except Exception as e:
            print("[REPORT] invalid date format:", e)
            return

        if end_dt < start_dt:
            print("[REPORT] end date must be >= start date")
            self.report_data = []
            self.show_report = False
            return

        total_days = (end_dt - start_dt).days + 1

        users_rows = conn.execute(
            "SELECT user_id, name, email, role FROM users WHERE tenant_id = ? AND status = 'active' ORDER BY name",
            (self.tenant_id,),
        ).fetchall()

        report = []
        for u in users_rows:
            user_id, name, email, role = u
            present_days = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE tenant_id = ? AND user_id = ? AND date >= ? AND date <= ?",
                (self.tenant_id, user_id, start_dt, end_dt),
            ).fetchone()[0]
            absent_days = total_days - present_days
            rate = round((present_days / total_days) * 100, 2) if total_days > 0 else 0.0

            if rate > 80:
                color = "green"
            elif rate >= 50:
                color = "orange"
            else:
                color = "red"

            report.append({
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": role or "N/A",
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": absent_days,
                "attendance_rate": f"{rate}%",
                "attendance_rate_pct": rate,
                "rate_color": color,
            })

        self.report_data = report
        self.show_report = True
        print(f"[REPORT] Generated: {len(report)} rows for {start_dt} to {end_dt}")

    # ----------------- Attendance Methods -----------------
    def load_attendance(self):
        if not getattr(self, "tenant_id", None):
            print("[LOAD] tenant_id not set; skip loading attendance.")
            return

        try:
            target_date = datetime.datetime.strptime(self.date_selected, "%Y-%m-%d").date()
        except Exception as e:
            print("[LOAD] invalid date_selected format:", e)
            return

        rows = conn.execute(
            """
            SELECT 
                u.user_id, u.name, u.email, u.role,
                a.check_in, a.check_out
            FROM users u
            LEFT JOIN (
                SELECT tenant_id, user_id, check_in, check_out
                FROM attendance
                WHERE date = ?
                AND rowid IN (
                    SELECT MAX(rowid) FROM attendance WHERE date = ? GROUP BY user_id
                )
            ) a ON u.user_id = a.user_id AND u.tenant_id = a.tenant_id
            WHERE u.tenant_id = ? AND u.status = 'active'
            ORDER BY u.name
            """,
            (target_date, target_date, self.tenant_id),
        ).fetchall()

        data = []
        present_count = 0
        for r in rows:
            user_id, name, email, role, check_in, check_out = r
            status = "Present" if check_in else "Absent"
            if status == "Present":
                present_count += 1
            data.append({
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": role or "N/A",
                "check_in": check_in.strftime("%H:%M:%S") if check_in else "-",
                "check_out": check_out.strftime("%H:%M:%S") if check_out else "-",
                "status": status
            })

        self.attendance_data = data
        self.total_employees = len(data)
        self.present_today = present_count
        self.absent_today = max(0, self.total_employees - present_count)
        self.attendance_rate = round((self.present_today / self.total_employees) * 100, 2) if self.total_employees else 0.0
        print(f"[LOAD] {len(data)} employees loaded for {target_date} (present: {present_count})")

    def get_monthly_attendance(self):
        if not getattr(self, "tenant_id", None) or not self.selected_user_id:
            self.monthly_attendance = []
            return

        try:
            sel_date = datetime.datetime.strptime(self.date_selected, "%Y-%m-%d").date()
        except Exception as e:
            print("[MONTHLY] invalid date_selected:", e)
            self.monthly_attendance = []
            return

        month_start = date(sel_date.year, sel_date.month, 1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(days=1)

        rows = conn.execute(
            """
            SELECT date, check_in, check_out, status
            FROM attendance
            WHERE tenant_id = ? AND user_id = ? AND date >= ? AND date <= ?
            ORDER BY date
            """,
            (self.tenant_id, self.selected_user_id, month_start, month_end),
        ).fetchall()

        row_map = {}
        for r in rows:
            r_date = r[0]
            if isinstance(r_date, str):
                try:
                    r_date_obj = datetime.datetime.strptime(r_date, "%Y-%m-%d").date()
                except Exception:
                    r_date_obj = r_date
            elif hasattr(r_date, "date") and not isinstance(r_date, date):
                r_date_obj = r_date.date()
            else:
                r_date_obj = r_date
            row_map[r_date_obj] = r

        data = []
        current = month_start
        while current <= month_end:
            dstr = current.strftime("%Y-%m-%d")
            if current in row_map:
                _, check_in, check_out, status = row_map[current]
                data.append({
                    "date": dstr,
                    "check_in": check_in.strftime("%H:%M") if check_in else "N/A",
                    "check_out": check_out.strftime("%H:%M") if check_out else "N/A",
                    "status": status or "Present",
                })
            else:
                data.append({
                    "date": dstr,
                    "check_in": "Absent",
                    "check_out": "N/A",
                    "status": "Absent",
                })
            current += timedelta(days=1)

        self.monthly_attendance = data
        print(f"[MONTHLY] Loaded {len(data)} days for user {self.selected_user_id}")

    # ----------------- Leave Management -----------------
    def load_leave_requests(self):
        if not getattr(self, "tenant_id", None):
            self.leave_requests = []
            return

        rows = conn.execute(
            """
            SELECT leave_id, user_id, type, start_date, end_date, status, requested_at
            FROM leaves
            WHERE tenant_id = ? AND status = 'pending'
            ORDER BY requested_at
            """,
            (self.tenant_id,)
        ).fetchall()

        data = []
        for r in rows:
            leave_id, user_id, ltype, start_date, end_date, status, requested_at = r
            user_name = conn.execute(
                "SELECT name FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            user_name = user_name[0] if user_name else "N/A"

            data.append({
                "leave_id": leave_id,
                "user_id": user_id,
                "user_name": user_name,
                "type": ltype,
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else "",
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                "status": status,
                "requested_at": requested_at.strftime("%Y-%m-%d %H:%M:%S") if requested_at else "",
            })

        self.leave_requests = data
        print(f"[LEAVES] Loaded {len(data)} pending requests")

    def approve_leave(self, leave_id: str):
        conn.execute(
            "UPDATE leaves SET status = 'approved' WHERE leave_id = ?",
            (leave_id,)
        )
        self.load_leave_requests()

    def reject_leave(self, leave_id: str):
        conn.execute(
            "UPDATE leaves SET status = 'rejected' WHERE leave_id = ?",
            (leave_id,)
        )
        self.load_leave_requests()


# ---------- UI COMPONENTS ----------
def attendance_metric_cards(state: AttendanceDashboardState):
    return rx.hstack(
        metric_card("users", state.total_employees, "Total Employees", "blue"),
        metric_card("check_check", state.present_today, "Present Today", "green"),
        metric_card("message_circle_warning", state.absent_today, "Absent Today", "red"),
        metric_card("clock", state.attendance_rate, "Attendance %", "teal"),
        spacing="6",
        wrap="wrap",
    )


def attendance_table(state: AttendanceDashboardState):
    return rx.cond(
        ~state.attendance_data,
        rx.text("No attendance data for this date.", font_size="2xl", py="6", text_align="center"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Name"),
                    rx.table.column_header_cell("Email"),
                    rx.table.column_header_cell("Role"),
                    rx.table.column_header_cell("Check-in"),
                    rx.table.column_header_cell("Check-out"),
                    rx.table.column_header_cell("Status"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    state.attendance_data,
                    lambda emp: rx.table.row(
                        rx.table.row_header_cell(emp["name"]),
                        rx.table.cell(emp["email"]),
                        rx.table.cell(emp["role"]),
                        rx.table.cell(emp["check_in"]),
                        rx.table.cell(emp["check_out"]),
                        rx.table.cell(
                            emp["status"],
                            color=rx.cond(emp["status"] == "Present", "green", "red"),
                            font_weight="bold",
                        ),
                        _hover={"bg": "gray.50"}
                    )
                )
            ),
            width="100%",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
            overflow_x="auto",
        )
    )


def monthly_attendance_section(state: AttendanceDashboardState):
    return rx.vstack(
        rx.cond(
            state.attendance_data,
            rx.hstack(
                rx.text("Select an employee to view monthly attendance:"),
                rx.select.root(
                    rx.select.trigger(placeholder="Choose an employee..."),
                    rx.select.content(
                        rx.select.group(
                            rx.foreach(
                                state.attendance_data,
                                lambda emp: rx.select.item(emp["name"], value=str(emp["user_id"]))
                            )
                        )
                    ),
                    value=rx.cond(state.selected_user_id, state.selected_user_id.to_string(), ""),
                    on_change=lambda val: state.set_selected_user_id(val),
                    width="260px",
                ),
                spacing="4",
                align="start",
            ),
            rx.text("No employees available to filter."),
        ),
        rx.cond(
            state.selected_user_id,
            rx.vstack(
                rx.heading(state.monthly_header, size="4", mb="4"),
                rx.cond(
                    ~state.monthly_attendance,
                    rx.text("No attendance data available.", font_size="lg", py="4", text_align="center"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Date", width="140px"),
                                rx.table.column_header_cell("Check-in", width="120px"),
                                rx.table.column_header_cell("Check-out", width="120px"),
                                rx.table.column_header_cell("Status", width="120px"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                state.monthly_attendance,
                                lambda day: rx.table.row(
                                    rx.table.cell(day["date"]),
                                    rx.table.cell(day["check_in"]),
                                    rx.table.cell(day["check_out"]),
                                    rx.table.cell(
                                        day["status"],
                                        color=rx.cond(day["status"] == "Present", "green",
                                                      rx.cond(day["status"] == "Half day", "orange", "red")),
                                    ),
                                    _hover={"bg": "gray.50"}
                                )
                            )
                        ),
                        width="100%",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                        overflow_x="auto",
                    )
                ),
                spacing="2",
                mt="6",
            ),
            rx.text("Select an employee to view monthly attendance.", font_size="lg", py="4")
        ),
        spacing="4",
        mt="4",
    )


def attendance_report_section(state: AttendanceDashboardState):
    return rx.vstack(
        rx.heading("Attendance Report Generator", size="4", mb="4"),
        rx.hstack(
            rx.text("Start Date:"),
            rx.input(type="date", value=state.start_date, on_change=state.set_start_date, width="160px"),
            rx.text("End Date:"),
            rx.input(type="date", value=state.end_date, on_change=state.set_end_date, width="160px"),
            rx.button("Generate Report", on_click=state.generate_report, color_scheme="blue"),
            spacing="4",
            align="center",
        ),
        rx.cond(
            state.show_report,
            rx.vstack(
                rx.heading(rx.text("Attendance Report: ", state.start_date, " to ", state.end_date), size="3", mb="3"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Name"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("Role"),
                            rx.table.column_header_cell("Total Days"),
                            rx.table.column_header_cell("Present Days"),
                            rx.table.column_header_cell("Absent Days"),
                            rx.table.column_header_cell("Attendance Rate"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            state.report_data,
                            lambda rep: rx.table.row(
                                rx.table.row_header_cell(rep["name"]),
                                rx.table.cell(rep["email"]),
                                rx.table.cell(rep["role"]),
                                rx.table.cell(rep["total_days"]),
                                rx.table.cell(rep["present_days"]),
                                rx.table.cell(rep["absent_days"]),
                                rx.table.cell(
                                    rep["attendance_rate"],
                                    color=rep["rate_color"],
                                    font_weight="bold",
                                ),
                                _hover={"bg": "gray.50"}
                            )
                        )
                    ),
                    width="100%",
                    border="1px solid",
                    border_color="gray.200",
                    border_radius="md",
                    overflow_x="auto",
                ),
                spacing="2",
                mt="4",
            ),
            rx.text("Generate a report by selecting dates and clicking the button.", text_align="center", py="4"),
        ),
        spacing="4",
        mt="8",
        p="4",
        bg="gray.50",
        border_radius="md",
    )


def leave_requests_section(state: AttendanceDashboardState):
    return rx.vstack(
        rx.heading("Pending Leave Requests", size="4", mb="4"),
        rx.cond(
            ~state.leave_requests,
            rx.text("No pending leave requests.", py="4", font_size="lg", text_align="center"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Employee"),
                        rx.table.column_header_cell("Type"),
                        rx.table.column_header_cell("Start Date"),
                        rx.table.column_header_cell("End Date"),
                        rx.table.column_header_cell("Requested At"),
                        rx.table.column_header_cell("Actions"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        state.leave_requests,
                        lambda leave: rx.table.row(
                            rx.table.row_header_cell(leave["user_name"]),
                            rx.table.cell(leave["type"]),
                            rx.table.cell(leave["start_date"]),
                            rx.table.cell(leave["end_date"]),
                            rx.table.cell(leave["requested_at"]),
                            rx.table.cell(
                                rx.hstack(
                                    rx.button("Approve", color_scheme="green",
                                              on_click=lambda l=leave["leave_id"]: state.approve_leave(l)),
                                    rx.button("Reject", color_scheme="red",
                                              on_click=lambda l=leave["leave_id"]: state.reject_leave(l)),
                                    spacing="2"
                                )
                            ),
                            _hover={"bg": "gray.50"}
                        )
                    )
                ),
                width="100%",
                border="1px solid",
                border_color="gray.200",
                border_radius="md",
                overflow_x="auto",
            )
        ),
        spacing="4",
        mt="6",
        p="4",
        bg="gray.50",
        border_radius="md",
    )


# ---------- PAGE ----------
def attendance_dashboard_page() -> rx.Component:
    state = AttendanceDashboardState

    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            admin_dash_side_nav.Sidebar(),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Attendance Dashboard - ", state.formatted_date, font_size="2xl", font_weight="bold"),
                        rx.spacer(),
                        rx.input(type="date", value=state.date_selected, on_change=state.on_date_change, width="200px"),
                        spacing="4",
                        align="center",
                    ),
                    attendance_metric_cards(state),
                    attendance_table(state),
                    monthly_attendance_section(state),
                    attendance_report_section(state),
                    leave_requests_section(state),  # ✅ New leave section
                    spacing="6",
                    p="6",
                ),
                width="100%",
                height="100vh",
                overflow_y="auto",
            ),
            spacing="4",
            align="start",
        ),
        spacing="0",
    )
