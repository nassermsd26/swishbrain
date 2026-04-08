# -*- coding: utf-8 -*-
"""
SQLite database module for NBA AI Predictor.
Replaces the previous JSON file-based storage.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "data/nba.db"


def get_connection():
    """Returns a new SQLite connection with row_factory set."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                email             TEXT UNIQUE NOT NULL,
                username          TEXT NOT NULL,
                password_hash     TEXT NOT NULL,
                role              TEXT NOT NULL DEFAULT 'user',
                approved          INTEGER NOT NULL DEFAULT 0,
                subscription_tier TEXT NOT NULL DEFAULT 'free',
                tokens            INTEGER NOT NULL DEFAULT 10,
                referral_code     TEXT UNIQUE,
                diamonds          INTEGER NOT NULL DEFAULT 0,
                referral_credited INTEGER NOT NULL DEFAULT 0,
                created_at        TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prediction_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                match_id    TEXT NOT NULL,
                data        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_prediction_history_user
                ON prediction_history(user_id);

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                sender      TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_user
                ON messages(user_id);

            CREATE TABLE IF NOT EXISTS predictions_cache (
                cache_key   TEXT PRIMARY KEY,
                team_a      TEXT NOT NULL,
                team_b      TEXT NOT NULL,
                result      TEXT NOT NULL,
                timestamp   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scores_cache (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                data        TEXT NOT NULL,
                last_update TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                username     TEXT NOT NULL,
                email        TEXT NOT NULL,
                diamonds     INTEGER NOT NULL,
                amount       INTEGER NOT NULL,
                crypto_addr  TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_withdrawal_user
                ON withdrawal_requests(user_id);
        """)
        conn.commit()

        # Migrate: add role column if missing (for existing databases)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add approved column if missing (for existing databases)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN approved INTEGER NOT NULL DEFAULT 1")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add subscription_tier column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT NOT NULL DEFAULT 'free'")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add tokens column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN tokens INTEGER NOT NULL DEFAULT 10")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add referral_code column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_ref ON users(referral_code)")
            conn.commit()
        except sqlite3.OperationalError as e:
            # column might already exist, but index might not
            try:
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_ref ON users(referral_code)")
                conn.commit()
            except:
                pass
            
        # Migrate: add diamonds column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN diamonds INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Migrate: add referred_by column if missing (stores the ID of the referrer)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add referral_credited column if missing (prevents double-crediting on re-approval)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN referral_credited INTEGER NOT NULL DEFAULT 0")
            # For existing users that are already approved and have a referrer, mark as credited
            conn.execute("""
                UPDATE users SET referral_credited = 1
                WHERE approved = 1 AND referred_by IS NOT NULL
            """)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: create withdrawal_requests table if missing (for existing DBs)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      INTEGER NOT NULL,
                    username     TEXT NOT NULL,
                    email        TEXT NOT NULL,
                    diamonds     INTEGER NOT NULL,
                    amount       INTEGER NOT NULL,
                    crypto_addr  TEXT NOT NULL,
                    status       TEXT NOT NULL DEFAULT 'pending',
                    created_at   TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_withdrawal_user ON withdrawal_requests(user_id);
            """)
            conn.commit()
        except:
            pass
            
        # Ensure all existing users have a referral code
        rows = conn.execute("SELECT id FROM users WHERE referral_code IS NULL").fetchall()
        import string, secrets
        for row in rows:
            while True:
                code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
                try:
                    conn.execute("UPDATE users SET referral_code = ? WHERE id = ?", (code, row['id']))
                    conn.commit()
                    break
                except sqlite3.IntegrityError:
                    pass

    finally:
        conn.close()


# ─────────────────── Withdrawal requests ────────────────────

def create_withdrawal_request(user_id, username, email, diamonds, amount, crypto_addr):
    """Create a new withdrawal request. Returns the created dict."""
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO withdrawal_requests (user_id, username, email, diamonds, amount, crypto_addr, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)",
            (int(user_id), username, email, int(diamonds), int(amount), crypto_addr, now)
        )
        conn.commit()
        return {
            "id": cur.lastrowid,
            "user_id": int(user_id),
            "username": username,
            "email": email,
            "diamonds": int(diamonds),
            "amount": int(amount),
            "crypto_addr": crypto_addr,
            "status": "pending",
            "created_at": now,
        }
    finally:
        conn.close()


