# -*- coding: utf-8 -*-
"""
One-time migration script: imports existing JSON data into the new SQLite database.

Usage:
    python migrate_json_to_sql.py

This is safe to re-run — it skips users whose email already exists and
predictions that are already stored.
"""
import json
import os
from database import init_db, get_connection

USERS_JSON = "data/users.json"
PREDICTIONS_CACHE_JSON = "data/predictions_cache.json"
SCORES_CACHE_JSON = "data/scores_cache.json"


def migrate_users():
    """Migrate users and their embedded prediction history."""
    if not os.path.exists(USERS_JSON):
        print("⚠️  users.json not found — skipping user migration.")
        return

    with open(USERS_JSON, "r") as f:
        data = json.load(f)

    users = data.get("users", [])
    if not users:
        print("⚠️  No users found in users.json.")
        return

    conn = get_connection()
    try:
        migrated_users = 0
        migrated_history = 0

        for user in users:
            # Check if email already exists
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", (user["email"],)
            ).fetchone()

            if existing:
                user_db_id = existing["id"]
                print(f"  ↳ User {user['email']} already exists (id={user_db_id}), skipping insert.")
            else:
                cur = conn.execute(
                    "INSERT INTO users (email, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (
                        user["email"],
                        user.get("username", user["email"].split("@")[0]),
                        user["password_hash"],
                        user.get("created_at", ""),
                    ),
                )
                user_db_id = cur.lastrowid
                migrated_users += 1
                print(f"  ✅ Migrated user: {user['email']} (id={user_db_id})")

            # Migrate prediction history
            history = user.get("history", [])
            for pred in history:
                match_id = pred.get("matchId", "")
                # Skip if already in DB
                exists = conn.execute(
                    "SELECT 1 FROM prediction_history WHERE user_id = ? AND match_id = ?",
                    (user_db_id, match_id),
                ).fetchone()
                if exists:
                    continue

                conn.execute(
                    "INSERT INTO prediction_history (user_id, match_id, data, created_at) VALUES (?, ?, ?, ?)",
                    (
                        user_db_id,
                        match_id,
                        json.dumps(pred, ensure_ascii=False),
                        pred.get("timestamp", ""),
                    ),
                )
                migrated_history += 1

        conn.commit()
        print(f"\n📊 Users: {migrated_users} new, {len(users)} total in JSON.")
        print(f"📊 Prediction history entries migrated: {migrated_history}")
    finally:
        conn.close()


def migrate_predictions_cache():
    """Migrate cached predictions."""
    if not os.path.exists(PREDICTIONS_CACHE_JSON):
        print("⚠️  predictions_cache.json not found — skipping.")
        return

    with open(PREDICTIONS_CACHE_JSON, "r") as f:
        data = json.load(f)

    predictions = data.get("predictions", {})
    if not predictions:
        print("⚠️  No cached predictions found.")
        return

    conn = get_connection()
    try:
        count = 0
        for cache_key, entry in predictions.items():
            conn.execute(
                "INSERT OR REPLACE INTO predictions_cache (cache_key, team_a, team_b, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                (
                    cache_key,
                    entry.get("teamA", ""),
                    entry.get("teamB", ""),
                    json.dumps(entry.get("result", {}), ensure_ascii=False),
                    entry.get("timestamp", ""),
                ),
            )
            count += 1
        conn.commit()
        print(f"📊 Predictions cache: {count} entries migrated.")
    finally:
        conn.close()


def migrate_scores_cache():
    """Migrate cached scores."""
    if not os.path.exists(SCORES_CACHE_JSON):
        print("⚠️  scores_cache.json not found — skipping.")
        return

    with open(SCORES_CACHE_JSON, "r") as f:
        data = json.load(f)

    scores = data.get("scores", [])
    last_update = data.get("lastUpdate")

    if not scores or not last_update:
        print("⚠️  No cached scores found.")
        return

    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO scores_cache (id, data, last_update) VALUES (1, ?, ?)",
            (json.dumps(scores, ensure_ascii=False), last_update),
        )
        conn.commit()
        print(f"📊 Scores cache: {len(scores)} scores migrated.")
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("  JSON → SQLite Migration")
    print("=" * 50)

    print("\n🔧 Initializing database...")
    init_db()

    print("\n👤 Migrating users...")
    migrate_users()

    print("\n🔮 Migrating predictions cache...")
    migrate_predictions_cache()

    print("\n🏀 Migrating scores cache...")
    migrate_scores_cache()

    print("\n" + "=" * 50)
    print("  Migration complete! ✅")
    print("=" * 50)
    print("\nThe SQLite database is at: data/nba.db")
    print("Your JSON files have NOT been deleted (kept as backup).")
