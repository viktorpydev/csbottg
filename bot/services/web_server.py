import logging
from aiohttp import web

logger = logging.getLogger("bot.web")


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for hosting probes (e.g. Render, Koyeb, Docker)."""
    return web.json_response({
        "status": "ok",
        "service": "telegram-schedule-bot"
    })


async def index(request: web.Request) -> web.Response:
    """Root endpoint returning basic service status."""
    return web.Response(text="Telegram Schedule Bot is running.", content_type="text/plain")


def create_web_app() -> web.Application:
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/health", health_check)
    return app


async def start_web_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
    """Start the aiohttp web server on the specified host and port.
    
    Returns:
        web.AppRunner: The running AppRunner instance for clean shutdown handling.
    """
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Web server started and listening at http://{host}:{port}")
    return runner
