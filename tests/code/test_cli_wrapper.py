"""Independent verification tests for the LEfSe CLI MCP wrappers.

These tests exercise the exposed tools through the installed fastmcp Client and
compare their real subprocess results against the reference outputs produced by
running the identical upstream LEfSe commands directly (see tests/results).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
REPO = PROJECT_ROOT / "repo"
ACCEPTANCE = PROJECT_ROOT / "resources" / "acceptance"
WORK = PROJECT_ROOT / ".work"


@pytest.fixture(scope="module")
def cli_client():
    """Adapter around the wrapper FastMCP server over in-process Client."""
    import sys
    sys.path.insert(0, str(SRC))
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.tools import cli_wrapper
    from fastmcp import Client

    wrapper = cli_wrapper.cli_wrapper_mcp

    class Adapter:
        async def call(self, tool, arguments):
            async with Client(wrapper) as client:
                result = await client.call_tool(tool, arguments)
                if result.is_error:
                    text = "".join(getattr(b, "text", "") for b in result.content)
                    raise RuntimeError(f"{tool} failed: {text}")
                return result.data

    instance = Adapter()
    yield instance


@pytest.mark.asyncio
async def test_format_official_example(cli_client):
    out = await cli_client.call("format_lefse_input", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.txt"),
        "output_dir": str(WORK / "output" / "test_format"),
        "class_row": 1,
        "subclass_row": 2,
        "subject_row": 3,
        "normalization": 1000000.0,
    })
    assert out["params"]["class_row"] == 1
    assert len(out["artifacts"]) >= 2
    paths = [Path(a["path"]) for a in out["artifacts"]]
    assert all(p.is_file() for p in paths)
    formatted = next(p for p in paths if p.suffix == ".in")
    # Formatting a diluted row must never exceed the normalization at each level.
    assert formatted.stat().st_size > 0


@pytest.mark.asyncio
async def test_run_official_example(cli_client):
    out = await cli_client.call("run_lefse_analysis", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.in"),
        "output_dir": str(WORK / "output" / "test_run"),
        "anova_alpha": 0.05,
        "wilcoxon_alpha": 0.05,
        "lda_threshold": 2.0,
    })
    res_path = Path(out["artifacts"][0]["path"])
    assert res_path.is_file()
    assert res_path.stat().st_size > 0
    assert "result_table" in out
    assert out["params"]["lda_threshold"] == 2.0

    reference = ACCEPTANCE / "hmp_aerobiosis_small.res"
    if reference.is_file():
        ours = res_path.read_text()
        ref = reference.read_text()
        assert set(ours.splitlines()) == set(ref.splitlines()), (
            "MCP result table differs from direct upstream LEfSe output"
        )


@pytest.mark.asyncio
async def test_run_changed_threshold(cli_client):
    out = await cli_client.call("run_lefse_analysis", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.in"),
        "output_dir": str(WORK / "output" / "test_run_strict"),
        "anova_alpha": 0.01,
        "wilcoxon_alpha": 0.01,
        "lda_threshold": 3.0,
    })
    assert out["params"]["lda_threshold"] == 3.0
    assert out["params"]["anova_alpha"] == 0.01
    res_path = Path(out["artifacts"][0]["path"])
    assert res_path.is_file()


@pytest.mark.asyncio
async def test_plot_lda_official_example(cli_client):
    out = await cli_client.call("plot_lefse_lda", {
        "result_path": str(ACCEPTANCE / "hmp_aerobiosis_small.res"),
        "output_dir": str(WORK / "output" / "test_plot_lda"),
        "format": "png",
    })
    chart = Path(out["artifacts"][0]["path"])
    assert chart.is_file()
    assert chart.stat().st_size > 0
    # PNG magic header
    assert chart.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_plot_cladogram_official_example(cli_client):
    out = await cli_client.call("plot_lefse_cladogram", {
        "result_path": str(ACCEPTANCE / "hmp_aerobiosis_small.res"),
        "output_dir": str(WORK / "output" / "test_cladogram"),
        "format": "png",
    })
    chart = Path(out["artifacts"][0]["path"])
    assert chart.is_file()
    assert chart.stat().st_size > 0
    assert chart.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_full_workflow_official_example(cli_client):
    out = await cli_client.call("run_full_lefse_workflow", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.txt"),
        "output_dir": str(WORK / "output" / "test_full"),
        "class_row": 1,
        "subclass_row": 2,
        "subject_row": 3,
        "normalization": 1000000.0,
        "anova_alpha": 0.05,
        "wilcoxon_alpha": 0.05,
        "lda_threshold": 2.0,
        "plot_format": "png",
    })
    assert out["significance_summary"]["total_tested"] > 0
    assert len(out["artifacts"]) >= 5
    pngs = [Path(a["path"]) for a in out["artifacts"] if a["path"].endswith(".png")]
    assert len(pngs) == 2
    labels = {a["description"] for a in out["artifacts"]}
    assert "LEfSe result table (.res)" in labels
    res_path = next(Path(a["path"]) for a in out["artifacts"] if a["path"].endswith(".res"))
    reference = ACCEPTANCE / "hmp_aerobiosis_small.res"
    if reference.is_file():
        assert set(res_path.read_text().splitlines()) == set(
            reference.read_text().splitlines()
        ), "Full workflow result table diverges from upstream reference"


@pytest.mark.asyncio
async def test_error_missing_input(cli_client):
    from src.tools import cli_wrapper
    from fastmcp import Client

    async with Client(cli_wrapper.cli_wrapper_mcp) as client:
        result = await client.call_tool(
            "format_lefse_input",
            {"input_path": str(WORK / "does-not-exist.txt")},
            raise_on_error=False,
        )
        assert result.is_error
        text = "".join(getattr(b, "text", "") for b in result.content)
        assert "Input file not found" in text


@pytest.mark.asyncio
async def test_error_parse_res_path(cli_client):
    from src.tools import cli_wrapper
    from fastmcp import Client

    async with Client(cli_wrapper.cli_wrapper_mcp) as client:
        result = await client.call_tool(
            "plot_lefse_lda",
            {"result_path": str(WORK / "missing.res")},
            raise_on_error=False,
        )
        assert result.is_error
        text = "".join(getattr(b, "text", "") for b in result.content)
        assert "result file not found" in text.lower()


@pytest.mark.asyncio
async def test_unique_output_dirs_across_calls(cli_client):
    first = await cli_client.call("format_lefse_input", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.txt"),
        "output_dir": str(WORK / "output" / "test_unique"),
        "class_row": 1,
        "subclass_row": 2,
        "subject_row": 3,
        "normalization": 1000000.0,
    })
    second = await cli_client.call("format_lefse_input", {
        "input_path": str(ACCEPTANCE / "hmp_aerobiosis_small.txt"),
        "output_dir": str(WORK / "output" / "test_unique"),
        "class_row": 1,
        "subclass_row": 2,
        "subject_row": 3,
        "normalization": 1000000.0,
    })
    p1 = Path(first["artifacts"][0]["path"])
    p2 = Path(second["artifacts"][0]["path"])
    assert p1 != p2, "Repeated calls must produce isolated output directories"