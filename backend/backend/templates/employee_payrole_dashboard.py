import reflex as rx
import duckdb
from datetime import date
from components import dashboard_navbar, employee_dash_side_nav

# ---------------- DATABASE CONNECTION ----------------
conn = duckdb.connect(database="hrms.duckdb")


# ---------------- METRIC CARD COMPONENT ----------------
def metric_card(icon_tag: str, value: str | float, label: str, color: str) -> rx.Component:
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


# ---------------- EMPLOYEE PAYROLL EmployeePayrollState ----------------
class EmployeePayrollState(employee_dash_side_nav.EmployeeState):
    """Employee payroll EmployeePayrollState for month-wise salary slips."""

    user_id: str = ""                       # Set from login
    month_selected: str = date.today().strftime("%Y-%m")  # "YYYY-MM"
    payroll_data: dict = {}
    available_months: list = []

    total_salary: float = 0.0
    gross_salary: float = 0.0
    deductions: float = 0.0
    net_salary: float = 0.0

    # ---------------- LOAD AVAILABLE MONTHS ----------------
    def load_available_months(self):
        rows = conn.execute(
            "SELECT DISTINCT month FROM payroll WHERE user_id=? ORDER BY month DESC",
            (self.user_id,),
        ).fetchall()
        self.available_months = [r[0] for r in rows]
        if self.available_months and not self.month_selected:
            self.month_selected = self.available_months[0]

    # ---------------- LOAD PAYROLL ----------------
    def set_month(self, month: str):
        self.month_selected = month
        self.load_payroll()

    def load_payroll(self):
        if not self.month_selected:
            return
        row = conn.execute(
            "SELECT gross_salary, deductions, net_salary, processed_at "
            "FROM payroll WHERE user_id=? AND month=?",
            (self.user_id, self.month_selected),
        ).fetchone()
        if row:
            self.payroll_data = {
                "gross_salary": row[0],
                "deductions": row[1],
                "net_salary": row[2],
                "processed_at": row[3],
            }
            self.total_salary = self.payroll_data["net_salary"]
            self.gross_salary = self.payroll_data["gross_salary"]
            self.deductions = self.payroll_data["deductions"]
            self.net_salary = self.payroll_data["net_salary"]
        else:
            self.payroll_data = {}
            self.total_salary = 0.0
            self.gross_salary = 0.0
            self.deductions = 0.0
            self.net_salary = 0.0

    # ---------------- ON MOUNT ----------------
    def on_load(self):
        self.load_available_months()


# ---------------- METRIC CARDS ----------------
def payroll_metric_cards():
    return rx.hstack(
        metric_card("wallet", EmployeePayrollState.total_salary, "Net Salary", "green"),
        metric_card("credit-card", EmployeePayrollState.gross_salary, "Gross Salary", "blue"),
        metric_card("minus-circle", EmployeePayrollState.deductions, "Deductions", "red"),
        spacing="5",
        wrap="wrap",
    )


# ---------------- PAYROLL INFO TABLE ----------------
def payroll_info_table():
    return rx.cond(
        EmployeePayrollState.payroll_data,  # Reflex Var
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Gross Salary"),
                    rx.table.column_header_cell("Deductions"),
                    rx.table.column_header_cell("Net Salary"),
                    rx.table.column_header_cell("Processed At"),
                )
            ),
            rx.table.body(
                rx.table.row(
                    rx.table.cell(EmployeePayrollState.payroll_data["gross_salary"]),
                    rx.table.cell(EmployeePayrollState.payroll_data["deductions"]),
                    rx.table.cell(EmployeePayrollState.payroll_data["net_salary"]),
                    rx.table.cell(EmployeePayrollState.payroll_data["processed_at"]),
                )
            ),
            width="100%",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
        ),
        rx.text("No payroll data for selected month.", color="gray.500")
    )



# ---------------- MAIN PAGE ----------------
def employee_payroll_dashboard() -> rx.Component:
    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            employee_dash_side_nav.Sidebar(),
            rx.box(
                rx.vstack(
                    rx.heading("Employee Payroll Dashboard", size="5", mb="4"),

                    # Month selection
                    rx.hstack(
                        rx.text("Select Month:"),
                        rx.select(
                            items=EmployeePayrollState.available_months,
                            value=EmployeePayrollState.month_selected,
                            on_change=EmployeePayrollState.set_month,
                            placeholder="Select Month",
                            width="200px",
                        ),
                        rx.button("Load Payroll", on_click=EmployeePayrollState.load_payroll),
                        mb=4,
                        spacing="3",
                    ),

                    # Metric Cards
                    payroll_metric_cards(),

                    # Payroll info table
                    payroll_info_table(),

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
        on_mount=EmployeePayrollState.on_load,  # 👈 Load months when page mounts
    )