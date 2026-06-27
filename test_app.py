from fastapi.testclient import TestClient
from app import app
import sqlite3  # ← 新增

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Hello" in r.json()["message"]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ===== Phase 3a 新增测试 =====


def test_items_crud():  # ← 新增
    # 用内存数据库跑测试，不影响 /data/items.db
    import app as app_module

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
    )
    conn.commit()

    original_get_db = app_module.get_db
    app_module.get_db = lambda: conn

    try:
        # 空列表
        r = client.get("/items")
        assert r.status_code == 200
        assert r.json() == []

        # 创建
        r = client.post("/items", json={"name": "learn k8s"})
        assert r.status_code == 201

        # 列表多了一条
        r = client.get("/items")
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "learn k8s"
        item_id = r.json()[0]["id"]

        # 删除
        r = client.delete(f"/items/{item_id}")
        assert r.status_code == 200

        # 列表又空了
        r = client.get("/items")
        assert r.json() == []

        # 删不存在的 → 404
        r = client.delete("/items/99999")
        assert r.status_code == 404
    finally:
        app_module.get_db = original_get_db  # 恢复，不污染其他测试
