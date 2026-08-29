import pytest
from aiohttp.test_utils import TestClient, TestServer
from bot.services.web_server import create_web_app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    app = create_web_app()
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "telegram-schedule-bot"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_index_endpoint():
    app = create_web_app()
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "Telegram Schedule Bot is running." in text
    finally:
        await client.close()
