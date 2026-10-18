"""Shared filesystem locations.

The Trends cache (SQLite) is deliberately kept OUT of the project folder: the project
lives in OneDrive, which can corrupt a SQLite file that is written continuously.
Override with the SR_WORK_DIR environment variable.
"""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _default_work():
    if os.environ.get("LOCALAPPDATA"):                 # Windows
        return pathlib.Path(os.environ["LOCALAPPDATA"]) / "StateRivals" / "work"
    base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))
    return base / "state-rivals" / "work"


WORK = pathlib.Path(os.environ["SR_WORK_DIR"]) if os.environ.get("SR_WORK_DIR") else _default_work()
