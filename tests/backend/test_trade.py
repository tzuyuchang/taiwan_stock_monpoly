import asyncio

import httpx

from backend.app import app


def test_trade_endpoint():
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/trade")

    response = asyncio.run(_request())

    assert response.status_code == 200
    assert isinstance(response.json(), list)
