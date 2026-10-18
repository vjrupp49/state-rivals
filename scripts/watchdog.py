"""Restart the Trends worker if its heartbeat is stale. Safe to run any time,
from anywhere (me, a scheduled rescue task, or by hand). Prints one line.

    python scripts/watchdog.py            # restart worker if stale and still before pull-stop
    python scripts/watchdog.py --agent    # also report agent-heartbeat staleness
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
from paths import WORK
STATE = WORK / "STATE.json"
PULL_STOP = dt.datetime.fromisoformat(os.environ.get("SR_PULL_STOP", "2026-10-25T00:00:00"))


def _alive(pid):
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259
    except Exception:
        return True


def age(path):
    try:
        d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        return (dt.datetime.now() - dt.datetime.fromisoformat(d["ts"])).total_seconds(), d
    except Exception:
        return None, {}


def main():
    a, st = age(STATE)
    msg = []
    if st.get("phase") == "finished":
        msg.append("worker=FINISHED")
    elif dt.datetime.now() >= PULL_STOP:
        msg.append("worker=past_pull_stop")
    else:
        lock = WORK / "worker.pid"
        try:
            lp = int(lock.read_text().strip())
        except Exception:
            lp = 0
        alive = bool(lp) and _alive(lp)
        if alive and a is not None and a < 900:
            msg.append(f"worker=OK pid={lp} age={a:.0f}s jobs={st.get('jobs_ok')}/{st.get('jobs_planned')} phase={st.get('phase')}")
        else:
            if alive:
                subprocess.run(["taskkill", "/F", "/PID", str(lp)], capture_output=True)
            flags = 0x00000008 | 0x00000200 | 0x08000000
            out = open(WORK / "worker.stdout", "ab")
            subprocess.Popen([sys.executable, str(ROOT / "scripts" / "trends_worker.py")], cwd=str(ROOT),
                             stdout=out, stderr=out, creationflags=flags, close_fds=True)
            msg.append(f"worker=RESTARTED (alive={alive}, stale age={a})")
    if "--agent" in sys.argv:
        ag, d = age(ROOT / "logs" / "AGENT_HEARTBEAT.json")
        msg.append(f"agent_heartbeat_age_s={None if ag is None else int(ag)}")
    print(" | ".join(msg))


if __name__ == "__main__":
    main()

