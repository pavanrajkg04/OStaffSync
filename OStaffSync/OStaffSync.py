"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config
from templates import admin_attendance_dashboard, admin_payroll_dashboard, employee_dashboard, employee_leave_dashboard, employee_payrole_dashboard, home, login, registeration, admin_dashboard, admin_employees_management_dashboard



class State(rx.State):
    """The app state."""


def index() -> rx.Component:
    # Welcome Page (Index)
    return home.landing_page()


app = rx.App()
app.add_page(index, route="/")
app.add_page(login.login_page, route="/login")
app.add_page(registeration.register_page, route="/register")
app.add_page(admin_dashboard.dashboard_page, route="/dashboard")
app.add_page(admin_employees_management_dashboard.employee_crud_page, route="/employees")
app.add_page(admin_attendance_dashboard.attendance_dashboard_page,route="/attendance")
app.add_page(admin_payroll_dashboard.payroll_dashboard_page,route='/payroll')
app.add_page(employee_dashboard.employee_dashboard_page, route='/empdashboard')
app.add_page(employee_leave_dashboard.employee_leaves_page, route='/empleaves')
app.add_page(employee_payrole_dashboard.employee_payroll_dashboard, route='/emppayrole')
# app.add_page(registration_page, route="/register")
# app.add_page(dashboard_page, route="/dashboard")