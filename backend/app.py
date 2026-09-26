from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "guestbook.db"


app = FastAPI(
    title="Undangan Pernikahan - Guestbook API",
    version="1.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:610",
        "http://localhost:610",
        "https://undangan-pernikahan-mr-afifah.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


class MessageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., min_length=1, max_length=50)
    message: str = Field(..., min_length=1, max_length=1000)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS guest_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Hadir',
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    columns = connection.execute(
        "PRAGMA table_info(guest_messages)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "status" not in column_names:
        connection.execute(
            """
            ALTER TABLE guest_messages
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Hadir'
            """
        )

    connection.commit()
    connection.close()


@app.on_event("startup")
def startup():
    init_database()


@app.get("/")
def root():
    return {
        "message": "Guestbook API berjalan",
        "status": "ok",
    }


@app.get("/api/messages")
def get_messages():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT id, name, status, message, created_at
        FROM guest_messages
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return {
        "messages": [dict(row) for row in rows]
    }


@app.delete("/api/messages/{message_id}")
def delete_message(message_id: int):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id
        FROM guest_messages
        WHERE id = ?
        """,
        (message_id,),
    ).fetchone()

    if row is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Ucapan tidak ditemukan.",
        )

    connection.execute(
        """
        DELETE FROM guest_messages
        WHERE id = ?
        """,
        (message_id,),
    )

    connection.commit()
    connection.close()

    return {
        "message": "Ucapan berhasil dihapus.",
        "id": message_id,
    }

@app.post("/api/messages")
def create_message(data: MessageCreate):
    name = data.name.strip()
    status = data.status.strip()
    message = data.message.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Nama tidak boleh kosong.",
        )

    if not status:
        raise HTTPException(
            status_code=400,
            detail="Status kehadiran tidak boleh kosong.",
        )

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Ucapan tidak boleh kosong.",
        )

    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO guest_messages
            (name, status, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, status, message, created_at),
    )

    connection.commit()

    message_id = cursor.lastrowid

    row = connection.execute(
        """
        SELECT id, name, status, message, created_at
        FROM guest_messages
        WHERE id = ?
        """,
        (message_id,),
    ).fetchone()

    connection.close()

    return {
        "message": "Ucapan berhasil disimpan.",
        "data": dict(row),
    }


