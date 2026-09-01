from __future__ import annotations

import os
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from time import time
from typing import Any

from .migrator import Migrator


class StatKeys(StrEnum):
    farm = "farm"
    farmAttempts = "farmAttempts"
    farmSuccesses = "farmSuccesses"
    steal = "steal"
    stealAttempts = "stealAttempts"
    stealSuccesses = "stealSuccesses"
    rankups = "rankups"
    prestiges = "prestiges"
    quizReward = "quizReward"
    quizAttempts = "quizAttempts"
    quizSuccesses = "quizSuccesses"
    quizFailures = "quizFailures"

ZERO_STATS = dict.fromkeys(StatKeys, 0)
RANK_NAMES = (
    "Bankrupt",
    "Backyard Garden",
    "Greenhouse",
    "Acre Farm",
    "10 Acre Farm",
    "Potato Plantation",
    "Industrial Potato Facility",
)

cache = {
    "totals": ZERO_STATS.copy(),
    "today": ZERO_STATS.copy(),
    "week": ZERO_STATS.copy(),
}
sessionTotals = ZERO_STATS.copy()
sessionStart = int(time() * 1000)
playerInfo = {
    "username": "",
    "potatoes": 0,
    "prestige": 0,
    "harvests": 0,
    "steals": 0,
    "stolenFrom": 0,
    "quizzes": 0,
    "quizzesCompleted": 0,
    "farmSize": "",
    "rank": 1,
    "leaderboardRank": 0,
    "totalPlayers": 0,
    "lastCommand": None,
}

_db: sqlite3.Connection | None = None
_lastRecordDate = ""
_lock = RLock()
_balanceRegex = re.compile(r"\[([+-])([\d,]+)\s*⇒\s*(-?[\d,]+)\]")
_cooldownRegex = re.compile(r"✋⏰|aren'?t ready|not ready", re.IGNORECASE)


def _todayStr() -> str:
    return datetime.now(UTC).date().isoformat()


def _weekStartStr() -> str:
    return (datetime.now(UTC).date() - timedelta(days=6)).isoformat()


def _rowStats(row: sqlite3.Row | None) -> dict[StatKeys, int]:
    if row is None:
        return ZERO_STATS.copy()
    return {key: int(row[key]) for key in StatKeys}


