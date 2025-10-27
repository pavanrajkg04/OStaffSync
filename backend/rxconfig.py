import reflex as rx

config = rx.Config(
    app_name="OStaffSync",
     api_url="https://4c75dac5382d.ngrok-free.app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)