"""Rebuild everything from current data.

    python scripts/finalize.py [--final] [--draws N] [--from-derived]

Full mode (needs the local Google Trends cache, see README): export the cache, rebuild attention, the model, uncertainty, every validation table,
the verdict and the figures. Stages run in dependency order and the script exits non-zero if any stage fails.

--from-derived (also chosen automatically when the cache is absent): re-runs the model computation from the committed matrices, the corroboration
table, the stress cases, the charts and the verdict. It reuses the committed uncertainty and measurement tables (robustness, channel decomposition,
second proxy), which are produced only in full mode.
"""
import pathlib
import subprocess
import sys
import time

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "scripts"))
from paths import WORK  # noqa: E402

draws = sys.argv[sys.argv.index("--draws") + 1] if "--draws" in sys.argv else "300"
final = ["--final"] if "--final" in sys.argv else []
derived = "--from-derived" in sys.argv or not (WORK / "trends.sqlite").exists()

if derived:
    print("derived mode: no local Trends cache (or --from-derived); reusing committed uncertainty and measurement tables")
    steps = [["build_H_M.py"], ["corroboration.py"], ["stress_cases.py"], ["build_visuals.py"], ["build_report.py"] + final, ["build_story_figures.py"], ["build_results_doc.py"], ["build_protocol_doc.py"]]
else:
    steps = [["export_trends.py"], ["build_P_from_trends.py"], ["build_W_A.py"], ["build_H_M.py"], ["derive_noise.py"], ["robustness.py", draws],
             ["variance_decomposition.py", "150"], ["topdown_validation.py"], ["cosearch_pilot.py"], ["hate_validation.py"],
             ["channel_decomposition.py"], ["measured_hostility.py"], ["corroboration.py"], ["second_proxy.py"],
             ["stress_cases.py"], ["build_visuals.py"],
             ["build_report.py"] + final,              # the verdict
             ["build_story_figures.py"], ["build_results_doc.py"], ["build_protocol_doc.py"]]               # figures that read the verdict (scorecard) must run after it
failed = 0
for s in steps:
    if not (R / "scripts" / s[0]).exists():      # a step that is not shipped in this checkout (for example the protocol builder)
        print(f"{s[0]} skipped (not present)")
        continue
    t = time.time()
    r = subprocess.run([sys.executable, str(R / "scripts" / s[0])] + s[1:], cwd=str(R), capture_output=True, text=True)
    print(f"{s[0]} rc={r.returncode} {time.time()-t:.0f}s", (r.stdout.strip().splitlines() or [''])[-1][:200], (r.stderr.strip().splitlines() or [''])[-1][:200] if r.returncode else "")
    if r.returncode:
        failed = r.returncode
        break
sys.exit(failed)
