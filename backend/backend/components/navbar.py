import reflex as rx

def navbar():
    return rx.hstack(
        # Left: Logo / Company Name
        rx.text(
            "OStaffSync",
            color="#1E3A8A",  # Deep blue
            font_size="2",
            font_weight="bold",
            padding_x="2",
            _hover={"color": "#2563EB", "transition": "color 0.3s ease"},
        ),

        # Right: Navigation Links
        rx.hstack(
            rx.link("Home", href="/", color="black", font_size="1.1", padding_x="2", _hover={
                "color": "#2563EB",
                "transform": "scale(1.05)",
                "transition": "all 0.3s ease-in-out",
            }),
            rx.link("About", href="/about", color="black", font_size="1.1", padding_x="2", _hover={
                "color": "#2563EB",
                "transform": "scale(1.05)",
                "transition": "all 0.3s ease-in-out",
            }),
            rx.link("Login", href="/login", color="black", font_size="1.1", padding_x="2", _hover={
                "color": "#2563EB",
                "transform": "scale(1.05)",
                "transition": "all 0.3s ease-in-out",
            }),
            rx.link("Register", href="/register", color="black", font_size="1.1", padding_x="2", _hover={
                "color": "#2563EB",
                "transform": "scale(1.05)",
                "transition": "all 0.3s ease-in-out",
            }),
            spacing="5",
            align="center",
            margin="20",
        ),

        # Navbar container styling
        width="100%",
        justify="between",
        align="center",
        padding_y="1.5",
        padding_x="6",  # ✅ horizontal padding to create margin from edges
        background_color="#FFF44F",  # Lemon yellow
        box_shadow="0 2px 8px rgba(0, 0, 0, 0.15)",
        position="sticky",
        top="0",
        z_index="1000",
    )
