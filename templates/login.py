import reflex as rx
import duckdb
import uuid
from datetime import datetime
from components.navbar import navbar

# Connect to database
conn = duckdb.connect(database="hrms.duckdb")


class LoginState(rx.State):
    """Handles login and session state."""

    company_name: str = ""
    username: str = ""
    password: str = ""
    message: str = ""

    tenant_id: str = ""
    user_id: str = ""
    session_id: str = ""
    full_name: str = ""

    # Setters
    def set_company_name(self, value: str):
        self.company_name = value

    def set_username(self, value: str):
        self.username = value

    def set_password(self, value: str):
        self.password = value

    def set_message(self, value: str):
        self.message = value

    def logout_user(self):
        """Clear session and redirect to login."""
        self.company_name = ""
        self.username = ""
        self.password = ""
        self.user_id = ""
        self.tenant_id = ""
        self.session_id = ""
        self.full_name = ""
        return rx.redirect("/login")

    def login_user(self):
        """Validate login credentials and set session."""
        try:
            if not all([self.company_name, self.username, self.password]):
                self.message = "⚠️ Please fill all fields."
                return

            # Check company exists
            tenant = conn.execute(
                "SELECT tenant_id FROM tenants WHERE company_name = ?", (self.company_name,)
            ).fetchone()

            if not tenant:
                self.message = "❌ Company not found. Please check the name."
                return

            self.tenant_id = tenant[0]

            # Validate credentials
            user = conn.execute(
                """
                SELECT u.user_id, u.name
                FROM logins l
                JOIN users u ON l.user_id = u.user_id
                WHERE l.username = ? AND l.password = ? AND l.tenant_id = ?
                """,
                (self.username, self.password, self.tenant_id),
            ).fetchone()

            if not user:
                self.message = "❌ Invalid username or password."
                return

            # Set session info
            self.user_id = user[0]
            self.full_name = user[1]
            self.session_id = str(uuid.uuid4())

            # Update last login
            conn.execute(
                "UPDATE logins SET last_login = ? WHERE username = ?",
                (datetime.now(), self.username),
            )

            self.message = f"✅ Welcome back, {self.full_name}!"
            return rx.redirect("/dashboard")

        except Exception as e:
            self.message = f"❌ Error: {str(e)}"


def login_page() -> rx.Component:
    """Login page UI."""
    return rx.box(
        navbar(),
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("Welcome Back!", font_size="2xl", color="#1E3A8A"),
                    rx.text(
                        "Sign in to your company workspace.",
                        color="gray",
                        margin_bottom="1em",
                    ),
                    rx.input(
                        placeholder="Company Name",
                        value=LoginState.company_name,
                        on_change=LoginState.set_company_name,
                        margin_bottom="0.5em",
                    ),
                    rx.input(
                        placeholder="Username",
                        value=LoginState.username,
                        on_change=LoginState.set_username,
                        margin_bottom="0.5em",
                    ),
                    rx.input(
                        placeholder="Password",
                        type_="password",
                        value=LoginState.password,
                        on_change=LoginState.set_password,
                        margin_bottom="0.5em",
                    ),
                    rx.button(
                        "Login",
                        on_click=LoginState.login_user,
                        color_scheme="blue",
                        width="100%",
                        border_radius="lg",
                        font_weight="bold",
                    ),
                    rx.text(LoginState.message, margin_top="1em", color="gray"),
                    rx.hstack(
                        rx.text("Don't have an account?", color="gray"),
                        rx.link(
                            "Register here",
                            href="/register",
                            color="blue.600",
                            font_weight="medium",
                        ),
                        align="center",
                        margin_top="1em",
                    ),
                    align="center",
                    width="100%",
                ),
                width="26em",
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
