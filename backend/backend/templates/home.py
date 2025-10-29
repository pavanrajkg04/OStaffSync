import reflex as rx
from reflex_motion import motion
from components.navbar import navbar

class State(rx.State):
    pass



# Animated Metric
def circular_metric(label: str, value: int, color: str) -> rx.Component:
    # value: percentage (0-100)
    return motion(
        rx.vstack(
            rx.box(
                rx.text(f"{value}%", font_size="2xl", font_weight="extrabold", color=color, text_align="center"),
                width="24",
                height="24",
                border_radius="full",
                display="flex",
                align_items="center",
                justify_content="center",
                background=f"conic-gradient({color} {value*3.6}deg, rgba(255,255,255,0.2) 0deg)",
            ),
            rx.text(label, font_size="3", color="gray.100", text_align="center"),
            align="center",
            spacing="2",
        ),
        initial={"opacity": 0, "y": 30},
        animate={"opacity": 1, "y": 0},
        transition={"duration": 0.8, "ease": "easeOut"},
    )

def horizontal_metric(label: str, value: int, color: str) -> rx.Component:
    return motion(
        rx.vstack(
            rx.text(label, font_size="3", color="gray.200", text_align="center"),
            rx.box(
                rx.box(
                    "", width=f"{value}%", height="6px", background_color=color, border_radius="full"
                ),
                width="full",
                background_color="whiteAlpha.300",
                border_radius="full",
                height="6px",
                margin_top="1",
            ),
            rx.text(f"{value}%", font_size="sm", color="white", font_weight="bold", text_align="center"),
            spacing="2",
        ),
        initial={"opacity": 0, "y": 20},
        animate={"opacity": 1, "y": 0},
        transition={"duration": 0.8, "ease": "easeOut"},
    )

def count_up_metric(label: str, value: int, color: str) -> rx.Component:
    return motion(
        rx.vstack(
            rx.text(value, font_size="3xl", font_weight="extrabold", color=color, id=f"{label}-counter"),
            rx.text(label, font_size="3", color="gray.100"),
            align="center",
        ),
        initial={"opacity": 0, "y": 80},
        animate={"opacity": 1, "y": 0},
        transition={"duration": 1, "ease": "easeOut"},
    )

# Hero Section with Metrics / Graphs
def hero_section() -> rx.Component:
    metrics = [
        {"label": "HR Time Saved", "value": 50, "color": "#9f7aea"},       # purple
        {"label": "Employees Managed", "value": 80, "color": "#48bb78"},   # green
        {"label": "Startups Using OStaffSync", "value": 70, "color": "#4299e1"}, # blue
    ]

    metric_components = [count_up_metric(m["label"], m["value"], m["color"]) for m in metrics]

    return rx.box(
        rx.vstack(
            # Headline
            motion(
                rx.heading(
                    "Transform Your HR. Open Source. Fully Flexible.",
                    font_size="6xl",
                    color="white",
                    font_weight="extrabold",
                    text_align="center",
                ),
                initial={"opacity": 0, "y": -50},
                animate={"opacity": 1, "y": 0},
                transition={"duration": 1, "ease": "easeOut"},
            ),
            # Subheadline
            motion(
                rx.text(
                    "Empower your team with a modern HR management system that handles payroll, attendance, performance, and more—without limits.",
                    font_size="2xl",
                    color="gray.100",
                    text_align="center",
                    max_width="3xl",
                    line_height="taller",
                ),
                initial={"opacity": 0, "y": 30},
                animate={"opacity": 1, "y": 0},
                transition={"duration": 1, "delay": 0.3, "ease": "easeOut"},
            ),
            # Key Highlights
            motion(
                rx.vstack(
                    rx.hstack(rx.text("✅", font_size="xl"), rx.text("Completely Free & Open Source: Take full control of your HR processes.", font_size="4", color="gray.100"), spacing="3"),
                    rx.hstack(rx.text("✅", font_size="xl"), rx.text("All-in-One HR Solution: Simplify recruitment, payroll, performance, and employee management.", font_size="4", color="gray.100"), spacing="3"),
                    rx.hstack(rx.text("✅", font_size="xl"), rx.text("Designed for Teams: Flexible, scalable, and easy to use for any organization size.", font_size="4", color="gray.100"), spacing="3"),
                    spacing="4",
                    align="start",
                    max_width="3xl",
                ),
                initial={"opacity": 0, "y": 20},
                animate={"opacity": 1, "y": 0},
                transition={"duration": 1, "delay": 0.5, "ease": "easeOut"},
            ),
            # Circular Metrics / Graphs
            rx.hstack(*metric_components, spacing="8", justify="center", wrap="wrap", margin_top="8"),
            
            # CTA Buttons
            rx.hstack(
                motion(
                    rx.button(
                        "Get Started Today",
                        size="4",
                        variant="solid",
                        background_color="white",
                        color="blue.600",
                        font_weight="bold",
                        width="48",
                        height="16",
                    ),
                    initial={"opacity": 0, "scale": 0.9},
                    animate={"opacity": 1, "scale": 1},
                    transition={"duration": 0.8, "delay": 0.7, "ease": "easeOut"},
                    whileHover={"bg": "blue.400", "transform": "translateY(-2px)"},
                ),
                motion(
                    rx.button(
                        "Learn More",
                        size="4",
                        variant="outline",
                        border_color="white",
                        color="white",
                        font_weight="bold",
                        width="48",
                        height="16",
                    ),
                    initial={"opacity": 0, "scale": 0.9},
                    animate={"opacity": 1, "scale": 1},
                    transition={"duration": 0.8, "delay": 0.9, "ease": "easeOut"},
                    whileHover={"bg": "whiteAlpha.200", "transform": "translateY(-2px)"},
                ),
                spacing="8",
                justify="center",
                margin_top="6",
            ),
            # Supporting Line
            motion(
                rx.text(
                    "Your HR, your way. Streamline workflows, empower employees, and save time.",
                    font_size="4",
                    color="gray.200",
                    text_align="center",
                    max_width="3xl",
                ),
                initial={"opacity": 0, "y": 20},
                animate={"opacity": 1, "y": 0},
                transition={"duration": 1, "delay": 1.1, "ease": "easeOut"},
            ),
            spacing="8",
            align="center",
        ),
        width="100vw",
        height="100vh",
        background="linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
        align="center",
        justify="center",
        padding_x="4",
    )


