import reflex as rx
from templates.login import LoginState


class EmployeeState(LoginState):
    username = LoginState.username
    user_id = LoginState.user_id
    company_name = LoginState.company_name
    tenant_id = LoginState.tenant_id
    dashboard_filter: str = ""


def sidebar_item(text: str, icon: str, href: str):
    """Sidebar link item."""
    return rx.link(
        rx.hstack(
            rx.icon(icon),
            rx.text(text, size="4"),
            width="100%",
            padding_x="0.5rem",
            padding_y="0.75rem",
            align="center",
            style={
                "_hover": {
                    "bg": rx.color("accent", 4),
                    "color": rx.color("accent", 11),
                    "cursor": "pointer",
                }
            },
        ),
        href=href,
    )


def sidebar_bottom_profile():
    """Sidebar bottom user profile with proper conditional rendering."""
    return rx.box(
        rx.hstack(
            rx.avatar(
                fallback="👤",
                size="3",
            ),
            rx.vstack(
                # ✅ Reflex-safe conditional
                rx.cond(
                    EmployeeState.full_name != "",
                    rx.text(EmployeeState.full_name, size="3", weight="bold"),
                    rx.text("Employee", size="3", weight="bold"),
                ),
                rx.text(EmployeeState.username, size="2", color="gray"),
                spacing="0",
                align="start",
            ),
            align="center",
            justify="between",
            width="100%",
        ),
        rx.button(
            "Logout",
            on_click=EmployeeState.logout_user,
            color_scheme="red",
            size="2",
            margin_top="0.75rem",
        ),
        padding="1rem",
        border_top=f"1px solid {rx.color('gray', 5)}",
    )


def Sidebar():
    """Full sidebar layout for Employee."""
    return rx.box(
        rx.vstack(
            # Sidebar header
            rx.hstack(
                rx.icon("user", size=22),
                rx.text("OStaffSync", size="5", weight="bold"),
                rx.text("Employee", size="3", color="gray"),
                spacing="3",
                align="center",
                padding="1rem",
            ),
            rx.divider(),

            # Sidebar navigation
            sidebar_item("Dashboard", "layout-dashboard", "/empdashboard"),
            #sidebar_item("My Profile", "user", "/empprofile"),
            #sidebar_item("Attendance", "clock", "/employee/attendance"),
            sidebar_item("Leaves", "calendar", "/empleaves"),
            sidebar_item("Payroll", "wallet", "/emppayrole"),
            #sidebar_item("Settings", "settings", "/employee/settings"),

            rx.spacer(),
            sidebar_bottom_profile(),
            spacing="2",
            height="100vh",
            justify="between",
            background_color=rx.color("accent", 2),
            width="18rem",
            border_right=f"1px solid {rx.color('gray', 6)}",
        )
    )