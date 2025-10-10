"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config
from templates import home, login, registeration, admin_dashboard



class State(rx.State):
    """The app state."""


def index() -> rx.Component:
    # Welcome Page (Index)
    return home.landing_page()


app = rx.App()
app.add_page(index)
app.add_page(index, route="/")
app.add_page(login.login_page, route="/login")
app.add_page(registeration.register_page, route="/register")
app.add_page(admin_dashboard.dashboard_page, route="/dashboard")
# app.add_page(registration_page, route="/register")
# app.add_page(dashboard_page, route="/dashboard")