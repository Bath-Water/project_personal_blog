"""Quick integration smoke test."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from httpx import AsyncClient, ASGITransport

from app.database import init_db, close_engine
from app.main import app


BASE = "http://test"


async def main():
    await init_db()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url=BASE) as c:
            r = await c.get("/api/health")
            assert r.status_code == 200, r.text
            print("health:", r.json())

            r = await c.post("/api/auth/register", json={
                "username": "alice", "email": "a@b.com", "password": "Pass1234",
            })
            print("register:", r.status_code, r.json())
            assert r.status_code == 201

            r = await c.post("/api/auth/login", json={
                "email_or_username": "alice", "password": "Pass1234",
            })
            body = r.json()
            assert body["code"] == 0
            token = body["data"]["access_token"]
            print("login ok, token prefix:", token[:20])
            auth = {"Authorization": f"Bearer {token}"}

            r = await c.post("/api/categories", json={"name": "Tech", "sort_order": 1}, headers=auth)
            print("create category:", r.status_code, r.json())
            cat_id = r.json()["data"]["id"]

            r = await c.post("/api/tags", json={"name": "python"}, headers=auth)
            print("create tag:", r.status_code, r.json())
            tag_id = r.json()["data"]["id"]

            r = await c.post("/api/posts", json={
                "title": "Hello 你好 World",
                "content": "<p>测试中文内容 python 编程</p>",
                "excerpt": "a test post",
                "category_id": cat_id,
                "tag_ids": [tag_id],
                "status": "draft",
            }, headers=auth)
            print("create post:", r.status_code)
            post_id = r.json()["data"]["id"]

            r = await c.get("/api/posts")
            print("list posts:", r.status_code, "total:", r.json()["data"]["total"])

            r = await c.get(f"/api/posts/{post_id}")
            print("get post:", r.status_code, r.json()["data"]["title"])

            r = await c.get("/api/search", params={"q": "你好"})
            print("search 你好:", r.status_code, "total:", r.json()["data"]["total"])

            r = await c.post(f"/api/posts/{post_id}/publish", headers=auth)
            print("publish:", r.status_code)

            r = await c.post(f"/api/posts/{post_id}/preview")
            print("preview ok:", r.status_code, "len:", len(r.json()["data"]["html"]))

            r = await c.get("/api/posts/archives")
            print("archives:", r.status_code, r.json())

            r = await c.get("/api/settings")
            print("settings:", r.status_code, r.json()["data"]["blog_name"])
            r = await c.put("/api/settings", json={"blog_name": "Alex Blog"}, headers=auth)
            print("update settings:", r.status_code)

            r = await c.post(f"/api/posts/{post_id}/comments", json={
                "nickname": "Bob", "content": "Great post!",
            })
            print("create comment:", r.status_code, r.json())
            r = await c.get(f"/api/posts/{post_id}/comments")
            print("list comments:", r.status_code, "count:", len(r.json()["data"]))

            r = await c.post("/api/auth/refresh", json={
                "refresh_token": body["data"]["refresh_token"],
            })
            print("refresh:", r.status_code, r.json()["data"]["access_token"][:20])

            r = await c.post("/api/auth/register", json={
                "username": "weak", "email": "w@b.com", "password": "short",
            })
            print("weak pw:", r.status_code, r.json()["code"])

            r = await c.post("/api/auth/register", json={
                "username": "alice", "email": "x@b.com", "password": "Pass1234",
            })
            print("dup user:", r.status_code, r.json()["code"])

            r2 = await c.post("/api/tags", json={"name": "AI"}, headers=auth)
            new_tag = r2.json()["data"]["id"]
            r = await c.patch(f"/api/posts/{post_id}/tags", json={
                "tag_ids": [new_tag]
            }, headers=auth)
            print("set tags:", r.status_code, r.json())

            r = await c.delete(f"/api/posts/{post_id}", headers=auth)
            print("delete post:", r.status_code, r.json())

            print("\nALL OK ✅")
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())