# Animated Feature Card
def feature_card(title: str, description: str, icon: str, color: str, delay: float = 0) -> rx.Component:
    return motion(
        rx.vstack(
            rx.box(icon, font_size="3xl", background_color=color, border_radius="full", padding="4", color="white"),
            rx.heading(title, font_size="xl", font_weight="bold", color="gray.800", text_align="center"),
            rx.text(description, font_size="3", color="gray.600", text_align="center"),
            spacing="4",
            align="center",
            padding="6",
            background_color="white",
            border_radius="xl",
            box_shadow="xl",
            width="full",
            _hover={"transform": "translateY(-6px)", "boxShadow": "2xl"},
        ),
        initial={"opacity": 0, "y": 50},
        animate={"opacity": 1, "y": 0},
        transition={"duration": 0.6, "delay": delay, "ease": "easeOut"},
    )

# Hero Section
# Marketing-Friendly Hero Section
def hero_section_with_metrics() -> rx.Component:
    metrics = [
        {"label": "HR Time Saved", "value": 50, "color": "purple.400"},       # percentage
        {"label": "Employees Managed", "value": 10000, "color": "green.400"}, # can scale visually
        {"label": "Startups Using OStaffSync", "value": 500, "color": "blue.400"},
    ]

    metric_cards = []
    for i, m in enumerate(metrics):
        # Bar graph representation
        metric_cards.append(
            motion(
                rx.vstack(
                    rx.text(m["label"], font_size="3", color="gray.200", text_align="center"),
                    rx.box(
                        rx.box(
                            "",  # the filled portion
                            width=f"{min(m['value']/100, 100)}%",  # scale for demo; adjust based on metric
                            height="4",
                            background_color=m["color"],
                            border_radius="full",
                        ),
                        width="full",
                        background_color="whiteAlpha.300",
                        border_radius="full",
                        height="4",
                        margin_top="1",
                    ),
                    rx.text(f"{m['value']}{'%' if i==0 else ''}", font_size="4", color="white", font_weight="bold", text_align="center", margin_top="1"),
                    spacing="2",
                    align="center",
                    padding="4",
                    background_color="whiteAlpha.100",
                    border_radius="3",
                    width="48",
                ),
                initial={"opacity": 0, "y": 30},
                animate={"opacity": 1, "y": 0},
                transition={"duration": 0.8, "delay": i*0.3, "ease": "easeOut"},
            )
        )

    return rx.box(
        rx.vstack(
            # Headline & tagline
            rx.vstack(
                rx.heading(
                    "Transform Your HR. Open Source. Fully Flexible.",
                    font_size="6xl",
                    color="white",
                    font_weight="extrabold",
                    text_align="center",
                ),
                rx.text(
                    "Empower your team with a modern HR system that handles payroll, attendance, performance, and more—without limits.",
                    font_size="2xl",
                    color="gray.100",
                    text_align="center",
                    max_width="3xl",
                    line_height="taller",
                ),
                spacing="4",
                align="center",
            ),
            # Key Highlights
            rx.vstack(
                rx.hstack(rx.text("✅", font_size="xl"), rx.text("Completely Free & Open Source", font_size="4", color="gray.100"), spacing="3"),
                rx.hstack(rx.text("✅", font_size="xl"), rx.text("All-in-One HR Solution", font_size="4", color="gray.100"), spacing="3"),
                rx.hstack(rx.text("✅", font_size="xl"), rx.text("Designed for Teams", font_size="4", color="gray.100"), spacing="3"),
                spacing="4",
                align="start",
                max_width="3xl",
            ),
            # Graph / Metric Bars
            rx.hstack(*metric_cards, spacing="6", justify="center", wrap="wrap", margin_top="8"),
            # CTA Buttons
            rx.hstack(
                rx.button("Get Started Today", size="4", variant="solid", background_color="white", color="blue.600", font_weight="bold", width="48", height="16"),
                rx.button("Learn More", size="4", variant="outline", border_color="white", color="white", font_weight="bold", width="48", height="16"),
                spacing="8",
                justify="center",
                margin_top="6",
            ),
            spacing="8",
            align="center",
        ),
        width="100vw",
        height="100vh",
        background="linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
        align="center",
        justify="center",
        padding_x="4",
    )