def get_all_withdrawal_requests():
    """Return all withdrawal requests ordered by most recent first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM withdrawal_requests ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_withdrawal_status(request_id, status):
    """Update the status of a withdrawal request ('pending', 'approved', 'rejected').
       If approved, deduct the corresponding diamonds from the user."""
    conn = get_connection()
    try:
        # Fetch request details to know the amount and user
        req = conn.execute("SELECT * FROM withdrawal_requests WHERE id = ?", (int(request_id),)).fetchone()
        if not req:
            return False
            
        cur = conn.execute(
            "UPDATE withdrawal_requests SET status = ? WHERE id = ?",
            (status, int(request_id))
        )
        
        # If we are approving a pending request, deduct diamonds
        if status == 'approved' and req['status'] == 'pending':
            diamonds_to_deduct = 5 if req['amount'] >= 50 else 3
            user_id = req['user_id']
            conn.execute(
                "UPDATE users SET diamonds = MAX(0, diamonds - ?) WHERE id = ?",
                (diamonds_to_deduct, user_id)
            )
            
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ───────────────────────── User helpers ─────────────────────────

def find_user_by_email(email):
    """Find a user by email. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def find_user_by_id(user_id):
    """Find a user by ID. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (int(user_id),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_users():
    """Return a list of all users as dicts."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM users").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_user(email, password_hash, username=None, subscription_tier='free', referral_code_input=None):
    """Insert a new user. Returns the user dict or None if email exists."""
    if find_user_by_email(email):
        return None

    now = datetime.now().isoformat()
    # Setup initial tokens according to subscription tier
    initial_tokens = 70 if subscription_tier == 'vip' else 10
    
    import string, secrets
    
    conn = get_connection()
    try:
        # Generate unique referral code
        while True:
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
            if not conn.execute("SELECT 1 FROM users WHERE referral_code = ?", (code,)).fetchone():
                break

        # Resolve referrer — store their ID but do NOT credit the diamond yet.
        # The diamond is only awarded when the admin approves this new account.
        referrer_id = None
        if referral_code_input:
            referrer = conn.execute(
                "SELECT id FROM users WHERE referral_code = ? AND approved = 1",
                (referral_code_input,)
            ).fetchone()
            if referrer:
                referrer_id = referrer['id']

        cur = conn.execute(
            "INSERT INTO users (email, username, password_hash, role, approved, subscription_tier, tokens, referral_code, diamonds, referred_by, referral_credited, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (email, username or email.split("@")[0], password_hash, 'user', 0, subscription_tier, initial_tokens, code, 0, referrer_id, 0, now)
        )
        conn.commit()
        return {
            "id": cur.lastrowid,
            "email": email,
            "username": username or email.split("@")[0],
            "password_hash": password_hash,
            "role": "user",
            "approved": 0,
            "subscription_tier": subscription_tier,
            "tokens": initial_tokens,
            "referral_code": code,
            "diamonds": 0,
            "referred_by": referrer_id,
            "created_at": now,
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def update_user_profile(user_id, email, username):
    """Update a user's email and username."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET email = ?, username = ? WHERE id = ?",
            (email, username, int(user_id))
        )
        conn.commit()
    finally:
        conn.close()


def update_user_password(user_id, password_hash):
    """Update a user's password hash."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, int(user_id))
        )
        conn.commit()
    finally:
        conn.close()


