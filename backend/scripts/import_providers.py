"""
Import provider definitions from a local JSON file into cursor-assistant.db.

Usage:
    python backend/scripts/import_providers.py backend/providers.local.json
"""
import json
import sqlite3
import sys
from pathlib import Path


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            api_key TEXT NOT NULL,
            base_url TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL,
            model_id TEXT NOT NULL,
            name TEXT NOT NULL,
            max_tokens INTEGER DEFAULT 4096,
            supports_streaming BOOLEAN DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            parameters JSON DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(provider_id) REFERENCES providers(id)
        )
        """
    )


def import_provider(conn: sqlite3.Connection, provider: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM providers WHERE name = ? AND type = ?",
        (provider["name"], provider["type"]),
    )
    row = cur.fetchone()
    if row:
        provider_id = row[0]
        cur.execute(
            """
            UPDATE providers
            SET api_key = ?, base_url = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (provider["api_key"], provider["base_url"], provider_id),
        )
        cur.execute("DELETE FROM models WHERE provider_id = ?", (provider_id,))
    else:
        cur.execute(
            """
            INSERT INTO providers (name, type, api_key, base_url, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (provider["name"], provider["type"], provider["api_key"], provider["base_url"]),
        )
        provider_id = cur.lastrowid

    for model in provider.get("models", []):
        cur.execute(
            """
            INSERT INTO models (provider_id, model_id, name, max_tokens, supports_streaming, is_active, parameters)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (
                provider_id,
                model["model_id"],
                model.get("name", model["model_id"]),
                model.get("max_tokens", 4096),
                1 if model.get("supports_streaming", True) else 0,
                json.dumps(model.get("parameters", {}), ensure_ascii=True),
            ),
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python backend/scripts/import_providers.py <providers.local.json>")
        return 1

    source = Path(sys.argv[1]).resolve()
    if not source.exists():
        print(f"Input file not found: {source}")
        return 1

    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "backend" / "cursor-assistant.db"

    payload = json.loads(source.read_text(encoding="utf-8"))
    providers = payload.get("providers", [])
    if not isinstance(providers, list) or not providers:
        print("No providers found in input file")
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        ensure_schema(conn)
        for provider in providers:
            import_provider(conn, provider)
        conn.commit()
    finally:
        conn.close()

    print(f"Imported {len(providers)} provider(s) into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
