from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .db import FirefoxDB


async def find_old_bookmarks(age_days: int = 365, profile_path: str | None = None) -> dict[str, Any]:
    db = FirefoxDB(Path(profile_path) if profile_path else None)
    cutoff_date = datetime.now() - timedelta(days=age_days)
    cutoff_timestamp = int(cutoff_date.timestamp() * 1000000)
    cursor = db.execute("""
        SELECT b.id, b.title, p.url, 
               b.dateAdded / 1000000 as created_ts,
               b.lastModified / 1000000 as modified_ts,
               (strftime('%s', 'now') - b.dateAdded/1000000)/86400 as age_days,
               (strftime('%s', 'now') - b.dateAdded/1000000)/86400/365.25 as age_years
        FROM moz_bookmarks b
        LEFT JOIN moz_places p ON b.fk = p.id
        WHERE b.type = 1 AND b.dateAdded < ?
        ORDER BY b.dateAdded ASC
    """, (cutoff_timestamp,))
    old_bookmarks = []
    for row in cursor.fetchall():
        bm = dict(row)
        if bm["created_ts"]:
            bm["created"] = datetime.fromtimestamp(bm["created_ts"]).isoformat()
        if bm["modified_ts"]:
            bm["last_modified"] = datetime.fromtimestamp(bm["modified_ts"]).isoformat()
        bm["age_years"] = round(bm["age_years"], 1) if bm["age_years"] else None
        old_bookmarks.append(bm)
    return {"cutoff_date": cutoff_date.isoformat(), "bookmark_count": len(old_bookmarks), "bookmarks": old_bookmarks}


async def find_forgotten_bookmarks(days_unvisited: int = 365, profile_path: str | None = None) -> dict[str, Any]:
    db = FirefoxDB(Path(profile_path) if profile_path else None)
    cutoff_date = datetime.now() - timedelta(days=days_unvisited)
    cutoff_timestamp = int(cutoff_date.timestamp() * 1000000)
    cursor = db.execute("""
        SELECT b.id, b.title, p.url, 
               p.last_visit_date / 1000000 as last_visit_ts,
               (strftime('%s', 'now') - p.last_visit_date/1000000)/86400 as days_since_visit
        FROM moz_places p
        JOIN moz_bookmarks b ON b.fk = p.id
        WHERE b.type = 1 AND p.last_visit_date > 0 AND p.last_visit_date < ?
        ORDER BY p.last_visit_date ASC
    """, (cutoff_timestamp,))
    stale = []
    for row in cursor.fetchall():
        bm = dict(row)
        if bm["last_visit_ts"]:
            bm["last_visit"] = datetime.fromtimestamp(bm["last_visit_ts"]).isoformat()
        stale.append(bm)
    return {"cutoff_date": cutoff_date.isoformat(), "bookmark_count": len(stale), "bookmarks": stale}


async def get_bookmark_stats(profile_path: str | None = None) -> dict[str, Any]:
    db = FirefoxDB(Path(profile_path) if profile_path else None)
    total = db.execute("SELECT COUNT(*) as count FROM moz_bookmarks WHERE type = 1").fetchone()["count"]
    age_cursor = db.execute("""
        SELECT COUNT(*) as count,
            CASE 
                WHEN (strftime('%s', 'now') - p.last_visit_date/1000000) < 7 THEN '1_week'
                WHEN (strftime('%s', 'now') - p.last_visit_date/1000000) < 30 THEN '1_month'
                WHEN (strftime('%s', 'now') - p.last_visit_date/1000000) < 90 THEN '3_months'
                WHEN (strftime('%s', 'now') - p.last_visit_date/1000000) < 365 THEN '1_year'
                ELSE 'older'
            END as age_group
        FROM moz_places p
        JOIN moz_bookmarks b ON b.fk = p.id
        WHERE p.last_visit_date > 0
        GROUP BY age_group
    """)
    age_stats = {row["age_group"]: row["count"] for row in age_cursor.fetchall()}
    return {"total_bookmarks": total, "age_distribution": age_stats}
