import uuid
import reflex as rx
import duckdb
from datetime import date, datetime
from components import dashboard_navbar, admin_dash_side_nav

# ---------------- DATABASE CONNECTION ----------------
conn = duckdb.connect(database="hrms.duckdb")


# ---------------- METRIC CARD COMPONENT ----------------
def metric_card(icon_tag: str, value: str | float, label: str, color: str) -> rx.Component:
    """Reusable metric card."""
    return rx.card(
        rx.flex(
            rx.icon(tag=icon_tag, color=f"{color}.600", size=22),
            rx.box(
                rx.heading(str(value), size="6", font_weight="bold", color="gray.800"),
                rx.text(label, font_size="2", color="gray.600"),
            ),
            direction="column",
            align="center",
            justify="center",
            p="4",
            gap="2",
        ),
        bg="white",
        shadow="sm",
        border_radius="12",
        width="230px",
        height="140px",
        _hover={"shadow": "md", "transform": "scale(1.03)", "transition": "all 0.25s ease"},
    )


# ---------------- PAYROLL DASHBOARD STATE ----------------
class PayrollDashboardState(admin_dash_side_nav.AdminState):
    """State for admin payroll operations."""

    # Core state
    all_employees: list[dict] = []
    payroll_data: list[dict] = []
    salary_trend: list[dict] = []

    user_id: str = ""
    selected_user_name: str = ""
    month_selected: str = date.today().strftime("%Y-%m")

    # CRUD fields
    gross_salary: float = 0.0
    deductions: float = 0.0
    net_salary: float = 0.0

    # Metrics
    total_employees: int = 0
    total_salary: float = 0.0
    average_salary: float = 0.0
    pending_count: int = 0

    # ---------------- HELPERS ----------------
    @rx.var
    def formatted_month(self) -> str:
        # Ensure month_selected is always string
        if isinstance(self.month_selected, str):
            dt = datetime.strptime(self.month_selected, "%Y-%m")
            return dt.strftime("%B %Y")
        return ""

    # ---------------- ON MOUNT ----------------
    def on_mount(self):
        self.load_employees()
        self.load_payroll()

    # ---------------- LOAD EMPLOYEES ----------------
    def load_employees(self):
        if not self.tenant_id:
            return

        rows = conn.execute(
            "SELECT user_id, name FROM users WHERE tenant_id=? AND status='active' ORDER BY name",
            (self.tenant_id,),
        ).fetchall()

        self.all_employees = [{"id": r[0], "name": r[1]} for r in rows]

    # ---------------- SELECT EMPLOYEE ----------------
    def set_selected_employee(self, employee_id: str):
        self.user_id = employee_id
        match = next((e for e in self.all_employees if e["id"] == employee_id), None)
        self.selected_user_name = match["name"] if match else ""
        self.load_salary_trend()

    # ---------------- MONTH SELECT ----------------
    def set_month(self, month: str):
        self.month_selected = month
        self.load_payroll()

    # ---------------- LOAD PAYROLL ----------------
    def load_payroll(self):
        if not self.tenant_id:
            return

        rows = conn.execute(
            """
            SELECT u.name, p.month, p.gross_salary, p.deductions, p.net_salary
            FROM payroll p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.tenant_id = ? AND strftime('%Y-%m', p.month::DATE) = ?
            ORDER BY u.name
            """,
            (self.tenant_id, self.month_selected),
        ).fetchall()

        total_salary = 0
        data = []
        for name, month, gross, ded, net in rows:
            total_salary += net or 0
            data.append({
                "name": name,
                "month": datetime.strptime(month, "%Y-%m-%d").strftime("%Y-%m"),
                "gross": gross or 0,
                "deductions": ded or 0,
                "net": net or 0,
            })

        self.payroll_data = data
        self.total_employees = len(data)
        self.total_salary = round(total_salary, 2)
        self.average_salary = round(total_salary / len(data), 2) if data else 0.0

    # ---------------- CRUD OPERATIONS ----------------
    def set_gross_salary(self, value: str):
        try:
            self.gross_salary = float(value or 0)
        except ValueError:
            self.gross_salary = 0.0
        self.calculate_net_salary()

    def set_deductions(self, value: str):
        try:
            self.deductions = float(value or 0)
        except ValueError:
            self.deductions = 0.0
        self.calculate_net_salary()

    def calculate_net_salary(self):
        self.net_salary = round(self.gross_salary - self.deductions, 2)

    def save_payroll(self):
        print("updating payrole")
        if not self.user_id:
            return

        pid = str(uuid.uuid4())
        self.calculate_net_salary()

        conn.execute(
            """
            INSERT INTO payroll (payroll_id, tenant_id, user_id, month, gross_salary, deductions, net_salary, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NOW())
            ON CONFLICT (tenant_id, user_id, month)
            DO UPDATE SET gross_salary=excluded.gross_salary,
                        deductions=excluded.deductions,
                        net_salary=excluded.net_salary,
                        processed_at=NOW()
            """,
            (
                str(uuid.uuid4()),
                self.tenant_id,
                self.user_id,
                self.month_selected + "-01",
                self.gross_salary,
                self.deductions,
                self.net_salary,
            ),
        )
        conn.commit()
        self.load_payroll()
        self.load_salary_trend()

    def delete_payroll(self, user_name: str):
        conn.execute(
            """
            DELETE FROM payroll 
            WHERE tenant_id=? AND strftime('%Y-%m', month::DATE)=? 
            AND user_id IN (SELECT user_id FROM users WHERE name=?)
            """,
            (self.tenant_id, self.month_selected, user_name),
        )
        conn.commit()
        self.load_payroll()

    # ---------------- SALARY TREND ----------------
    def load_salary_trend(self):
        if not self.user_id:
            self.salary_trend = []
            return

        rows = conn.execute(
            """
            SELECT month, net_salary FROM payroll
            WHERE tenant_id=? AND user_id=?
            ORDER BY month
            """,
            (self.tenant_id, self.user_id),
        ).fetchall()

        self.salary_trend = [{"month": datetime.strptime(m, "%Y-%m-%d").strftime("%Y-%m"), "net": n or 0} for m, n in rows]


