import datetime
import reflex as rx
from datetime import date, datetime, timezone, timedelta
from components import dashboard_navbar, admin_dash_side_nav
import duckdb

conn = duckdb.connect(database="hrms.duckdb")

# ---------- REUSABLE CARD COMPONENT ----------
def metric_card(icon_tag: str, value: rx.Component | str, label: str, change: str, color: str) -> rx.Component:
    """Reusable stats card for HR dashboard metrics."""
    return rx.card(
        rx.flex(
            # Icon at top
            rx.box(
                rx.icon(tag=icon_tag, color=f"{color}.600", size=22),
                bg=f"{color}.100",
                p="3",
                border_radius="full",
                mb="3",
            ),
            # Metric value
            rx.heading(value, size="6", font_weight="bold", color="gray.800"),
            # Label
            rx.text(label, font_size="2", color="gray.600"),
            # Change indicator
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
    date_now: datetime = datetime.now(timezone.utc)
    isLogin: bool = True
    Total_Employees: int = 0
    New_Hires: int = 0
    Attrition: int = 0
    Leave_Requests: int = 0
    Attendance_Rate: float = 0.0
    Departments: int = 0
    check_in: datetime = None
    check_out: datetime = None
    

    @rx.var
    def formatted_date(self) -> str:
        """Computed formatted date string."""
        return self.date_now.strftime("%B %d, %Y")

    def __init__(self, **data):
        super().__init__(**data)
        self.sync_login_state()
        # Removed self.get_metrics() from here -- too early in lifecycle

    def sync_login_state(self):
        """Sync isLogin based on today's attendance record."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            return  # tenant/user not set yet
        today_date = datetime.today().date()
        row = conn.execute(
            "SELECT check_in, check_out FROM attendance WHERE tenant_id = ? AND user_id = ? AND date = ?",
            (self.tenant_id, self.user_id, today_date)
        ).fetchone()
        if row:
            self.check_in = row[0]
            self.check_out = row[1]
            self.isLogin = self.check_out is None  # if checked in but no checkout, logged in
        else:
            self.check_in = None
            self.check_out = None
            self.isLogin = False  # no row yet, need to check in

    def LoginStateUpdate(self):
        """Toggle check-in/check-out based on isLogin."""
        today_date = datetime.today().date()
        now_time = datetime.now()
        
        if not self.isLogin:
            # Check-in
            conn.execute(
                "INSERT INTO attendance (tenant_id, user_id, date, check_in) VALUES (?, ?, ?, ?)",
                (self.tenant_id, self.user_id, today_date, now_time)
            )
            self.check_in = now_time
            self.check_out = None
            self.isLogin = True
        else:
            # Check-out
            conn.execute(
                "UPDATE attendance SET check_out = ? WHERE tenant_id = ? AND user_id = ? AND date = ?",
                (now_time, self.tenant_id, self.user_id, today_date)
            )
            self.check_out = now_time
            self.isLogin = False


    def get_metrics(self, atenant_id=None):
        """Fetch metrics from database."""
        if atenant_id is None:
            atenant_id = str(self.tenant_id)
        if not atenant_id or atenant_id == "None":  # Guard: skip if still unset
            print(f"tenant_id not ready yet; skipping metrics load")
            return
        today = datetime.today()
        month_start = datetime(today.year, today.month, 1)
        days_passed = (today - month_start).days + 1
        days_passed_this_month = datetime.today() - timedelta(days=days_passed)
        print(today,month_start,days_passed,days_passed_this_month)
        Total_Employees = conn.execute(
            "SELECT count(user_id) FROM users WHERE tenant_id = ?", (atenant_id,)
        ).fetchone()
        self.Total_Employees = Total_Employees[0] if Total_Employees else 0
        New_Hires = conn.execute(
            "SELECT count(user_id) from users WHERE tenant_id = ? and date_joined > ?", (atenant_id,month_start)
        ).fetchone()
        # TODO: Fetch other metrics similarly
        self.New_Hires = New_Hires[0] if New_Hires else 0
        self.Attrition = 3
        self.Leave_Requests = 48
        self.Attendance_Rate = 96
        self.Departments = 8
        print("printing results: ", New_Hires, atenant_id)

# ---------- DASHBOARD PAGE ----------
def dashboard_page() -> rx.Component:
    """Main HR Admin Dashboard layout."""
    # Create cards using state vars directly (reactive binding)
    cards = [
        metric_card("users", AdminDashboardState.Total_Employees, "Total Employees", "▲ 2.4%", "blue"),
        metric_card("user-plus", AdminDashboardState.New_Hires, "New Hires (This Month)", "▲ 8.3%", "green"),
        metric_card("user-x", AdminDashboardState.Attrition, "Attrition", "▼ 1.5%", "red"),
        metric_card("calendar", AdminDashboardState.Leave_Requests, "Leave Requests", "▲ 6.1%", "purple"),
        metric_card("clock", AdminDashboardState.Attendance_Rate, "Attendance Rate", "▲ 1.2%", "teal"),
        metric_card("briefcase", AdminDashboardState.Departments, "Departments", "—", "orange"),
    ]
    # Top-left corner section: date + login button
    top_left_section = rx.hstack(
        rx.text(AdminDashboardState.formatted_date, font_weight="bold", text_align="left"),
        rx.button(
            rx.cond(
                AdminDashboardState.isLogin,
                rx.text("Sign-in", color="blue"),
                rx.text("Sign-out", color="red"),
            ),
            on_click=AdminDashboardState.LoginStateUpdate,
        ),
        rx.text(f"Login time : {AdminDashboardState.check_in}"),
        rx.text(f"Logout time : {AdminDashboardState.check_out}"),
        align="end",
        spacing="4",
        mb="6",
    )

    # Main content: top-left + cards
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
        p="8",
        border_radius="12",
        shadow="sm",
        width="100%",
    )

    # Complete dashboard layout
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
                on_mount=AdminDashboardState.get_metrics,  # Trigger metrics load after mount (tenant_id now set)
            ),
            align="start",
            width="100%",
        ),
        spacing="0",
    )