def set_user_role(user_id, role):
    """Set a user's role ('user' or 'admin')."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, int(user_id))
        )
        conn.commit()
    finally:
        conn.close()


def approve_user(user_id):
    """Approve a user's account and credit the referrer's diamond if applicable."""
    conn = get_connection()
    try:
        # Fetch the user to check referred_by and referral_credited BEFORE approving
        user_row = conn.execute(
            "SELECT approved, referred_by, referral_credited FROM users WHERE id = ?",
            (int(user_id),)
        ).fetchone()
        if not user_row:
            return False

        cur = conn.execute(
            "UPDATE users SET approved = 1 WHERE id = ?",
            (int(user_id),)
        )
        conn.commit()

        # Credit +1 diamond to the referrer ONLY if it has never been credited before
        # (referral_credited = 0 means never credited, regardless of suspend/re-approve cycles)
        referrer_id = user_row['referred_by']
        already_credited = user_row['referral_credited'] == 1
        if referrer_id and not already_credited:
            conn.execute(
                "UPDATE users SET diamonds = diamonds + 1 WHERE id = ?",
                (referrer_id,)
            )
            # Mark as credited so future re-approvals never double-credit
            conn.execute(
                "UPDATE users SET referral_credited = 1 WHERE id = ?",
                (int(user_id),)
            )
            conn.commit()
            print(f"💎 +1 diamond crédité au parrain (id={referrer_id}) pour approbation de l'utilisateur {user_id}")

        return cur.rowcount > 0
    finally:
        conn.close()


def suspend_user(user_id):
    """Suspend a user (set approved = 0)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE users SET approved = 0 WHERE id = ?",
            (int(user_id),)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_user_subscription(user_id, tier):
    """Update a user's subscription tier ('free', 'basic', 'premium', 'vip')."""
    conn = get_connection()
    try:
        if tier == 'vip':
            cur = conn.execute(
                "UPDATE users SET subscription_tier = ?, tokens = 70 WHERE id = ?",
                (tier, int(user_id))
            )
        else:
            cur = conn.execute(
                "UPDATE users SET subscription_tier = ? WHERE id = ?",
                (tier, int(user_id))
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def decrement_user_tokens(user_id):
    """Decrement a user's tokens by 1. Returns True if successful and tokens were > 0."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE users SET tokens = tokens - 1 WHERE id = ? AND tokens > 0",
            (int(user_id),)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_user_tokens(user_id):
    """Get the current number of tokens for a user."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT tokens FROM users WHERE id = ?", (int(user_id),)).fetchone()
        return row["tokens"] if row else 0
    finally:
        conn.close()


def add_user_tokens(user_id, amount):
    """Add tokens to a user. Returns True if successful."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE users SET tokens = tokens + ? WHERE id = ?",
            (int(amount), int(user_id))
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_all_users_with_history():
    """Return all users with their prediction history count and latest predictions."""
    conn = get_connection()
    try:
        users = []
        rows = conn.execute(
            "SELECT id, email, username, role, approved, subscription_tier, tokens, referral_code, diamonds, referred_by, referral_credited, created_at FROM users ORDER BY id"
        ).fetchall()
        for row in rows:
            user = dict(row)
            # Get prediction count
            count = conn.execute(
                "SELECT COUNT(*) FROM prediction_history WHERE user_id = ?",
                (user["id"],)
            ).fetchone()[0]
            user["prediction_count"] = count
            # Get last 50 predictions
            preds = conn.execute(
                "SELECT data FROM prediction_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
                (user["id"],)
            ).fetchall()
            user["history"] = [json.loads(p["data"]) for p in preds]
            users.append(user)
        return users
    finally:
        conn.close()


def delete_user(user_id):
    """Delete a user and their prediction history. Returns True if deleted."""
    conn = get_connection()
    try:
        # prediction_history has ON DELETE CASCADE, so it will be cleaned up
        cur = conn.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ─────────────────────── Messages history ────────────────────────

def get_user_messages(user_id):
    """Get all messages for a user, ordered by creation time."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, user_id, sender, content, created_at FROM messages WHERE user_id = ? ORDER BY created_at ASC",
            (int(user_id),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_message(user_id, sender, content):
    """Add a new message to the database. sender should be 'user' or 'admin'."""
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO messages (user_id, sender, content, created_at) VALUES (?, ?, ?, ?)",
            (int(user_id), sender, content, now)
        )
        conn.commit()
        return {
            "id": cur.lastrowid,
            "user_id": int(user_id),
            "sender": sender,
            "content": content,
            "created_at": now
        }
    finally:
        conn.close()


# ───────────────────── Prediction history ───────────────────────

