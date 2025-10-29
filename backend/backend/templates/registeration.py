import reflex as rx
import duckdb
import uuid
from datetime import datetime
from components.navbar import navbar

# Connect to database
conn = duckdb.connect(database='hrms.duckdb')

class RegisterState(rx.State):
    # Form fields
    company_name: str = ""
    name: str = ""
    email: str = ""
    role: str = "Employee"
    username: str = ""
    password: str = ""
    message: str = ""

    def register_user(self):
        try:
            # Validation
            if not all([self.company_name, self.name, self.email, self.username, self.password]):
                self.message = "⚠️ Please fill in all fields."
                return

            # Check if username exists
            existing_user = conn.execute(
                "SELECT username FROM logins WHERE username = ?", (self.username,)
            ).fetchone()
            if existing_user:
                self.message = "❌ Username already taken. Please choose another."
                return

            # Check if company (tenant) exists
            tenant = conn.execute(
                "SELECT tenant_id FROM tenants WHERE company_name = ?", (self.company_name,)
            ).fetchone()

            if tenant:
                tenant_id = tenant[0]
            else:
                tenant_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO tenants VALUES (?, ?, ?, ?, ?)",
                    [tenant_id, self.company_name, f"{self.company_name.lower().replace(' ', '')}.io", "basic", datetime.now()],
                )

            # Create user + login
            user_id = str(uuid.uuid4())
            login_id = str(uuid.uuid4())

            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    user_id,
                    tenant_id,
                    self.company_name,
                    self.name,
                    self.email,
                    self.role,
                    "active",
                    datetime.now(),
                ],
            )

            conn.execute(
                "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [login_id, tenant_id, user_id, self.username, self.password, None, 0, False, datetime.now()],
            )

            self.message = f"✅ Registration successful! Welcome to {self.company_name}, {self.name}."
        except Exception as e:
            self.message = f"❌ Error: {str(e)}"


def register_page() -> rx.Component:
    return rx.box(
        navbar(),
        rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Create Your Account", size="7", color="#1E3A8A"),
                rx.text("Join your company’s workspace or create a new one.", color="gray", margin_bottom="1em"),

                rx.input(placeholder="Company Name", value=RegisterState.company_name, on_change=RegisterState.set_company_name, margin_bottom="0.5em"),
                rx.input(placeholder="Full Name", value=RegisterState.name, on_change=RegisterState.set_name, margin_bottom="0.5em"),
                rx.input(placeholder="Email", value=RegisterState.email, on_change=RegisterState.set_email, margin_bottom="0.5em"),
                rx.input(placeholder="Username", value=RegisterState.username, on_change=RegisterState.set_username, margin_bottom="0.5em"),
                rx.input(placeholder="Password", type_="password", value=RegisterState.password, on_change=RegisterState.set_password, margin_bottom="0.5em"),

                rx.button(
                    "Register",
                    on_click=RegisterState.register_user,
                    color_scheme="blue",
                    width="100%",
                    border_radius="lg",
                    font_weight="bold",
                ),

                rx.text(RegisterState.message, color="gray", margin_top="1em"),
                align="center",
                width="100%",
            ),
            width="28em",
            padding="2em",
            border_radius="xl",
            box_shadow="md",
            bg="white",
        ),
        bg="#F3F4F6",
        min_height="100vh",
        padding_y="4em",
    ),
    )