import reflex as rx

config = rx.Config(
    app_name="OStaffSync",
     api_url="https://319eebe35928.ngrok-free.app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
