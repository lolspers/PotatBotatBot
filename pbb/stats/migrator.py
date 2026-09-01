import sqlite3
from collections.abc import Callable

import pbb.globals as g


class Migrator:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db: sqlite3.Connection = db

        self.migrations: list[Callable[[], None]] = [
            self.migration_01,
        ]


    def migrate(self) -> None:
        version: int = self.db.execute("PRAGMA user_version").fetchone()["user_version"]

        if version > len(self.migrations):
            raise Exception(f"Stats: Database version {version} is newer than supported version " \
                            f"{len(self.migrations)}")

        try:
            for i in range(version, len(self.migrations)):
                self.migrations[i]()
                self.db.execute(f"PRAGMA user_version = {i + 1}")
                self.db.commit()

                g.logger.info(f"Stats: Applied migration {i + 1} ({self.migrations[i].__name__})")

        except Exception as e:
            self.db.rollback()
            raise Exception("Stats: Failed migrate database " \
                            f"({version} -> {len(self.migrations)})") from e



    def migration_01(self) -> None:
        hasLegacyEvents = self.tableExists("balance_events")
        hasEvents = self.tableExists("events")

        if not hasLegacyEvents:
            return

        # table name
        if hasEvents:
            self.db.execute("""
                INSERT INTO events
                    (executedAt, command, category, delta, balanceAfter, responseText)
                SELECT executedAt, command, category, delta, balanceAfter, responseText
                FROM balance_events;
                DROP TABLE balance_events;
            """)
        else:
            self.db.execute("ALTER TABLE balance_events RENAME to events")

        # normalize events
        self.db.execute("""
            UPDATE events SET category = 'spending' WHERE category = 'shop_cdr';
        """)

        # add quiz columns
        QUIZ_COLUMNS: list[str] = [
            "quizReward",
            "quizAttempts",
            "quizSuccesses",
            "quizFailures",
        ]

        for table in ["totals", "daily"]:
            columns = self.tableColumns(table)

            for column in QUIZ_COLUMNS:
                if column not in columns:
                    self.db.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")



    def tableExists(self, table: str) -> bool:
        return bool(self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone())


    def tableColumns(self, table: str) -> list[str]:
        return [
            row["name"]
            for row in
            self.db.execute(f"PRAGMA table_info({table})").fetchall()
        ]