def save_prediction_to_history(user_id, prediction_data):
    """Save a prediction to a user's history (max 50 kept)."""
    try:
        user = find_user_by_id(user_id)
        if not user:
            print(f"❌ Utilisateur avec ID {user_id} non trouvé!")
            return

        match_id = prediction_data.get("matchId", "")
        now = datetime.now().isoformat()
        data_json = json.dumps(prediction_data, ensure_ascii=False)

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO prediction_history (user_id, match_id, data, created_at) VALUES (?, ?, ?, ?)",
                (int(user_id), match_id, data_json, now)
            )

            # Keep only the 50 most recent predictions
            conn.execute("""
                DELETE FROM prediction_history
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM prediction_history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 50
                )
            """, (int(user_id), int(user_id)))

            conn.commit()
            count = conn.execute(
                "SELECT COUNT(*) FROM prediction_history WHERE user_id = ?",
                (int(user_id),)
            ).fetchone()[0]
            print(f"💾 Prédiction sauvegardée. Total: {count} prédictions pour user {user_id}")
        finally:
            conn.close()
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de l'historique: {e}")
        import traceback
        traceback.print_exc()


def get_user_history(user_id):
    """Get a user's prediction history (most recent first)."""
    try:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT data FROM prediction_history WHERE user_id = ? ORDER BY created_at DESC",
                (int(user_id),)
            ).fetchall()
            return [json.loads(r["data"]) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {e}")
        return []


def delete_prediction_from_history(user_id, match_id):
    """Delete a specific prediction from a user's history. Returns True if deleted."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM prediction_history WHERE user_id = ? AND match_id = ?",
            (int(user_id), match_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ───────────────────── Predictions cache ────────────────────────

def get_cache_key(teamA: str, teamB: str) -> str:
    """Generate a cache key for a match (sorted so A-B == B-A)."""
    teams = sorted([teamA, teamB])
    return f"{teams[0]}-{teams[1]}"


def get_cached_prediction(teamA: str, teamB: str):
    """Return a cached prediction if it exists and is less than 24h old."""
    try:
        cache_key = get_cache_key(teamA, teamB)
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT result, timestamp FROM predictions_cache WHERE cache_key = ?",
                (cache_key,)
            ).fetchone()

            if row:
                cached_time = datetime.fromisoformat(row["timestamp"])
                age = datetime.now() - cached_time

                if age.total_seconds() < 24 * 3600:
                    print(f"✅ Prédiction trouvée en cache pour {cache_key} (âge: {age.total_seconds()/3600:.1f}h)")
                    return json.loads(row["result"])
                else:
                    print(f"⚠️ Prédiction en cache expirée pour {cache_key} (âge: {age.total_seconds()/3600:.1f}h)")
                    conn.execute("DELETE FROM predictions_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()

            return None
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur lors de la récupération du cache: {e}")
        return None


def save_prediction_to_cache(teamA: str, teamB: str, result: dict):
    """Save or update a prediction in the cache (max 100 entries)."""
    try:
        cache_key = get_cache_key(teamA, teamB)
        now = datetime.now().isoformat()
        result_json = json.dumps(result, ensure_ascii=False)

        conn = get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO predictions_cache (cache_key, team_a, team_b, result, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, teamA, teamB, result_json, now))

            # Keep only 100 most recent predictions
            conn.execute("""
                DELETE FROM predictions_cache
                WHERE cache_key NOT IN (
                    SELECT cache_key FROM predictions_cache
                    ORDER BY timestamp DESC
                    LIMIT 100
                )
            """)

            conn.commit()
            print(f"💾 Prédiction sauvegardée en cache pour {cache_key}")
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du cache: {e}")


# ────────────────────── Scores cache ────────────────────────────

def get_cached_scores():
    """Return cached scores if they are less than 1 hour old."""
    try:
        conn = get_connection()
        try:
            row = conn.execute("SELECT data, last_update FROM scores_cache WHERE id = 1").fetchone()

            if row:
                last_update = datetime.fromisoformat(row["last_update"])
                age = datetime.now() - last_update

                if age.total_seconds() < 3600:
                    print(f"✅ Scores trouvés en cache (âge: {age.total_seconds()/60:.1f}min)")
                    return json.loads(row["data"])

            return None
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur récupération cache scores: {e}")
        return None


def save_scores_to_cache(scores):
    """Save scores to the cache (single row, upserted)."""
    try:
        now = datetime.now().isoformat()
        data_json = json.dumps(scores, ensure_ascii=False)

        conn = get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO scores_cache (id, data, last_update)
                VALUES (1, ?, ?)
            """, (data_json, now))
            conn.commit()
            print(f"💾 {len(scores)} scores sauvegardés en cache")
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur sauvegarde cache scores: {e}")
