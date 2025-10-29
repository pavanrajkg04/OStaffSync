import reflex as rx

config = rx.Config(
    app_name="OStaffSync",
     api_url="https://ostaffsync-backend.onrender.com",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
) 