import datetime
import reflex as rx
import uuid
from datetime import date, datetime, timezone, timedelta
from components import dashboard_navbar, employee_dash_side_nav
import duckdb

conn = duckdb.connect(database="hrms.duckdb")

# ---------- REUSABLE CARD COMPONENT ----------
def metric_card(icon_tag: str, value: rx.Var, label: str, change: str, color: str) -> rx.Component:
    """Reusable stats card for metrics."""
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
class EmployeeLeavesState(employee_dash_side_nav.EmployeeState):
    """Stateful Employee Leaves Dashboard."""
    date_now: datetime = datetime.now(timezone.utc)

    # Leaves metrics
    Leaves_Taken: int = 0
    Leaves_Remaining: int = 0  # Assuming 20 annual entitlement
    Pending_Requests: int = 0

    # Leaves history data
    leaves_data: list[dict] = []

    # Form fields for new leave request
    leave_type: str = "Vacation"
    start_date: date = date.today()
    end_date: date = date.today() + timedelta(days=1)
    notes: str = ""

    @rx.var
    def formatted_date(self) -> str:
        return self.date_now.strftime("%B %d, %Y")

    @rx.var
    def formatted_start_date(self) -> str:
        return self.start_date.strftime('%Y-%m-%d')

    @rx.var
    def formatted_end_date(self) -> str:
        return self.end_date.strftime('%Y-%m-%d')

    def set_leave_type(self, value: str):
        self.leave_type = value

    def set_start_date(self, value: str):
        if value:
            self.start_date = datetime.strptime(value, '%Y-%m-%d').date()

    def set_end_date(self, value: str):
        if value:
            self.end_date = datetime.strptime(value, '%Y-%m-%d').date()

    def set_notes(self, value: str):
        self.notes = value

    def on_mount(self):
        """Runs when the leaves page mounts."""
        print("Mounting employee leaves page...")
        self.get_leaves_metrics()
        self.get_leaves_history()

    def get_leaves_metrics(self):
        """Fetch personal leaves metrics."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            print("tenant_id or user_id not ready; skipping metrics")
            return

        today = datetime.today()
        year_start = datetime(today.year, 1, 1)

        self.Leaves_Taken = conn.execute(
            """
            SELECT COUNT(*) 
            FROM leaves 
            WHERE tenant_id = ? AND user_id = ? AND status = 'approved' AND start_date >= ?
            """,
            (self.tenant_id, self.user_id, year_start.date()),
        ).fetchone()[0]

        self.Leaves_Remaining = max(0, 20 - self.Leaves_Taken)

        self.Pending_Requests = conn.execute(
            """
            SELECT COUNT(*) 
            FROM leaves 
            WHERE tenant_id = ? AND user_id = ? AND status = 'pending'
            """,
            (self.tenant_id, self.user_id),
        ).fetchone()[0]

        print(f"[LEAVES METRICS] Taken={self.Leaves_Taken}, Remaining={self.Leaves_Remaining}, Pending={self.Pending_Requests}")

    def get_leaves_history(self):
        """Fetch personal leaves history."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            print("tenant_id or user_id not ready; skipping history")
            return

        rows = conn.execute(
            """
            SELECT leave_id, type, start_date, end_date, status, requested_at
            FROM leaves
            WHERE tenant_id = ? AND user_id = ?
            ORDER BY requested_at DESC
            """,
            (self.tenant_id, self.user_id),
        ).fetchall()

        data = []
        for row in rows:
            leave_id, leave_type, start_d, end_d, status, requested = row
            duration = (end_d - start_d).days + 1 if start_d and end_d else 0
            data.append({
                'id': leave_id,
                'type': leave_type or 'N/A',
                'start_date': start_d.strftime('%Y-%m-%d') if start_d else 'N/A',
                'end_date': end_d.strftime('%Y-%m-%d') if end_d else 'N/A',
                'duration': duration,
                'status': status or 'N/A',
                'requested': requested.strftime('%Y-%m-%d') if requested else 'N/A'
            })
        self.leaves_data = data
        print(f"[LEAVES HISTORY] Loaded {len(data)} records for user {self.user_id}")

    def submit_leave_request(self):
        """Submit a new leave request."""
        if not hasattr(self, "tenant_id") or not hasattr(self, "user_id"):
            print("tenant_id or user_id not ready; cannot submit")
            return

        leave_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO leaves (leave_id, tenant_id, user_id, type, start_date, end_date, status, requested_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', NOW())
            """,
            (leave_id, self.tenant_id, self.user_id, self.leave_type, 
             self.start_date, self.end_date),
        )
        print(f"[LEAVE REQUEST] Submitted {leave_id} for {self.user_id}")

        # Reset form
        self.leave_type = "Vacation"
        self.start_date = date.today()
        self.end_date = date.today() + timedelta(days=1)
        self.notes = ""

        # Refresh metrics and history
        self.get_leaves_metrics()
        self.get_leaves_history()


# ---------- LEAVES PAGE ----------
def employee_leaves_page() -> rx.Component:
    """Main Employee Leaves Page layout."""

    # Metrics Cards
    cards = [
        metric_card("calendar-x", EmployeeLeavesState.Leaves_Taken, "Leaves Taken (This Year)", "▼ 2.1%", "orange"),
        metric_card("calendar-check", EmployeeLeavesState.Leaves_Remaining, "Leaves Remaining", "▲ 18.0%", "green"),
        metric_card("clock", EmployeeLeavesState.Pending_Requests, "Pending Requests", "▲ 1", "yellow"),
    ]

    # Leaves History Table
    table_content = rx.vstack(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Type", width="120px"),
                    rx.table.column_header_cell("Start Date", width="120px"),
                    rx.table.column_header_cell("End Date", width="120px"),
                    rx.table.column_header_cell("Duration (Days)", width="140px"),
                    rx.table.column_header_cell("Status", width="100px"),
                    rx.table.column_header_cell("Requested", width="120px"),
                )
            ),
            rx.table.body(
                rx.cond(
                    EmployeeLeavesState.leaves_data.length() > 0,
                    rx.foreach(
                        EmployeeLeavesState.leaves_data,
                        lambda lv: rx.table.row(
                            rx.table.row_header_cell(lv['type']),
                            rx.table.cell(lv['start_date']),
                            rx.table.cell(lv['end_date']),
                            rx.table.cell(lv['duration']),
                            rx.table.cell(lv['status']),
                            rx.table.cell(lv['requested']),
                        ),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell(
                            rx.text("No leave records found."),
                            col_span=6,
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

    # New Leave Request Form
    form_section = rx.card(
        rx.heading("Request New Leave", size="6", mb="4"),
        rx.form(  # Wrap all fields in a single Form
            rx.vstack(
                rx.select(
                    EmployeeLeavesState.leave_type,
                    on_change=EmployeeLeavesState.set_leave_type,
                    placeholder="Select Leave Type",
                    options=["Vacation", "Sick Leave", "Personal", "Maternity/Paternity"],
                ),
                rx.hstack(
                    rx.form.field(
                        rx.form.label("Start Date"),
                        rx.input(
                            type="date",
                            value=EmployeeLeavesState.formatted_start_date,
                            on_change=EmployeeLeavesState.set_start_date
                        ),
                    ),
                    rx.form.field(
                        rx.form.label("End Date"),
                        rx.input(
                            type="date",
                            value=EmployeeLeavesState.formatted_end_date,
                            on_change=EmployeeLeavesState.set_end_date
                        ),
                    ),
                    spacing="4",
                ),
                rx.form.field(
                    rx.form.label("Notes (Optional)"),
                    rx.text_area(
                        EmployeeLeavesState.notes,
                        on_change=EmployeeLeavesState.set_notes,
                        rows="3"
                    ),
                ),
                rx.button(
                    "Submit Request",
                    on_click=EmployeeLeavesState.submit_leave_request,
                    color_scheme="blue",
                    width="full",
                ),
                spacing="4",
                align="stretch",
            )
        ),
        bg="white",
        shadow="sm",
        border_radius="md",
        p="6",
        mb="8",
    )

    main_content = rx.vstack(
        rx.text(f"Leaves Management - {EmployeeLeavesState.formatted_date}"),
        rx.grid(
            *cards,
            columns="repeat(auto-fit, minmax(230px, 1fr))",
            spacing="6",
            justify_items="center",
            width="100%",
        ),
        form_section,
        table_content,
        p="8",
        border_radius="12",
        shadow="sm",
        width="100%",
    )

    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            employee_dash_side_nav.Sidebar(),
            rx.box(
                main_content,
                width="100%",
                height="100vh",
                overflow_y="auto",
                p="6",
                on_mount=EmployeeLeavesState.on_mount,
            ),
            align="start",
            width="100%",
        ),
        spacing="0",
    )
