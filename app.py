from fastapi import FastAPI
import os
import sqlite3
from pydantic import BaseModel

app = FastAPI()
DB_PATH = os.getenv("DB_PATH", "/data/items.db")


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


@app.get("/items")  # ← 新增
def list_items():
    db = get_db()
    rows = db.execute("SELECT id, name FROM items ORDER BY id").fetchall()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


@app.post("/items", status_code=201)  # ← 新增
def create_item(item: ItemCreate):
    db = get_db()
    db.execute("INSERT INTO items (name) VALUES (?)", (item.name,))
    db.commit()
    return {"ok": True}


@app.delete("/items/{item_id}")  # ← 新增
def delete_item(item_id: int):
    from fastapi import HTTPException

    db = get_db()
    cur = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}
