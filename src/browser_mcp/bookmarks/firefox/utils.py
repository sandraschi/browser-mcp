import configparser
import os
from pathlib import Path
from typing import Any


def get_platform() -> str:
    if os.name == "nt":
        return "windows"
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():
            return "darwin"
    return "linux"

def get_profiles_ini_path() -> Path | None:
    platform = get_platform()
    if platform == "windows":
        return Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "profiles.ini"
    elif platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Firefox" / "profiles.ini"
    else:
        return Path.home() / ".mozilla" / "firefox" / "profiles.ini"

def parse_profiles_ini() -> dict[str, dict[str, Any]]:
    profiles_ini = get_profiles_ini_path()
    if not profiles_ini or not profiles_ini.exists():
        return {}
    config = configparser.ConfigParser()
    config.read(profiles_ini)
    profiles = {}
    for section in config.sections():
        if section.startswith("Profile"):
            profile = dict(config[section])
            if "Path" in profile:
                profiles[profile.get("Name", profile["Path"])] = profile
    return profiles

def get_profile_directory(profile_name: str | None = None) -> Path | None:
    profiles = parse_profiles_ini()
    if not profiles:
        return None
    if not profile_name:
        for name, profile in profiles.items():
            if profile.get("Default", "0") == "1":
                profile_name = name
                break
        else:
            profile_name = next(iter(profiles.keys()), None)
    if profile_name not in profiles:
        return None
    profile = profiles[profile_name]
    base_dir = get_profiles_ini_path().parent
    if profile.get("IsRelative", "1") == "1":
        return base_dir / profile["Path"]
    else:
        return Path(profile["Path"])

def get_places_db_path(profile_name: str | None = None) -> Path | None:
    profile_dir = get_profile_directory(profile_name)
    if not profile_dir:
        return None
    return profile_dir / "places.sqlite"