# Features Section
def features_section() -> rx.Component:
    features = [
        {"title": "Employee Management", "description": "Centralize all employee records and HR tasks.", "icon": "👤", "color": "blue.400"},
        {"title": "Payroll & Attendance", "description": "Automate payroll and track attendance easily.", "icon": "💰", "color": "green.400"},
        {"title": "Performance Tracking", "description": "Monitor KPIs, goals, and appraisals effectively.", "icon": "📊", "color": "purple.400"},
        {"title": "Recruitment & Onboarding", "description": "Manage candidates and onboarding in one platform.", "icon": "🔍", "color": "orange.400"},
    ]

    cards = [feature_card(f["title"], f["description"], f["icon"], f["color"], i*0.2) for i, f in enumerate(features)]

    return rx.box(
        rx.vstack(
            rx.heading("Key Features", font_size="3xl", font_weight="extrabold", color="blue.600", text_align="center"),
            rx.grid(*cards, columns="2", spacing="8", width="full"),
            spacing="9",
            align="center",
        ),
        width="100vw",
        padding_y="20",
        background_color="gray.50",
        align="center",
    )

# Testimonials Section
# Polished Testimonials Section
def testimonial_section() -> rx.Component:
    testimonials = [
        {"name": "Ravi K", "company": "StartupX", "quote": "OStaffSync reduced our HR workload by 50%!", "avatar": "👨‍💼"},
        {"name": "Anika S", "company": "TechNova", "quote": "The payroll module is a lifesaver.", "avatar": "👩‍💼"},
        {"name": "Rahul P", "company": "Innovatech", "quote": "Simplified our employee management completely.", "avatar": "👨‍💻"},
    ]

    cards = [
        motion(
            rx.vstack(
                rx.text("“", font_size="6xl", color="blue.600", text_align="center", line_height="0.5"),
                rx.text(t["quote"], font_size="2xl", color="gray.800", font_weight="semibold", text_align="center", line_height="tall"),
                rx.text(f'- {t["name"]}, {t["company"]}', font_size="3", color="gray.500", text_align="center"),
                rx.box(t["avatar"], font_size="4xl", padding="2", background_color="blue.100", border_radius="full", margin_top="4"),
                spacing="4",
                align="center",
                padding="8",
                background_color="white",
                border_radius="xl",
                box_shadow="2xl",
                width="sm",
            ),
            initial={"opacity": 0, "y": 40},
            animate={"opacity": 1, "y": 0},
            transition={"duration": 0.6, "delay": i * 0.2, "ease": "easeOut"},
        )
        for i, t in enumerate(testimonials)
    ]

    return rx.box(
        rx.vstack(
            rx.heading("What Startups Say", font_size="3xl", font_weight="extrabold", color="blue.600", text_align="center"),
            rx.hstack(
                *cards,
                spacing="9",
                justify="center",
                wrap="wrap",
            ),
            spacing="9",
            align="center",
        ),
        width="100vw",
        padding_y="24",
        background_color="gray.50",
        align="center",
    )


# Footer
def footer_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("© 2025 OStaffSync. All rights reserved.", color="gray.500", font_size="sm"),
            rx.hstack(
                rx.text("GitHub", color="blue.600", font_weight="bold", _hover={"textDecoration": "underline"}),
                rx.text("Docs", color="blue.600", font_weight="bold", _hover={"textDecoration": "underline"}),
                spacing="6",
            ),
            spacing="4",
            align="center",
        ),
        width="100vw",
        padding_y="6",
        background_color="gray.900",
        align="center",
    )

# Complete Landing Page Layout
def layout() -> rx.Component:
    return rx.vstack(
        navbar(),
        hero_section(),
        features_section(),
        testimonial_section(),
        footer_section(),
        width="100%",
        spacing="0",
    )

def landing_page() -> rx.Component:
    return layout()
