"""LEfSe MCP server entry point built on the paper2mcp CLI wrapper.

Exposes the reproducibility-tested LEfSe command-line tools as fastmcp tools,
plus one workflow prompt and stable README/method resources.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastmcp import FastMCP

from src.tools import cli_wrapper

server = FastMCP("lefse-mcp")
server.mount(cli_wrapper.cli_wrapper_mcp)


@server.resource("lefse://method/README")
def readme_resource() -> str:
    """LEfSe repository README describing the method and installation."""
    readme = PROJECT_ROOT / "repo" / "README.md"
    if readme.is_file():
        return readme.read_text(encoding="utf-8")
    return "LEfSe: Linear discriminant analysis Effect Size (SegataLab)."


@server.resource("lefse://method/input-format")
def input_format_resource() -> str:
    """Input data contract for the LEfSe abundance-matrix workflow."""
    return (
        "LEfSe 输入为制表符分隔的丰度矩阵，特征按行排列（默认），"
        "每列是一个样本。前几行为分组元数据：第一行 class（必选）、"
        "第二行 subclass（可选，用 -s/-s 行号指定）、第三行 subject（可选）。\n\n"
        "特征名以 '.' 分隔分类层级（如 Bacteria.Actinobacteria.Actinobacteria），"
        "format_lefse_input 会按该层级补全缺失级别并归一化（-o，默认不归一化 -1）。\n\n"
        "典型调用行号：class_row=1, subclass_row=2, subject_row=3。"
        "若无 subclass/subject，请在调用中传入 0 关闭对应行。"
    )


@server.resource("lefse://method/output-format")
def output_format_resource() -> str:
    """Output contract for LEfSe result tables and figures."""
    return (
        "LEfSe 结果表（.res）为制表符分隔文本，每行一个显著特征：\n"
        "  feature | log10(max class mean) | enriched class | LDA score (log10) | Kruskal-Wallis p-value\n"
        "feature 名中的 '.' 分隔对应分类层级（界、门、纲、目、科、属…）。\n\n"
        "可视化产物：\n"
        "  - LDA 效果量柱状图（plot_lefse_lda），水平/垂直方向可选；\n"
        "  - 分类层级树图 cladogram（plot_lefse_cladogram），"
        "以物种丰度为节点大小、以显著特征染色。"
    )


@server.prompt()
def lefse_diff_feature_analysis() -> str:
    return (
        "使用 LEfSe 分析不同组别的差异微生物特征。\n\n"
        "请用户提供：\n"
        "1. 制表符分隔的微生物丰度矩阵文件路径（特征按行，样本按列，"
        "前几行为 class/subclass/subject 分组行）。\n"
        "2. 分组行号：class_row（默认 1）、subclass_row（默认 2）、subject_row（默认 3，"
        "不存在时传 0 关闭）。\n\n"
        "建议步骤：\n"
        "1. 调用 format_lefse_input 把丰度矩阵转换成 LEfSe 输入文件；\n"
        "2. 调用 run_lefse_analysis 执行 Kruskal-Wallis/Wilcoxon 检验与 LDA 效应量，"
        "可用 anova_alpha、wilcoxon_alpha、lda_threshold、normalization 调整阈值；\n"
        "3. 调用 plot_lefse_lda 生成 LDA 效果量柱状图；\n"
        "4. 调用 plot_lefse_cladogram 生成分类层级树图 cladogram。\n\n"
        "也可以直接调用 run_full_lefse_workflow 一次性完成上述全部步骤。\n\n"
        "输出：差异特征结果表（含特征名、层级数、富集组别、p 值、LDA 效应量）、"
        "LDA 柱状图与 cladogram 图片文件路径。\n"
        "局限：LEfSe 统计显著性依赖样本量与分类平衡；结果的科学解读需结合领域知识，"
        "本工具只复现官方 LEfSe 程序的统计与绘图行为。"
    )

if __name__ == "__main__":
    server.run()