def initDb(path: str | None = None) -> None:
    global _db, _lastRecordDate

    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "stats.sqlite")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    _db = sqlite3.connect(path, check_same_thread=False)
    _db.row_factory = sqlite3.Row
    _db.execute("PRAGMA journal_mode = WAL")

    migrator = Migrator(_db)
    migrator.migrate()

    _db.executescript(
        """
        CREATE TABLE IF NOT EXISTS totals (
            id                   INTEGER PRIMARY KEY CHECK (id = 1),
            farm                 INTEGER NOT NULL DEFAULT 0,
            farmAttempts         INTEGER NOT NULL DEFAULT 0,
            farmSuccesses        INTEGER NOT NULL DEFAULT 0,
            steal                INTEGER NOT NULL DEFAULT 0,
            stealAttempts        INTEGER NOT NULL DEFAULT 0,
            stealSuccesses       INTEGER NOT NULL DEFAULT 0,
            rankups              INTEGER NOT NULL DEFAULT 0,
            prestiges            INTEGER NOT NULL DEFAULT 0,
            quizReward           INTEGER NOT NULL DEFAULT 0,
            quizAttempts         INTEGER NOT NULL DEFAULT 0,
            quizSuccesses        INTEGER NOT NULL DEFAULT 0,
            quizFailures         INTEGER NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO totals (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS daily (
            date                 TEXT PRIMARY KEY,
            farm                 INTEGER NOT NULL DEFAULT 0,
            farmAttempts         INTEGER NOT NULL DEFAULT 0,
            farmSuccesses        INTEGER NOT NULL DEFAULT 0,
            steal                INTEGER NOT NULL DEFAULT 0,
            stealAttempts        INTEGER NOT NULL DEFAULT 0,
            stealSuccesses       INTEGER NOT NULL DEFAULT 0,
            rankups              INTEGER NOT NULL DEFAULT 0,
            prestiges            INTEGER NOT NULL DEFAULT 0,
            quizReward           INTEGER NOT NULL DEFAULT 0,
            quizAttempts         INTEGER NOT NULL DEFAULT 0,
            quizSuccesses        INTEGER NOT NULL DEFAULT 0,
            quizFailures         INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            executedAt   TEXT NOT NULL,
            command      TEXT NOT NULL,
            category     TEXT NOT NULL,
            delta        INTEGER NOT NULL,
            balanceAfter INTEGER NOT NULL,
            responseText TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_events_executedAt
            ON events (executedAt);
        CREATE INDEX IF NOT EXISTS idx_events_category_executedAt
            ON events (category, executedAt);
        """,
    )

    cache["totals"] = _rowStats(
        _db.execute(
            """
            SELECT farm, farmAttempts, farmSuccesses, steal, stealAttempts,
                   stealSuccesses, rankups, prestiges, quizReward, quizAttempts,
                   quizSuccesses, quizFailures
            FROM totals WHERE id = 1
            """,
        ).fetchone(),
    )
    cache["today"] = _rowStats(
        _db.execute(
            """
            SELECT farm, farmAttempts, farmSuccesses, steal, stealAttempts,
                   stealSuccesses, rankups, prestiges, quizReward, quizAttempts,
                   quizSuccesses, quizFailures
            FROM daily WHERE date = ?
            """,
            (_todayStr(),),
        ).fetchone(),
    )
    cache["week"] = _rowStats(
        _db.execute(
            """
            SELECT
              COALESCE(SUM(farm), 0) AS farm,
              COALESCE(SUM(farmAttempts), 0) AS farmAttempts,
              COALESCE(SUM(farmSuccesses), 0) AS farmSuccesses,
              COALESCE(SUM(steal), 0) AS steal,
              COALESCE(SUM(stealAttempts), 0) AS stealAttempts,
              COALESCE(SUM(stealSuccesses), 0) AS stealSuccesses,
              COALESCE(SUM(rankups), 0) AS rankups,
              COALESCE(SUM(prestiges), 0) AS prestiges,
              COALESCE(SUM(quizReward), 0) AS quizReward,
              COALESCE(SUM(quizAttempts), 0) AS quizAttempts,
              COALESCE(SUM(quizSuccesses), 0) AS quizSuccesses,
              COALESCE(SUM(quizFailures), 0) AS quizFailures
            FROM daily WHERE date >= ?
            """,
            (_weekStartStr(),),
        ).fetchone(),
    )
    _lastRecordDate = _todayStr()
    _db.commit()


def closeDb() -> None:
    global _db

    with _lock:
        if _db is not None:
            _db.close()
            _db = None


