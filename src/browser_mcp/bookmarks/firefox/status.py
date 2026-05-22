import logging
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)

class FirefoxStatusChecker:
    @staticmethod
    def is_firefox_running() -> dict[str, Any]:
        try:
            firefox_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "firefox" in proc.info["name"].lower():
                        firefox_processes.append({
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": proc.info["cmdline"][:3] if proc.info["cmdline"] else [],
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            is_running = len(firefox_processes) > 0
            return {
                "is_running": is_running,
                "process_count": len(firefox_processes),
                "processes": firefox_processes,
                "message": f"Firefox is {'running' if is_running else 'not running'} ({len(firefox_processes)} processes)",
            }
        except Exception as e:
            return {"is_running": False, "error": f"Could not check Firefox status: {e!s}", "message": "Unable to determine Firefox status"}

    @staticmethod
    def check_database_access_safe(profile_path: Path | None = None) -> dict[str, Any]:
        status = FirefoxStatusChecker.is_firefox_running()
        if status.get("error"):
            return {"safe": False, "reason": "status_check_failed", "message": status["message"], "details": status}
        if status["is_running"]:
            return {"safe": False, "reason": "firefox_running", "message": "Firefox is currently running. Close Firefox before accessing bookmark databases.", "details": status}
        if profile_path:
            if not profile_path.exists():
                return {"safe": False, "reason": "profile_not_found", "message": f"Firefox profile not found at: {profile_path}", "details": {"profile_path": str(profile_path)}}
            places_db = profile_path / "places.sqlite"
            if not places_db.exists():
                return {"safe": False, "reason": "database_not_found", "message": f"Firefox places.sqlite not found at: {places_db}", "details": {"database_path": str(places_db)}}
        return {"safe": True, "message": "Safe to access Firefox databases", "details": status}
