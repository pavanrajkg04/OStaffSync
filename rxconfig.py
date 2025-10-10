import reflex as rx

config = rx.Config(
    app_name="OStaffSync",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)