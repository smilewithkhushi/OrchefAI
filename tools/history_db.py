import json
import sqlite3
import os
from models.event_state import EventState
from models.restaurant import RestaurantProfile

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orchefai.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_events (
                event_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                event_type TEXT,
                guest_count INTEGER,
                venue TEXT,
                budget_usd REAL,
                total_cost_usd REAL,
                suggested_price_usd REAL,
                margin_percentage REAL,
                budget_feasible INTEGER,
                risk_level TEXT,
                created_at TEXT,
                completed_at TEXT DEFAULT (datetime('now')),
                full_state TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kitchen_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL DEFAULT 'kg',
                cost_per_unit REAL NOT NULL DEFAULT 0.0,
                region TEXT NOT NULL DEFAULT 'singapore',
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)


def save_restaurant_profile(profile: RestaurantProfile):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO restaurant_profile (id, data, updated_at) VALUES (1, ?, datetime('now')) "
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
            (profile.model_dump_json(),),
        )


def get_restaurant_profile() -> RestaurantProfile | None:
    with _conn() as conn:
        row = conn.execute("SELECT data FROM restaurant_profile WHERE id=1").fetchone()
    if row:
        return RestaurantProfile(**json.loads(row["data"]))
    return None


def save_completed_event(state: EventState):
    with _conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO completed_events
               (event_id, status, event_type, guest_count, venue, budget_usd,
                total_cost_usd, suggested_price_usd, margin_percentage,
                budget_feasible, risk_level, created_at, full_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                state.event_id,
                state.status,
                state.customer.event_type,
                state.customer.guest_count,
                state.customer.venue,
                state.customer.budget_usd,
                state.pricing.cost_breakdown.total_cost_usd,
                state.pricing.suggested_price_usd,
                state.pricing.margin_percentage,
                int(state.pricing.budget_feasible),
                state.monitoring.overall_risk_level,
                state.created_at,
                state.model_dump_json(),
            ),
        )


def get_event_history(limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT event_id, status, event_type, guest_count, venue, budget_usd, "
            "total_cost_usd, suggested_price_usd, margin_percentage, budget_feasible, "
            "risk_level, created_at, completed_at "
            "FROM completed_events ORDER BY completed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_event_detail(event_id: str) -> EventState | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT full_state FROM completed_events WHERE event_id=?", (event_id,)
        ).fetchone()
    if row:
        return EventState(**json.loads(row["full_state"]))
    return None


def get_history_summary() -> dict:
    """Quick stats for agent context: total events, avg margin, conversion rate."""
    with _conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='complete' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status='needs_review' THEN 1 ELSE 0 END) as needs_review,
                AVG(margin_percentage) as avg_margin,
                AVG(suggested_price_usd) as avg_price,
                AVG(guest_count) as avg_guests
            FROM completed_events
        """).fetchone()
    if not row or row["total"] == 0:
        return {}
    return dict(row)


def save_kitchen_item(ingredient: str, quantity: float, unit: str, cost_per_unit: float, region: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO kitchen_stock (ingredient, quantity, unit, cost_per_unit, region, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (ingredient, quantity, unit, cost_per_unit, region),
        )


def get_kitchen_stock(region: str | None = None) -> list[dict]:
    with _conn() as conn:
        if region:
            rows = conn.execute(
                "SELECT * FROM kitchen_stock WHERE region=? ORDER BY ingredient", (region,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM kitchen_stock ORDER BY ingredient").fetchall()
    return [dict(r) for r in rows]


def delete_kitchen_item(item_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM kitchen_stock WHERE id=?", (item_id,))


def seed_kitchen_stock():
    with _conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM kitchen_stock").fetchone()[0]
        if count > 0:
            return
        defaults = [
            ("jasmine_rice", 120.0, "kg", 2.50, "singapore"),
            ("chicken", 80.0, "kg", 8.00, "singapore"),
            ("onion", 60.0, "kg", 2.00, "singapore"),
            ("garlic", 15.0, "kg", 5.00, "singapore"),
            ("coconut_milk", 40.0, "kg", 3.50, "singapore"),
            ("chili", 10.0, "kg", 7.00, "singapore"),
            ("soy_sauce", 20.0, "kg", 4.00, "singapore"),
            ("flour", 50.0, "kg", 1.80, "singapore"),
        ]
        conn.executemany(
            "INSERT INTO kitchen_stock (ingredient, quantity, unit, cost_per_unit, region) VALUES (?, ?, ?, ?, ?)",
            defaults,
        )


init_db()
seed_kitchen_stock()