def _record(values: dict[str, int]) -> None:
    global _lastRecordDate

    if _db is None:
        raise RuntimeError("Stats database is not initialized")

    date = _todayStr()
    params = values | {"date": date}

    with _lock:
        _db.execute(
            """
            UPDATE totals SET
              farm = farm + :farm,
              farmAttempts = farmAttempts + :farmAttempts,
              farmSuccesses = farmSuccesses + :farmSuccesses,
              steal = steal + :steal,
              stealAttempts = stealAttempts + :stealAttempts,
              stealSuccesses = stealSuccesses + :stealSuccesses,
              rankups = rankups + :rankups,
              prestiges = prestiges + :prestiges,
              quizReward = quizReward + :quizReward,
              quizAttempts = quizAttempts + :quizAttempts,
              quizSuccesses = quizSuccesses + :quizSuccesses,
              quizFailures = quizFailures + :quizFailures
            WHERE id = 1
            """,
            values,
        )
        _db.execute(
            """
            INSERT INTO daily (
              date, farm, farmAttempts, farmSuccesses, steal, stealAttempts,
              stealSuccesses, rankups, prestiges, quizReward, quizAttempts,
              quizSuccesses, quizFailures
            )
            VALUES (
              :date, :farm, :farmAttempts, :farmSuccesses, :steal, :stealAttempts,
              :stealSuccesses, :rankups, :prestiges, :quizReward, :quizAttempts,
              :quizSuccesses, :quizFailures
            )
            ON CONFLICT(date) DO UPDATE SET
              farm = farm + excluded.farm,
              farmAttempts = farmAttempts + excluded.farmAttempts,
              farmSuccesses = farmSuccesses + excluded.farmSuccesses,
              steal = steal + excluded.steal,
              stealAttempts = stealAttempts + excluded.stealAttempts,
              stealSuccesses = stealSuccesses + excluded.stealSuccesses,
              rankups = rankups + excluded.rankups,
              prestiges = prestiges + excluded.prestiges,
              quizReward = quizReward + excluded.quizReward,
              quizAttempts = quizAttempts + excluded.quizAttempts,
              quizSuccesses = quizSuccesses + excluded.quizSuccesses,
              quizFailures = quizFailures + excluded.quizFailures
            """,
            params,
        )
        _db.commit()

        dateChanged = date != _lastRecordDate
        if dateChanged:
            _lastRecordDate = date
            cache["today"] = ZERO_STATS.copy()
            cache["week"] = _rowStats(
                _db.execute(
                    """
                    SELECT
                      COALESCE(SUM(farm), 0) AS farm,
                      COALESCE(SUM(farmAttempts), 0) AS farmAttempts,
                      COALESCE(SUM(farmSuccesses), 0) AS farmSuccesses,
                      COALESCE(SUM(steal), 0) AS steal,
                      COALESCE(SUM(stealAttempts), 0) AS stealAttempts,
                      COALESCE(SUM(stealSuccesses), 0) AS stealSuccesses,
                      COALESCE(SUM(rankups), 0) AS rankups,
                      COALESCE(SUM(prestiges), 0) AS prestiges
                    FROM daily WHERE date >= ?
                    """,
                    (_weekStartStr(),),
                ).fetchone(),
            )

        for key in StatKeys:
            cache["totals"][key] += values[key]
            cache["today"][key] += values[key]
            sessionTotals[key] += values[key]
            if not dateChanged:
                cache["week"][key] += values[key]


