"""Local smoke tests: python -m unittest test_a2a.py"""
import asyncio
import os
import unittest
import uuid
import httpx
from app import app

class A2AContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["A2A_BEARER_TOKEN"] = "synthetic-test-secret-12345"
        os.environ["PUBLIC_BASE_URL"] = "https://northstar.example.test"
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_health_and_card(self):
        health = await self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        card = (await self.client.get("/.well-known/agent-card.json")).json()
        self.assertEqual(card["protocolVersion"], "0.3.0")
        self.assertEqual(card["url"], "https://northstar.example.test/a2a")
        self.assertEqual(card["securitySchemes"]["bearerAuth"]["scheme"], "bearer")

    async def test_unauthorized(self):
        self.assertEqual((await self.client.post("/a2a", json={})).status_code, 401)

    async def test_send_and_get(self):
        data = {"jsonrpc":"2.0","id":"t1","method":"message/send", "params":{"message": {"kind":"message","messageId": str(uuid.uuid4()), "role":"user", "parts":[{"kind":"text","text":"Prepare onboarding checklist for two Java developers joining Project Orion."}]}}}
        headers = {"Authorization": "Bearer synthetic-test-secret-12345"}
        result = (await self.client.post("/a2a", json=data, headers=headers)).json()
        task = result["result"]
        self.assertEqual(task["status"]["state"], "completed")
        text = task["artifacts"][0]["parts"][0]["text"]
        for term in ["Hiring authorization","Right-to-work", "Security training", "Access governance", "Device provisioning", "Manager sign-off", "No offer, hire"]:
            self.assertIn(term, text)
        get_result = (await self.client.post("/a2a", json={"jsonrpc":"2.0","id":"t2","method":"tasks/get","params":{"id":task["id"]}},headers=headers)).json()
        self.assertEqual(get_result["result"]["id"], task["id"])

if __name__ == "__main__": unittest.main()