# ---------------- METRIC CARDS ----------------
def payroll_metric_cards(state: PayrollDashboardState):
    return rx.hstack(
        metric_card("users", state.total_employees, "Employees", "blue"),
        metric_card("wallet", state.total_salary, "Total Paid", "green"),
        metric_card("chart-bar", state.average_salary, "Avg Salary", "teal"),
        spacing="5",
        wrap="wrap",
    )


# ---------------- PAYROLL CRUD FORM ----------------
def payroll_crud_form(state: PayrollDashboardState):
    return rx.card(
        rx.vstack(
            rx.heading("Update Employee Payroll", size="5"),
            rx.select.root(
                rx.select.trigger(placeholder="Select Employee"),
                rx.select.content(
                    rx.foreach(
                        state.all_employees,
                        lambda emp: rx.select.item(emp["name"], value=emp["id"])
                    )
                ),
                on_change=state.set_selected_employee
            ),
            rx.input(
                type="month",
                value=state.month_selected,
                on_change=state.set_month,
                width="200px",
            ),
            rx.input(
                placeholder="Gross Salary",
                type="number",
                value=state.gross_salary,
                on_change=state.set_gross_salary,
            ),
            rx.input(
                placeholder="Deductions",
                type="number",
                value=state.deductions,
                on_change=state.set_deductions,
            ),
            rx.input(
                placeholder="Net Salary",
                type="number",
                value=state.net_salary,
                read_only=True,
            ),
            rx.button("Save Payroll", color_scheme="green", on_click=state.save_payroll),
            spacing="3",
        ),
        p="5",
        shadow="sm",
        width="300px",
    )


# ---------------- PAYROLL TABLE ----------------
def payroll_table(state: PayrollDashboardState):
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Name"),
                rx.table.column_header_cell("Month"),
                rx.table.column_header_cell("Gross Salary"),
                rx.table.column_header_cell("Deductions"),
                rx.table.column_header_cell("Net Salary"),
                rx.table.column_header_cell("Actions"),
            )
        ),
        rx.table.body(
            rx.foreach(
                state.payroll_data,
                lambda emp: rx.table.row(
                    rx.table.cell(emp["name"]),
                    rx.table.cell(emp["month"]),
                    rx.table.cell(emp["gross"]),
                    rx.table.cell(emp["deductions"]),
                    rx.table.cell(emp["net"]),
                    rx.table.cell(
                        rx.hstack(
                            rx.button(
                                "Delete",
                                color_scheme="red",
                                size="1",
                                on_click=lambda emp_name=emp["name"]: state.delete_payroll(emp_name),
                            ),
                            spacing="2",
                        )
                    ),
                ),
            )
        ),
        width="100%",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
    )


# ---------------- SALARY TREND GRAPH ----------------
def salary_trend_chart(state: PayrollDashboardState):
    return rx.cond(
        ~state.salary_trend,
        rx.text("Select an employee to view salary trend.", color="gray.500", mt="4"),
        rx.recharts.line_chart(
            rx.recharts.line(data_key="net", stroke="#3b82f6"),
            rx.recharts.x_axis(data_key="month"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            data=state.salary_trend,
            height=300,
            width="100%",
        ),
    )


# ---------------- MAIN PAGE ----------------
def payroll_dashboard_page() -> rx.Component:
    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            admin_dash_side_nav.Sidebar(),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            PayrollDashboardState.formatted_month,
                            size="7",
                        ),
                        rx.spacer(),
                        rx.input(
                            type="month",
                            value=PayrollDashboardState.month_selected,
                            on_change=PayrollDashboardState.set_month,
                            width="200px",
                        ),
                        spacing="4",
                    ),
                    payroll_metric_cards(PayrollDashboardState),
                    rx.hstack(
                        payroll_crud_form(PayrollDashboardState),
                        rx.box(payroll_table(PayrollDashboardState), flex="1"),
                        spacing="6",
                        align="start",
                    ),
                    rx.box(
                        rx.heading("Salary Trend", size="5"),
                        salary_trend_chart(PayrollDashboardState),
                        mt="6",
                    ),
                    spacing="6",
                    p="6",
                ),
                width="100%",
                height="100vh",
                overflow_y="auto",
            ),
            spacing="4",
        ),
        spacing="0",
        on_mount=PayrollDashboardState.on_mount,
    )