def _recordBalanceChange(
        command: str,
        category: str,
        delta: int,
        balanceAfter: int,
        responseText: str,
) -> None:
    if _db is None:
        raise RuntimeError("Stats database is not initialized")

    executedAt = datetime.now(UTC).isoformat(timespec="milliseconds")
    executedAt = executedAt.replace("+00:00", "Z")
    with _lock:
        _db.execute(
            """
            INSERT INTO events (
              executedAt, command, category, delta, balanceAfter, responseText
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (executedAt, command, category, delta, balanceAfter, responseText[:500]),
        )
        _db.commit()


def getEvents(fromDate: str, toDate: str) -> list[dict]:
    if _db is None:
        raise RuntimeError("Stats database is not initialized")

    with _lock:
        rows = _db.execute(
            """
            SELECT id, executedAt, command, category, delta, balanceAfter, responseText
            FROM events
            WHERE executedAt >= ? AND executedAt <= ?
            ORDER BY executedAt ASC, id ASC
            """,
            (fromDate, toDate),
        ).fetchall()
    return [dict(row) for row in rows]


def getEvent(id: int) -> dict | None:
    if _db is None:
        raise RuntimeError("Stats database is not initialized")

    with _lock:
        row = _db.execute(
            """
            SELECT id, executedAt, command, category, delta, balanceAfter, responseText
            FROM events
            WHERE id = ?
            """,
            (id,),
        ).fetchone()
    return dict(row) if row else None


def updatePlayer(user: Any) -> None:
    rank = max(0, min(int(user.rank), len(RANK_NAMES) - 1))
    with _lock:
        playerInfo.update(
            {
                "username": user.username,
                "potatoes": int(user.potatoes),
                "prestige": int(user.prestige),
                "harvests": int(user.commands.potato.usage),
                "steals": int(user.commands.steal.usage),
                "stolenFrom": int(user.commands.steal.stolenCount),
                "quizzes": int(user.commands.quiz.attempted),
                "quizzesCompleted": int(user.commands.quiz.completed),
                "farmSize": RANK_NAMES[rank],
                "rank": rank,
            },
        )


def setLastCommand(command: str) -> None:
    with _lock:
        playerInfo["lastCommand"] = command


def _parseBalanceChange(text: str) -> tuple[int, int] | None:
    match = _balanceRegex.search(text)
    if match is None:
        return None

    sign = 1 if match.group(1) == "+" else -1
    delta = sign * int(match.group(2).replace(",", ""))
    balanceAfter = int(match.group(3).replace(",", ""))
    return delta, balanceAfter


def _balanceCategory(command: str) -> str:
    normalized = command.lower()
    if command == "steal":
        return "steal"
    if command == "potato":
        return "harvest"
    if command == "rankup":
        return "rankup"
    if command == "prestige":
        return "prestige"
    if command == "rank":
        return "refresh"
    if command == "cdr" or "cooldown" in normalized or command.startswith("shop "):
        return "spending"
    if command == "quiz":
        return "quiz"
    return "other"


def _parseDelta(command: str, responseText: str, isError: bool) -> int:
    if isError or command not in {"potato", "steal"}:
        return 0

    bracketMatch = re.search(r"\[([+-])([\d,]+)", responseText)
    if bracketMatch is not None:
        sign = 1 if bracketMatch.group(1) == "+" else -1
        return sign * int(bracketMatch.group(2).replace(",", ""))

    potatoMatch = re.search(r"([+-])\s*([\d,]+)\s*🥔", responseText)
    if potatoMatch is not None:
        sign = 1 if potatoMatch.group(1) == "+" else -1
        return sign * int(potatoMatch.group(2).replace(",", ""))

    return 0


def recordCommandResult(
    command: str,
    responseText: str,
    isError: bool,
    balanceChange: tuple[int, int] | None = None,
) -> None:
    if not balanceChange:
        balanceChange = _parseBalanceChange(responseText)
    if balanceChange is not None:
        delta, balanceAfter = balanceChange
        with _lock:
            playerInfo["potatoes"] = balanceAfter
        _recordBalanceChange(
            command,
            _balanceCategory(command),
            delta,
            balanceAfter,
            responseText,
        )

    if _cooldownRegex.search(responseText):
        return
    if command == "potato" and "♻⏰" in responseText:
        return
    if command not in {"potato", "steal", "rankup", "prestige", "quiz"}:
        return

    delta = balanceChange[0] if balanceChange is not None else _parseDelta(
        command,
        responseText,
        isError,
    )
    values = {
        "farm": delta if command == "potato" else 0,
        "farmAttempts": 1 if command == "potato" else 0,
        "farmSuccesses": 1 if command == "potato" and delta > 0 else 0,
        "steal": delta if command == "steal" else 0,
        "stealAttempts": 1 if command == "steal" else 0,
        "stealSuccesses": 1 if command == "steal" and delta > 0 else 0,
        "rankups": 1 if command == "rankup" and not isError else 0,
        "prestiges": 1 if command == "prestige" and not isError else 0,
        "quizReward": delta if command == "quiz" and delta > 0 else 0,
        "quizAttempts": 1 if command == "quiz" else 0,
        "quizSuccesses": 1 if command == "quiz" and delta > 0 else 0,
        "quizFailures": 1 if command == "quiz" and isError else 0,
    }
    _record(values)


def recordRefreshedBalanceChange(
        command: str,
        balanceBefore: int,
        responseText: str,
) -> None:
    with _lock:
        balanceAfter = int(playerInfo["potatoes"])
    delta = balanceAfter - balanceBefore
    if delta == 0:
        return

    _recordBalanceChange(
        command,
        _balanceCategory(command),
        delta,
        balanceAfter,
        responseText,
    )


def getStatsPayload() -> dict:
    with _lock:
        return {
            "player": playerInfo.copy(),
            "session": {
                "elapsedMs": int(time() * 1000) - sessionStart,
                **sessionTotals,
            },
            "today": cache["today"].copy(),
            "week": cache["week"].copy(),
            "allTime": cache["totals"].copy(),
        }
