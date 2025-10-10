import reflex as rx
from components import dashboard_navbar, admin_dash_side_nav


class AdminDashboardState(admin_dash_side_nav.AdminState):
    def get_card_data():
        pass
    

def dashboard_page() -> rx.Component:
    # Example main content placeholder
    main_content = rx.box(
        rx.heading("Welcome to HRMS Admin Dashboard", size="5"),
        rx.text(AdminDashboardState.username),
        rx.text(AdminDashboardState.tenant_id),
        padding="6",
        width="100%",
    )

    return rx.vstack(
        # Top Navbar
        dashboard_navbar.navbar(),

        # Sidebar + Main Content
        rx.hstack(
            # Sidebar
            admin_dash_side_nav.Sidebar(),

            # Main content area
            main_content,
            width="100%",           # Take remaining width
            height="100vh",         # Full viewport height
            overflow_x="auto",      # Scroll if content is long
        ),
        spacing="0",
    )

