import reflex as rx

config = rx.Config(
    app_name="OStaffSync",
     api_url="https://32088bfe8d8c.ngrok-free.app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)