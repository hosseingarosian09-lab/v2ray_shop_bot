import sqlite3
import uuid
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    duration_months INTEGER NOT NULL UNIQUE CHECK (duration_months > 0),
                    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    traffic_gb INTEGER NOT NULL CHECK (traffic_gb > 0),
                    price INTEGER NOT NULL CHECK (price > 0),
                    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    UNIQUE (category_id, traffic_gb)
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_id INTEGER,
                    duration_months INTEGER NOT NULL CHECK (duration_months > 0),
                    duration_label TEXT NOT NULL,
                    traffic_gb INTEGER NOT NULL CHECK (traffic_gb > 0),
                    price INTEGER NOT NULL CHECK (price > 0),
                    status TEXT NOT NULL DEFAULT 'pending_payment'
                        CHECK (status IN ('pending_payment', 'pending_review', 'approved', 'rejected', 'cancelled')),
                    receipt_file_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (plan_id) REFERENCES plans(id)
                );
                """
            )

            self._migrate_orders_for_cancelled(conn)

            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_id INTEGER NOT NULL UNIQUE,
                    duration_months INTEGER NOT NULL CHECK (duration_months > 0),
                    duration_label TEXT NOT NULL,
                    traffic_gb INTEGER NOT NULL CHECK (traffic_gb > 0),
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'expired')),
                    config_uri TEXT NOT NULL,
                    subscription_url TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                );

                CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
                CREATE INDEX IF NOT EXISTS idx_services_user_id ON services(user_id);
                """
            )

            self._seed_catalog(conn)
            self._localize_categories(conn)

    def _migrate_orders_for_cancelled(self, conn: sqlite3.Connection) -> None:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
        ).fetchone()
        if not row or not row["sql"] or "cancelled" in row["sql"]:
            return

        conn.execute("ALTER TABLE orders RENAME TO orders_legacy")
        conn.executescript(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER,
                duration_months INTEGER NOT NULL CHECK (duration_months > 0),
                duration_label TEXT NOT NULL,
                traffic_gb INTEGER NOT NULL CHECK (traffic_gb > 0),
                price INTEGER NOT NULL CHECK (price > 0),
                status TEXT NOT NULL DEFAULT 'pending_payment'
                    CHECK (status IN ('pending_payment', 'pending_review', 'approved', 'rejected', 'cancelled')),
                receipt_file_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            );

            INSERT INTO orders (
                id, user_id, plan_id, duration_months, duration_label,
                traffic_gb, price, status, receipt_file_id, created_at, updated_at
            )
            SELECT
                id, user_id, plan_id, duration_months, duration_label,
                traffic_gb, price, status, receipt_file_id, created_at, updated_at
            FROM orders_legacy;

            DROP TABLE orders_legacy;
            """
        )

    def _seed_catalog(self, conn: sqlite3.Connection) -> None:
        categories = [
            ("۱ ماهه", 1),
            ("۳ ماهه", 3),
            ("۶ ماهه", 6),
        ]
        conn.executemany(
            """
            INSERT INTO categories (name, duration_months)
            VALUES (?, ?)
            ON CONFLICT(duration_months) DO NOTHING
            """,
            categories,
        )

        plan_count = conn.execute("SELECT COUNT(*) AS count FROM plans").fetchone()["count"]
        if plan_count:
            return

        category_ids = {
            row["duration_months"]: row["id"]
            for row in conn.execute("SELECT id, duration_months FROM categories").fetchall()
        }

        demo_plans = [
            (category_ids[1], 20, 120_000),
            (category_ids[1], 40, 190_000),
            (category_ids[1], 60, 260_000),
            (category_ids[3], 60, 300_000),
            (category_ids[3], 100, 450_000),
            (category_ids[3], 150, 620_000),
            (category_ids[6], 120, 550_000),
            (category_ids[6], 200, 780_000),
            (category_ids[6], 300, 1_100_000),
        ]
        conn.executemany(
            """
            INSERT INTO plans (category_id, traffic_gb, price)
            VALUES (?, ?, ?)
            """,
            demo_plans,
        )

    def _localize_categories(self, conn: sqlite3.Connection) -> None:
        names = {
            1: "۱ ماهه",
            3: "۳ ماهه",
            6: "۶ ماهه",
        }
        for duration_months, name in names.items():
            conn.execute(
                "UPDATE categories SET name = ? WHERE duration_months = ?",
                (name, duration_months),
            )

    def upsert_user(self, user_id: int, username: Optional[str], first_name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name),
            )

    def get_setting(self, key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_admin_id(self) -> Optional[int]:
        value = self.get_setting("admin_id")
        return int(value) if value else None

    def claim_admin(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = 'admin_id'").fetchone()
            if row:
                return False
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('admin_id', ?)",
                (str(user_id),),
            )
            return True

    # ----- Categories -----

    def list_categories(self, *, active_only: bool = False, with_active_plans: bool = False):
        sql = "SELECT * FROM categories WHERE 1 = 1"
        if active_only:
            sql += " AND is_active = 1"
        if with_active_plans:
            sql += (
                " AND EXISTS (SELECT 1 FROM plans p "
                "WHERE p.category_id = categories.id AND p.is_active = 1)"
            )
        sql += " ORDER BY duration_months"
        with self._connect() as conn:
            return conn.execute(sql).fetchall()

    def get_category(self, category_id: int):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM categories WHERE id = ?",
                (category_id,),
            ).fetchone()

    # ----- Plans -----

    def list_plans(self, category_id: int, *, active_only: bool = False):
        sql = "SELECT * FROM plans WHERE category_id = ?"
        params: list[object] = [category_id]
        if active_only:
            sql += " AND is_active = 1"
        sql += " ORDER BY traffic_gb"
        with self._connect() as conn:
            return conn.execute(sql, params).fetchall()

    def get_plan(self, plan_id: int):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT
                    p.*,
                    c.name AS category_name,
                    c.duration_months AS duration_months,
                    c.is_active AS category_active
                FROM plans p
                JOIN categories c ON c.id = p.category_id
                WHERE p.id = ?
                """,
                (plan_id,),
            ).fetchone()

    def add_plan(self, category_id: int, traffic_gb: int, price: int) -> int:
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO plans (category_id, traffic_gb, price)
                    VALUES (?, ?, ?)
                    """,
                    (category_id, traffic_gb, price),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise ValueError("پلنی با این حجم از قبل در این دسته‌بندی وجود دارد.") from exc
            raise ValueError("ساخت پلن انجام نشد. مقادیر را بررسی کنید و دوباره تلاش کنید.") from exc

    def update_plan_traffic(self, plan_id: int, traffic_gb: int) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE plans
                    SET traffic_gb = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (traffic_gb, plan_id),
                )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise ValueError("این حجم از قبل در این دسته‌بندی وجود دارد.") from exc
            raise ValueError("به‌روزرسانی پلن انجام نشد.") from exc

    def update_plan_price(self, plan_id: int, price: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE plans
                SET price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (price, plan_id),
            )

    def toggle_plan(self, plan_id: int) -> Optional[bool]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT is_active FROM plans WHERE id = ?",
                (plan_id,),
            ).fetchone()
            if not row:
                return None
            new_value = 0 if row["is_active"] else 1
            conn.execute(
                """
                UPDATE plans
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_value, plan_id),
            )
            return bool(new_value)

    # ----- Orders -----

    def create_order_from_plan(self, user_id: int, plan_id: int) -> int:
        with self._connect() as conn:
            plan = conn.execute(
                """
                SELECT
                    p.id,
                    p.traffic_gb,
                    p.price,
                    p.is_active,
                    c.name AS category_name,
                    c.duration_months,
                    c.is_active AS category_active
                FROM plans p
                JOIN categories c ON c.id = p.category_id
                WHERE p.id = ?
                """,
                (plan_id,),
            ).fetchone()
            if not plan or not plan["is_active"] or not plan["category_active"]:
                raise ValueError("این پلن دیگر برای خرید در دسترس نیست.")

            user_exists = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not user_exists:
                raise ValueError("اطلاعات کاربر ثبت نشده است. لطفاً /start را بزنید و دوباره تلاش کنید.")

            cursor = conn.execute(
                """
                INSERT INTO orders (
                    user_id,
                    plan_id,
                    duration_months,
                    duration_label,
                    traffic_gb,
                    price,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending_payment')
                """,
                (
                    user_id,
                    plan["id"],
                    plan["duration_months"],
                    plan["category_name"],
                    plan["traffic_gb"],
                    plan["price"],
                ),
            )
            return int(cursor.lastrowid)

    def get_order_for_user(self, order_id: int, user_id: int):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM orders WHERE id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()

    def get_order_for_admin(self, order_id: int):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT
                    o.*,
                    u.username,
                    u.first_name
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                WHERE o.id = ?
                """,
                (order_id,),
            ).fetchone()

    def list_orders_for_user(self, user_id: int, limit: int = 20):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT * FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

    def list_pending_review_orders(self, limit: int = 50):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT
                    o.*,
                    u.username,
                    u.first_name
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                WHERE o.status = 'pending_review'
                ORDER BY o.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def save_order_receipt(self, order_id: int, user_id: int, file_id: str) -> bool:
        with self._connect() as conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()
            if not order or order["status"] not in {"pending_payment", "pending_review"}:
                return False

            conn.execute(
                """
                UPDATE orders
                SET receipt_file_id = ?,
                    status = 'pending_review',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (file_id, order_id, user_id),
            )
            return True

    def cancel_order(self, order_id: int, user_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE orders
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND status = 'pending_payment'
                """,
                (order_id, user_id),
            )
            return cursor.rowcount == 1

    def approve_order(self, order_id: int):
        demo_uuid = str(uuid.uuid4())
        demo_sub_token = uuid.uuid4().hex
        config_uri = (
            f"vless://{demo_uuid}@demo.example.com:443"
            f"?encryption=none&security=tls&type=ws#Demo-Service-{order_id}"
        )
        subscription_url = f"https://demo.example.com/sub/{demo_sub_token}"

        with self._connect() as conn:
            order = conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if not order or order["status"] != "pending_review" or not order["receipt_file_id"]:
                return None

            conn.execute(
                """
                UPDATE orders
                SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending_review'
                """,
                (order_id,),
            )
            conn.execute(
                """
                INSERT INTO services (
                    user_id,
                    order_id,
                    duration_months,
                    duration_label,
                    traffic_gb,
                    status,
                    config_uri,
                    subscription_url
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    order["user_id"],
                    order["id"],
                    order["duration_months"],
                    order["duration_label"],
                    order["traffic_gb"],
                    config_uri,
                    subscription_url,
                ),
            )
            return conn.execute(
                "SELECT * FROM services WHERE order_id = ?",
                (order_id,),
            ).fetchone()

    def reject_order(self, order_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE orders
                SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending_review'
                """,
                (order_id,),
            )
            return cursor.rowcount == 1

    # ----- Services -----

    def list_services_for_user(self, user_id: int):
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT * FROM services
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()

    def get_service_for_user(self, service_id: int, user_id: int):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM services WHERE id = ? AND user_id = ?",
                (service_id, user_id),
            ).fetchone()
