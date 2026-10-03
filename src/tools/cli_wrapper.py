"""Tools extracted from SegataLab/lefse command-line scripts (paper2mcp CLI route)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP

REPO_URL = "https://github.com/SegataLab/lefse"
COMMIT = "ff93a8b6a4bf12420cfcb99c67786dee80d388d2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT / "repo"
SRC_ROOT = PROJECT_ROOT / "src"
LEFSE_DIR = REPO_ROOT / "lefse"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / ".work" / "output"

cli_wrapper_mcp = FastMCP("lefse_cli")


def _fresh_output_dir(base: str | None, tool: str) -> Path:
    root = Path(base).resolve() if base else DEFAULT_OUTPUT_ROOT / tool
    out = root / f"{uuid.uuid4().hex}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _run_script(script: str, argv: list[str], timeout: int = 1200) -> str:
    """Invoke an upstream lefse CLI via `python -m lefse.<script>`.

    Invoked as a module (not by path) so the `lefse` / `lefsebiom` packages
    resolve from the pinned checkout on PYTHONPATH instead of being shadowed
    by the script's own directory being placed first on sys.path.
    """
    module = f"lefse.{Path(script).stem}"
    env = dict(os.environ)
    pypath = os.pathsep.join(
        p for p in (str(REPO_ROOT), str(SRC_ROOT), env.get("PYTHONPATH", ""))
        if p
    )
    env["PYTHONPATH"] = pypath
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, "-m", module, *argv],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"lefse command {script} exited {proc.returncode}\n"
            f"stderr: {proc.stderr[-4000:]}"
        )
    return proc.stdout


def _reference(script: str) -> str:
    return f"{REPO_URL}/blob/{COMMIT}/lefse/{script}"


def _validate_float(name: str, value: float, minimum: float | None = None) -> None:
    if value is None:
        raise ValueError(f"{name} must be provided")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")


cli_wrapper_mcp_tools = cli_wrapper_mcp


@cli_wrapper_mcp.tool()
def format_lefse_input(
    input_path: Annotated[str, "Path to the tab-delimited abundance matrix with class/subclass/subject metadata rows, features on rows by default"],
    output_dir: Annotated[str, "Directory for the formatted LEfSe input; a fresh subdirectory is created"] = "",
    class_row: Annotated[int, "1-based row index used as class (default 1)"] = 1,
    subclass_row: Annotated[int, "1-based row index used as subclass; -1 or 0 disables it"] = 2,
    subject_row: Annotated[int, "1-based row index used as subject; -1 or 0 disables it"] = 3,
    normalization: Annotated[float, "Normalization value so each feature level sums to this value (-1 = no normalization)"] = -1.0,
    features_dir: Annotated[Literal["r", "c"], "Features on rows (r, default) or columns (c)"] = "r",
) -> dict:
    """Convert an abundance matrix with group metadata rows into the LEfSe input format.
    Abundance matrix (with class/subclass/subject rows) -> formatted LEfSe input file and plain-text table."""
    if not Path(input_path).is_file():
        raise ValueError(f"Input file not found: {input_path}")
    _validate_float("normalization", normalization)
    if class_row < 1 and class_row != -1:
        raise ValueError("class_row must be a positive 1-based row index")
    out_dir = _fresh_output_dir(output_dir, "format_input")
    in_file = out_dir / "formatted.in"
    table_file = out_dir / "formatted_table.txt"
    cmd = [str(Path(input_path).resolve()), str(in_file), "-c", str(class_row), "-o", str(normalization),
           "-f", features_dir]
    if subclass_row is not None and subclass_row > 0:
        cmd += ["-s", str(subclass_row)]
    if subject_row is not None and subject_row > 0:
        cmd += ["-u", str(subject_row)]
    cmd += ["--output_table", str(table_file)]
    _run_script("lefse_format_input.py", cmd)
    artifacts = [
        {"description": "formatted LEfSe input (pickle)", "path": str(in_file)},
    ]
    if table_file.is_file():
        artifacts.append({"description": "formatted abundance table (txt)", "path": str(table_file)})
    return {
        "message": "Input formatted for LEfSe.",
        "reference": _reference("lefse_format_input.py"),
        "artifacts": artifacts,
        "params": {"class_row": class_row, "subclass_row": subclass_row,
                   "subject_row": subject_row, "normalization": normalization},
    }


@cli_wrapper_mcp.tool()
def run_lefse_analysis(
    input_path: Annotated[str, "Path to the formatted LEfSe input (.in pickled file from format_lefse_input)"],
    output_dir: Annotated[str, "Directory for the LEfSe result table; a fresh subdirectory is created"] = "",
    anova_alpha: Annotated[float, "Alpha for the Kruskal-Wallis (ANOVA) test (default 0.05)"] = 0.05,
    wilcoxon_alpha: Annotated[float, "Alpha for the Wilcoxon test (default 0.05)"] = 0.05,
    lda_threshold: Annotated[float, "Absolute log10 LDA score threshold for reporting (default 2.0)"] = 2.0,
    n_bootstrap: Annotated[int, "Number of bootstrap iterations for LDA (default 30)"] = 30,
    bootstrap_fraction: Annotated[float, "Subsampling fraction per bootstrap iteration (default 0.67)"] = 0.67,
    min_samples_per_subclass: Annotated[int, "Minimum samples per subclass for the Wilcoxon test (default 10)"] = 10,
    multiclass_strategy: Annotated[Literal[0, 1], "0 = one-against-all, 1 = one-against-one (more strict)"] = 0,
    rank_technique: Annotated[Literal["lda", "svm"], "Effect-size ranking: LDA (default) or SVM"] = "lda",
    run_wilcoxon: Annotated[bool, "Perform the Wilcoxon step (default true)"] = True,
    timeout_seconds: Annotated[int, "Per-run wall-clock timeout in seconds"] = 1200,
) -> dict:
    """Run LEfSe Kruskal-Wallis, Wilcoxon and LDA effect-size analysis.
    Formatted LEfSe input (.in) -> differential feature result table (.res) plus parsed records."""
    if not Path(input_path).is_file():
        raise ValueError(f"Formatted input not found: {input_path}")
    _validate_float("anova_alpha", anova_alpha, 0.0)
    _validate_float("wilcoxon_alpha", wilcoxon_alpha, 0.0)
    _validate_float("bootstrap_fraction", bootstrap_fraction, 0.0)
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be >= 1")
    if min_samples_per_subclass < 1:
        raise ValueError("min_samples_per_subclass must be >= 1")
    out_dir = _fresh_output_dir(output_dir, "run_analysis")
    res_file = out_dir / "lefse.res"
    cmd = [str(Path(input_path).resolve()), str(res_file),
           "-a", str(anova_alpha), "-w", str(wilcoxon_alpha), "-l", str(lda_threshold),
           "-b", str(n_bootstrap), "-f", str(bootstrap_fraction),
           "--min_c", str(min_samples_per_subclass), "-r", rank_technique,
           "-y", str(multiclass_strategy), "--wilc", "1" if run_wilcoxon else "0"]
    _run_script("lefse_run.py", cmd, timeout=timeout_seconds)
    records = _parse_res(res_file)
    return {
        "message": f"LEfSe analysis completed; {len([r for r in records if r['lda_score'] is not None])} features pass the LDA threshold.",
        "reference": _reference("lefse_run.py"),
        "artifacts": [{"description": "LEfSe result table (.res)", "path": str(res_file)}],
        "result_table": records,
        "params": {"anova_alpha": anova_alpha, "wilcoxon_alpha": wilcoxon_alpha,
                   "lda_threshold": lda_threshold, "n_bootstrap": n_bootstrap,
                   "bootstrap_fraction": bootstrap_fraction,
                   "min_samples_per_subclass": min_samples_per_subclass,
                   "multiclass_strategy": multiclass_strategy, "rank_technique": rank_technique},
    }


def _parse_res(res_file: Path) -> list[dict]:
    records = []
    with open(res_file) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            feature = parts[0]
            tax_levels = feature.count(".") + 1
            log10_mean = float(parts[1]) if parts[1] else None
            enriched_class = parts[2] if parts[2] else None
            lda = float(parts[3]) if parts[3] else None
            pvalue = parts[4] if parts[4] and parts[4] != "-" else None
            records.append({
                "feature": feature,
                "taxonomy_levels": tax_levels,
                "log10_max_class_mean": log10_mean,
                "enriched_class": enriched_class,
                "lda_score": lda,
                "kruskal_wallace_pvalue": pvalue,
            })
    return records


@cli_wrapper_mcp.tool()
def plot_lefse_lda(
    result_path: Annotated[str, "Path to the LEfSe result table (.res) from run_lefse_analysis"],
    output_dir: Annotated[str, "Directory for the LDA bar chart; a fresh subdirectory is created"] = "",
    format: Annotated[Literal["png", "svg", "pdf"], "Output image format"] = "png",
    dpi: Annotated[int, "Image resolution in dots per inch (default 72)"] = 72,
    title: Annotated[str, "Plot title"] = "",
    orientation: Annotated[Literal["h", "v"], "Horizontal (h, default) or vertical (v) bar chart"] = "h",
    feature_font_size: Annotated[int, "Font size for feature labels (default 7)"] = 7,
) -> dict:
    """Visualize LEfSe LDA effect-size scores as a bar chart.
    LEfSe result table (.res) -> LDA effect-size bar chart image."""
    if not Path(result_path).is_file():
        raise ValueError(f"LEfSe result file not found: {result_path}")
    out_dir = _fresh_output_dir(output_dir, "plot_lda")
    out_file = out_dir / f"lda_effect_size.{format}"
    cmd = [str(Path(result_path).resolve()), str(out_file), "--format", format,
           "--dpi", str(dpi), "--orientation", orientation,
           "--feature_font_size", str(feature_font_size)]
    if title:
        cmd += ["--title", title]
    _run_script("lefse_plot_res.py", cmd)
    return {
        "message": "LDA effect-size bar chart generated.",
        "reference": _reference("lefse_plot_res.py"),
        "artifacts": [{"description": "LDA effect-size bar chart", "path": str(out_file)}],
    }


@cli_wrapper_mcp.tool()
def plot_lefse_cladogram(
    result_path: Annotated[str, "Path to the LEfSe result table (.res) from run_lefse_analysis"],
    output_dir: Annotated[str, "Directory for the cladogram; a fresh subdirectory is created"] = "",
    format: Annotated[Literal["png", "svg", "pdf"], "Output image format"] = "png",
    dpi: Annotated[int, "Image resolution in dots per inch (default 72)"] = 72,
    title: Annotated[str, "Plot title"] = "Cladogram",
) -> dict:
    """Visualize LEfSe biomarkers on their hierarchical taxonomy tree as a cladogram.
    LEfSe result table (.res) -> cladogram image."""
    if not Path(result_path).is_file():
        raise ValueError(f"LEfSe result file not found: {result_path}")
    out_dir = _fresh_output_dir(output_dir, "plot_cladogram")
    out_file = out_dir / f"cladogram.{format}"
    cmd = [str(Path(result_path).resolve()), str(out_file), "--format", format,
           "--dpi", str(dpi), "--title", title]
    _run_script("lefse_plot_cladogram.py", cmd)
    return {
        "message": "Cladogram generated.",
        "reference": _reference("lefse_plot_cladogram.py"),
        "artifacts": [{"description": "taxonomy cladogram", "path": str(out_file)}],
    }


@cli_wrapper_mcp.tool()
def run_full_lefse_workflow(
    input_path: Annotated[str, "Path to the tab-delimited abundance matrix with class/subclass/subject metadata rows (features on rows)"],
    output_dir: Annotated[str, "Directory for all workflow outputs; a fresh subdirectory is created"] = "",
    class_row: Annotated[int, "1-based row index used as class (default 1)"] = 1,
    subclass_row: Annotated[int, "1-based row index used as subclass; 0 disables it (default 2)"] = 2,
    subject_row: Annotated[int, "1-based row index used as subject; 0 disables it (default 3)"] = 3,
    normalization: Annotated[float, "Normalization value so each feature level sums to this value (-1 = no normalization)"] = -1.0,
    anova_alpha: Annotated[float, "Alpha for the Kruskal-Wallis test (default 0.05)"] = 0.05,
    wilcoxon_alpha: Annotated[float, "Alpha for the Wilcoxon test (default 0.05)"] = 0.05,
    lda_threshold: Annotated[float, "Absolute log10 LDA score threshold (default 2.0)"] = 2.0,
    n_bootstrap: Annotated[int, "Number of bootstrap iterations for LDA (default 30)"] = 30,
    bootstrap_fraction: Annotated[float, "Subsampling fraction per bootstrap iteration (default 0.67)"] = 0.67,
    min_samples_per_subclass: Annotated[int, "Minimum samples per subclass for Wilcoxon (default 10)"] = 10,
    multiclass_strategy: Annotated[Literal[0, 1], "0 = one-against-all, 1 = one-against-one"] = 0,
    plot_format: Annotated[Literal["png", "svg", "pdf"], "Image format for both figures"] = "png",
    timeout_seconds: Annotated[int, "Per-run wall-clock timeout in seconds"] = 1800,
) -> dict:
    """Run the complete LEfSe differential-feature workflow (format, analyze, plot).
    Abundance matrix with group rows -> result table, LDA effect-size chart and cladogram."""
    if not Path(input_path).is_file():
        raise ValueError(f"Input file not found: {input_path}")
    _validate_float("anova_alpha", anova_alpha, 0.0)
    _validate_float("wilcoxon_alpha", wilcoxon_alpha, 0.0)
    _validate_float("normalization", normalization)
    _validate_float("bootstrap_fraction", bootstrap_fraction, 0.0)
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be >= 1")
    if min_samples_per_subclass < 1:
        raise ValueError("min_samples_per_subclass must be >= 1")
    out_dir = _fresh_output_dir(output_dir, "full_workflow")
    in_file = out_dir / "formatted.in"
    res_file = out_dir / "lefse.res"
    lda_file = out_dir / f"lda_effect_size.{plot_format}"
    clad_file = out_dir / f"cladogram.{plot_format}"
    table_file = out_dir / "formatted_table.txt"

    fmt = [str(Path(input_path).resolve()), str(in_file), "-c", str(class_row),
           "-o", str(normalization), "--output_table", str(table_file)]
    if subclass_row is not None and subclass_row > 0:
        fmt += ["-s", str(subclass_row)]
    if subject_row is not None and subject_row > 0:
        fmt += ["-u", str(subject_row)]
    _run_script("lefse_format_input.py", fmt, timeout=timeout_seconds)

    run = [str(in_file), str(res_file), "-a", str(anova_alpha), "-w", str(wilcoxon_alpha),
           "-l", str(lda_threshold), "-b", str(n_bootstrap), "-f", str(bootstrap_fraction),
           "--min_c", str(min_samples_per_subclass), "-y", str(multiclass_strategy), "--wilc", "1"]
    _run_script("lefse_run.py", run, timeout=timeout_seconds)

    records = _parse_res(res_file)
    _run_script("lefse_plot_res.py", [str(res_file), str(lda_file), "--format", plot_format],
                timeout=timeout_seconds)
    _run_script("lefse_plot_cladogram.py",
                [str(res_file), str(clad_file), "--format", plot_format, "--title", "Cladogram"],
                timeout=timeout_seconds)

    significant = [r for r in records if r["lda_score"] is not None]
    artifacts = [
        {"description": "formatted LEfSe input", "path": str(in_file)},
        {"description": "LEfSe result table (.res)", "path": str(res_file)},
        {"description": "LDA effect-size bar chart", "path": str(lda_file)},
        {"description": "taxonomy cladogram", "path": str(clad_file)},
    ]
    if table_file.is_file():
        artifacts.append({"description": "formatted abundance table (txt)", "path": str(table_file)})
    return {
        "message": f"LEfSe workflow completed; {len(significant)} features pass the LDA threshold.",
        "reference": _reference("lefse_run.py"),
        "artifacts": artifacts,
        "result_table": records,
        "significance_summary": {
            "total_tested": len(records),
            "significant_at_lda_threshold": len(significant),
        },
        "params": {
            "class_row": class_row, "subclass_row": subclass_row, "subject_row": subject_row,
            "normalization": normalization, "anova_alpha": anova_alpha,
            "wilcoxon_alpha": wilcoxon_alpha, "lda_threshold": lda_threshold,
            "n_bootstrap": n_bootstrap, "bootstrap_fraction": bootstrap_fraction,
            "min_samples_per_subclass": min_samples_per_subclass,
            "multiclass_strategy": multiclass_strategy,
        },
    }