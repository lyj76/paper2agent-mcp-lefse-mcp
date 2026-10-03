"""Replay the official selo example with the pinned R/rpy2 stack (CLI route).

Runs the exact upstream commands from example/bioconda-lefse_run.sh against the
official small HMP aerobiosis dataset and writes native outputs to
.work/output/reference. Publishes the formatted input and result table as
portable acceptance fixtures under resources/acceptance.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO = PROJECT_ROOT / "repo"
WORK_OUT = PROJECT_ROOT / ".work" / "output" / "reference"
ACCEPTANCE = PROJECT_ROOT / "resources" / "acceptance"
INPUT_TXT = ACCEPTANCE / "hmp_aerobiosis_small.txt"

WORK_OUT.mkdir(parents=True, exist_ok=True)


def run(args: list[str], name: str) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(REPO), str(PROJECT_ROOT / "src"), env.get("PYTHONPATH", "")) if p
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(args, capture_output=True, text=True, env=env)
    (WORK_OUT / f"{name}.stdout.log").write_text((proc.stdout or "")[-5000:])
    (WORK_OUT / f"{name}.stderr.log").write_text((proc.stderr or "")[-8000:])
    return proc.returncode


def report(name: str, value) -> None:
    (WORK_OUT / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False))


codes = {}
formatted = WORK_OUT / "hmp_aerobiosis_small.in"
res = WORK_OUT / "hmp_aerobiosis_small.res"
png_lda = WORK_OUT / "lda_effect_size.png"
png_cladogram = WORK_OUT / "cladogram.png"

codes["format_input"] = run([sys.executable, "-m", "lefse.lefse_format_input",
    str(INPUT_TXT), str(formatted), "-c", "1", "-s", "2", "-u", "3", "-o", "1000000",
    "--output_table", str(WORK_OUT / "formatted_table.txt")], "lefse_format_input")

codes["run"] = run([sys.executable, "-m", "lefse.lefse_run", str(formatted), str(res)],
                   "lefse_run")

if codes["run"] == 0:
    codes["plot_res"] = run([sys.executable, "-m", "lefse.lefse_plot_res",
        str(res), str(png_lda), "--format", "png"], "lefse_plot_res")
    codes["plot_cladogram"] = run([sys.executable, "-m", "lefse.lefse_plot_cladogram",
        str(res), str(png_cladogram), "--format", "png", "--title", "Cladogram"],
        "lefse_plot_cladogram")
else:
    codes["plot_res"] = "skipped"
    codes["plot_cladogram"] = "skipped"

records = []
if res.is_file():
    for line in res.read_text().splitlines():
        parts = line.strip("\n").split("\t")
        if len(parts) >= 5:
            records.append({
                "feature": parts[0],
                "log10_max_class_mean": float(parts[1]) if parts[1] else None,
                "enriched_class": parts[2] if parts[2] else None,
                "lda_score": float(parts[3]) if parts[3] else None,
                "kruskal_wallace_pvalue": parts[4] if parts[4] != "-" else None,
            })

summary = {
    "exit_codes": codes,
    "n_features_significant": sum(1 for r in records if r["lda_score"] is not None),
    "n_features_tested": len(records),
}
report("reference_summary", summary)
print(json.dumps(summary, indent=2))
sys.exit(0 if all(c == 0 for k, c in codes.items() if isinstance(c, int)) else 1)