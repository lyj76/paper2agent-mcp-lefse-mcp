# LEfSe MCP 使用说明（LEfSe-mcp）

`lefse-mcp` 是一个 FastMCP 服务器，把 SegataLab 的
[LEfSe](https://github.com/SegataLab/lefse)（Linear discriminant analysis
Effect Size）命令行工具封装为可复用的 MCP 工具，用于**分析不同组别间的差异
微生物特征**。

## 支持的用途

- 把带分组元数据行的微生物丰度矩阵格式化为 LEfSe 输入文件
  （`format_lefse_input`）。
- 执行 Kruskal-Wallis / Wilcoxon 检验与 LDA 效应量分析，输出差异特征结果表
  （`run_lefse_analysis`）。
- 绘制 LDA 效应量柱状图（`plot_lefse_lda`）与分类层级树图 cladogram
  （`plot_lefse_cladogram`）。
- 一键完成 格式化 → 统计 → 出图 的完整工作流（`run_full_lefse_workflow`）。

同时暴露一个工作流 prompt（`lefse_diff_feature_analysis`）与三个稳定 resource
（`lefse://method/README`、`lefse://method/input-format`、
`lefse://method/output-format`）。

## 输入契约

LEfSe 输入为**制表符分隔的丰度矩阵**：特征按行（默认）、样本按列，前几行为分组
元数据：

```
class     A   B   B   A
subclass  x   y   y   x
subject   1   2   2   1
Feature1  0.1 0.2 ...
Feature2  ...
```

- `class_row`（默认 1）、`subclass_row`（默认 2）、`subject_row`（默认 3）；
  不需要的元数据行传 `0` 关闭。
- 特征名以 `.` 表示分类层级（如 `Bacteria.Actinobacteria.Actinobacteria`），
  format 步骤会自动补全缺失层级。
- `normalization`（默认 -1 = 不归一化）可设 1,000,000 之类的值，使每个分类层级
  的列和缩放到该值，便于 LDA 得分解释。

## 工具与参数

| 工具 | 必填输入 | 主要参数 | 输出 |
| --- | --- | --- | --- |
| `format_lefse_input` | `input_path` | `class_row`/`subclass_row`/`subject_row`、`normalization` | 格式化 `.in` 文件与规范化表 |
| `run_lefse_analysis` | `input_path`（`.in`） | `anova_alpha`、`wilcoxon_alpha`、`lda_threshold`、`n_bootstrap`、`bootstrap_fraction`、`min_samples_per_subclass`、`multiclass_strategy`、`rank_technique` | `.res` 结果表 + 解析后的 `result_table` |
| `plot_lefse_lda` | `result_path`（`.res`） | `format`、`dpi`、`orientation` | LDA 效应量柱状图 |
| `plot_lefse_cladogram` | `result_path`（`.res`） | `format`、`dpi`、`title` | 分类层级树图 |
| `run_full_lefse_workflow` | `input_path`（丰度矩阵） | 上述统计参数 + `plot_format` | `.in`、`.res`、柱状图、cladogram、规范化表 + `significance_summary` |

`.res` 表列为 `feature | log10(max class mean) | enriched class | LDA score | Kruskal-Wallis p-value`。

## 前提与运行环境

- 平台：linux-64（CPU）。
- Python 3.11，依赖见 `src/requirements.txt`（fastmcp 4.0.3、numpy<2、scipy、
  matplotlib、rpy2、biom-format、pytest、pytest-asyncio）。
- LEfSe 需要 R≥3.6 及 R 包 survival、mvtnorm、modeltools、coin、MASS（本交付通过
  pixi 环境提供 R 4.5.3 与 r-survival/r-mvtnorm/r-modeltools/r-coin/r-mass）。
- 本交付的 `src/sitecustomize.py` 在 LEfSe 子进程内把 rpy2 3.x 对「赋值表达式返回
  None」的行为恢复为 LEfSe 依赖的 rpy2 2.x 语义（仅交换可见性，R 计算逐字节相同）；
  这是对 rpy2 3.x 的兼容适配，不改动上游源码。

## 启动

```bash
# 从交付包根目录启动
python server.py
```

默认采用 MCP stdio 传输；作为受管环境，entrypoint 为 `server.py`（environment
`server`）。安装/恢复依赖请使用项目 `pixi.toml` + `pixi.lock`（conda-forge），
例如：

```bash
pixi install          # 通过 pixi 锁恢复
pixi run python server.py
```

## 验证范围与限制

- 已用**官方小规模示例**（biobakery HMP aerobiosis small：
  `resources/acceptance/hmp_aerobiosis_small.txt`）在项目环境与干净重建环境分别
  做严格 MCP 调用验收：全部 5 个工具的真实调用、输入校验错误、重复调用均通过。
- 参考结果（`.res` 结果表）由同一固定 LEfSe 提交的直接上游执行生成并保存在
  `resources/acceptance/`，用于逐一对应用户运行与官方程序的一致性。
- 限制：`rank_technique="svm"` 在上游 `test_svm` 中未实现（返回 `None`），因此
  MCP 仅对 `lda` 路径做了完整验证；迁移 `svm` 会在运行时报错而非伪成功。
- LDA bootstrap 依赖随机抽样（上游固定 seed），在相同输入与 seed 下可复现。
- 通过交付验收的工具覆盖所选工作流，不等同于整个 LEfSe 仓库全部功能已验证。
  科学解读需结合领域知识。