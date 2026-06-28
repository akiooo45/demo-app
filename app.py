from fastapi import FastAPI
import os
import sqlite3
from pydantic import BaseModel
import redis
import json

app = FastAPI()
DB_PATH = os.getenv("DB_PATH", "/data/items.db")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_db():  # ← 新增：获取数据库连接，自动建表
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
    )
    conn.commit()
    return conn


@app.get("/")
def root():
    return {"message": "Hello from CI/CD pipeline", "env": os.getenv("ENV", "dev")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/foo")
def foo():
    return {"status": "ok"}


class ItemCreate(BaseModel):
    name: str


@app.get("/items")
def list_items():
    cached = r.get("items:list")
    if cached:
        return json.loads(cached)
    db = get_db()
    rows = db.execute("SELECT id, name FROM items ORDER BY id").fetchall()
    result = [{"id": row["id"], "name": row["name"]} for row in rows]
    r.setex("items:list", 30, json.dumps(result))
    return result


@app.post("/items", status_code=201)  # ← 新增
def create_item(item: ItemCreate):
    db = get_db()
    db.execute("INSERT INTO items (name) VALUES (?)", (item.name,))
    db.commit()
    r.delete("items:list")  # 追加在 return 前面
    return {"ok": True}


@app.delete("/items/{item_id}")  # ← 新增
def delete_item(item_id: int):
    from fastapi import HTTPException

    db = get_db()
    cur = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not found")
    r.delete("items:list")
    return {"ok": True}
