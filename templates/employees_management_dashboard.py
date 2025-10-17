import reflex as rx
import duckdb
import uuid
from datetime import datetime
from components import dashboard_navbar, admin_dash_side_nav

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
conn = duckdb.connect(database="hrms.duckdb")


# ---------------------------------------------------
# STATE CLASS
# ---------------------------------------------------
class EmployeeCRUDState(admin_dash_side_nav.AdminState):
    """State for managing employee CRUD operations."""

    employees: list[dict] = []
    name: str = ""
    email: str = ""
    role: str = ""
    status: str = "active"
    password: str = ""
    selected_user_id: str = ""

    # ---------------------------------------------------
    # LOAD EMPLOYEES
    # ---------------------------------------------------
    def load_employees(self, atenant_id=None):
        """Load all employees for the current tenant."""
        if atenant_id is None:
            atenant_id = str(self.tenant_id)
        if not atenant_id or atenant_id == "None":
            print("⏳ tenant_id not ready; skipping employee load.")
            return

        results = conn.execute(
            """
            SELECT user_id, name, email, role, status, date_joined
            FROM users
            WHERE tenant_id = ?
            ORDER BY date_joined DESC
            """,
            (atenant_id,),
        ).fetchall()

        self.employees = [
            {
                "user_id": r[0],
                "name": r[1],
                "email": r[2],
                "role": r[3],
                "status": r[4],
                "date_joined": r[5].strftime("%Y-%m-%d"),
            }
            for r in results
        ]
        print(f"✅ Loaded {len(self.employees)} employees for tenant {atenant_id}")

    # ---------------------------------------------------
    # CREATE EMPLOYEE
    # ---------------------------------------------------
    def create_employee(self, atenant_id=None):
        """Create a new employee and corresponding login."""
        if atenant_id is None:
            atenant_id = str(self.tenant_id)

        if not (self.name and self.email and self.password):
            print("⚠️ Missing fields for employee creation.")
            return

        # Check duplicate email
        exists = conn.execute(
            "SELECT 1 FROM users WHERE email = ? AND tenant_id = ?", (self.email, atenant_id)
        ).fetchone()
        if exists:
            print("⚠️ Employee with this email already exists.")
            return

        user_id = str(uuid.uuid4())
        tenant_name = conn.execute(
            "SELECT company_name FROM tenants WHERE tenant_id = ?", (atenant_id,)
        ).fetchone()
        company_name = tenant_name[0] if tenant_name else "Unknown"

        # Hash the password
        hashed_pw = self.password

        # Insert into users
        conn.execute(
            """
            INSERT INTO users (user_id, tenant_id, company_name, name, email, role, status, date_joined)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                atenant_id,
                company_name,
                self.name.strip(),
                self.email.strip(),
                self.role.strip(),
                self.status,
                datetime.now(),
            ),
        )

        # Insert into logins
        conn.execute(
            """
            INSERT INTO logins (login_id, user_id, tenant_id, username, password, account_locked, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                atenant_id,
                self.name.strip(),
                hashed_pw,
                False,
                datetime.now(),
            ),
        )

        conn.commit()
        print(f"✅ Created employee and login for {self.name}")

        # Reset form and reload employees
        self.name = self.email = self.role = self.password = ""
        self.load_employees(atenant_id)

    # ---------------------------------------------------
    # EDIT EMPLOYEE
    # ---------------------------------------------------
    def edit_employee(self, user_id: str):
        """Load existing employee into form."""
        result = conn.execute(
            "SELECT name, email, role, status FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if result:
            self.selected_user_id = user_id
            self.name, self.email, self.role, self.status = result
            print(f"✏️ Editing employee: {self.name}")

    # ---------------------------------------------------
    # UPDATE EMPLOYEE
    # ---------------------------------------------------
    def update_employee(self):
        """Update user and login data."""
        if not self.selected_user_id:
            print("⚠️ No employee selected for update.")
            return

        # Update users
        conn.execute(
            """
            UPDATE users
            SET name = ?, email = ?, role = ?, status = ?
            WHERE user_id = ?
            """,
            (self.name.strip(), self.email.strip(), self.role.strip(), self.status, self.selected_user_id),
        )

        # Update logins
        if self.password.strip():
            hashed_pw = hashlib.sha256(self.password.strip().encode()).hexdigest()
            conn.execute(
                """
                UPDATE logins
                SET email = ?, password_hash = ?
                WHERE user_id = ?
                """,
                (self.email.strip(), hashed_pw, self.selected_user_id),
            )
        else:
            conn.execute(
                """
                UPDATE logins
                SET email = ?
                WHERE user_id = ?
                """,
                (self.email.strip(), self.selected_user_id),
            )

        conn.commit()
        print(f"📝 Updated employee and login: {self.name}")

        # Reset
        self.selected_user_id = ""
        self.name = self.email = self.role = self.password = ""
        self.load_employees(str(self.tenant_id))

    # ---------------------------------------------------
    # DELETE EMPLOYEE
    # ---------------------------------------------------
    def delete_employee(self, user_id: str):
        """Delete from both users and logins."""
        conn.execute("DELETE FROM logins WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        print(f"🗑️ Deleted employee and login: {user_id}")
        self.load_employees(str(self.tenant_id))


# ---------------------------------------------------
# PAGE UI
# ---------------------------------------------------
def employee_crud_page() -> rx.Component:
    """Employee management dashboard page."""
    return rx.vstack(
        dashboard_navbar.navbar(),
        rx.hstack(
            admin_dash_side_nav.Sidebar(),
            rx.box(
                rx.vstack(
                    rx.heading("Employee Management Dashboard", size="7", mb="6", color="gray.700"),

                    # -------------------------------
                    # EMPLOYEE FORM
                    # -------------------------------
                    rx.form(
                        rx.vstack(
                            rx.input(
                                placeholder="Full Name",
                                value=EmployeeCRUDState.name,
                                on_change=EmployeeCRUDState.set_name,
                            ),
                            rx.input(
                                placeholder="Email Address",
                                value=EmployeeCRUDState.email,
                                on_change=EmployeeCRUDState.set_email,
                            ),
                            rx.input(
                                placeholder="Role (e.g., Manager, Engineer)",
                                value=EmployeeCRUDState.role,
                                on_change=EmployeeCRUDState.set_role,
                            ),
                            # Password field (only visible for new employees)
                            rx.cond(
                                EmployeeCRUDState.selected_user_id == "",
                                rx.input(
                                    type="password",
                                    placeholder="Password",
                                    value=EmployeeCRUDState.password,
                                    on_change=EmployeeCRUDState.set_password,
                                ),
                            ),
                            rx.select(
                                ["active", "inactive", "terminated"],
                                value=EmployeeCRUDState.status,
                                on_change=EmployeeCRUDState.set_status,
                            ),
                            rx.hstack(
                                rx.button(
                                    rx.cond(
                                        EmployeeCRUDState.selected_user_id == "",
                                        "Create Employee",
                                        "Update Employee",
                                    ),
                                    color_scheme="green",
                                    on_click=rx.cond(
                                        EmployeeCRUDState.selected_user_id == "",
                                        EmployeeCRUDState.create_employee,
                                        EmployeeCRUDState.update_employee,
                                    ),
                                ),
                                rx.button(
                                    "Clear Form",
                                    color_scheme="gray",
                                    on_click=lambda: [
                                        EmployeeCRUDState.set_name(""),
                                        EmployeeCRUDState.set_email(""),
                                        EmployeeCRUDState.set_role(""),
                                        EmployeeCRUDState.set_password(""),
                                        EmployeeCRUDState.set_selected_user_id(""),
                                    ],
                                ),
                                spacing="3",
                            ),
                            spacing="3",
                        ),
                        reset_on_submit=False,
                        width="100%",
                        max_width="500px",
                        mb="8",
                    ),

                    # -------------------------------
                    # EMPLOYEE TABLE
                    # -------------------------------
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Name"),
                                rx.table.column_header_cell("Email"),
                                rx.table.column_header_cell("Role"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Date Joined"),
                                rx.table.column_header_cell("Actions"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                EmployeeCRUDState.employees,
                                lambda emp: rx.table.row(
                                    rx.table.cell(emp["name"]),
                                    rx.table.cell(emp["email"]),
                                    rx.table.cell(emp["role"]),
                                    rx.table.cell(emp["status"]),
                                    rx.table.cell(emp["date_joined"]),
                                    rx.table.cell(
                                        rx.hstack(
                                            rx.button(
                                                "Edit",
                                                size="1",
                                                color_scheme="blue",
                                                variant="outline",
                                                on_click=lambda _: EmployeeCRUDState.edit_employee(emp["user_id"]),
                                            ),
                                            rx.button(
                                                "Delete",
                                                size="1",
                                                color_scheme="red",
                                                variant="solid",
                                                on_click=lambda _: EmployeeCRUDState.delete_employee(emp["user_id"]),
                                            ),
                                            spacing="2",
                                        )
                                    ),
                                ),
                            )
                        ),
                    ),
                ),
                on_mount=EmployeeCRUDState.load_employees,  # Load employees on mount
                p="8",
                width="100%",
                height="100vh",
                overflow_y="auto",
                bg="white",
                border_radius="12",
                shadow="sm",
            ),
            align="start",
            width="100%",
        ),
        spacing="0",
    )
