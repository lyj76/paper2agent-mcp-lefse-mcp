# LEfSe 差异微生物分析 MCP

分析不同组别的差异微生物特征，输出分类层级、富集组、Kruskal–Wallis p 值和 LDA 效应量，并生成 LDA 柱状图与分类层级图。

## 1. 用途与适用范围

核心任务：分析不同组别的差异微生物特征，输出分类层级、富集组、Kruskal–Wallis p 值和 LDA 效应量，并生成 LDA 柱状图与分类层级图。

- lefse_diff_feature_analysis

## 2. 来源与方法

源仓库：https://github.com/SegataLab/lefse

对应源文件：
- lefse/lefse_format_input.py
- lefse/lefse_run.py
- lefse/lefse.py
- lefse/lefse_plot_res.py
- lefse/lefse_plot_cladogram.py
- example/bioconda-lefse_run.sh

## 3. 能力与工具

工具清单来源：MCP 实际工具目录

| 工具 | 能力说明 | 输入参数 |
| --- | --- | --- |
| `format_lefse_input` | 将含分组信息的丰度表转换为 LEfSe 输入，并保存规范化表。 | input_path, output_dir, class_row, subclass_row, subject_row, normalization, features_dir |
| `plot_lefse_cladogram` | 读取分类层级与差异结果，绘制分类层级图（cladogram）。 | result_path, output_dir, format, dpi, title |
| `plot_lefse_lda` | 读取 LEfSe 结果，绘制按富集组着色的 LDA 效应量柱状图。 | result_path, output_dir, format, dpi, title, orientation, feature_font_size |
| `run_full_lefse_workflow` | 依次完成输入格式化、差异分析和两种图表绘制，并返回结果、参数与文件路径。 | input_path, output_dir, class_row, subclass_row, subject_row, normalization, anova_alpha, wilcoxon_alpha, lda_threshold, n_bootstrap, bootstrap_fraction, min_samples_per_subclass, multiclass_strategy, plot_format, timeout_seconds |
| `run_lefse_analysis` | 调用原 LEfSe 执行 Kruskal–Wallis/Wilcoxon 筛选及 LDA 分析，返回原始结果表和结构化结果。 | input_path, output_dir, anova_alpha, wilcoxon_alpha, lda_threshold, n_bootstrap, bootstrap_fraction, min_samples_per_subclass, multiclass_strategy, rank_technique, run_wilcoxon, timeout_seconds |

完整输入/输出 Schema 见 `mcp-report.json`；实际服务的 tools/list 是调用依据。

预期输出：
- 差异结果表：特征、分类层级、富集组、Kruskal–Wallis p 值、LDA 效应量；Wilcoxon用于筛选，不逐项输出其p值。
- LDA 效应量柱状图（PNG）
- 分类层级树图 cladogram（PNG）
- 分析参数与依赖版本记录
- 中文分析说明

## 4. 安装与使用

Pixi 锁定多语言环境（linux-64）

资源声明：
```json
{
  "minimumMemoryBytes": 1073741824,
  "maximumMemoryBytes": 4294967296,
  "minimumDiskBytes": 5368709120,
  "minimumCpuCores": 1,
  "gpuRequired": false
}
```

依赖声明（约束不是实际安装版本；精确求解结果见锁文件）：

| 包 | 来源 | 声明约束 |
| --- | --- | --- |
| python | conda | 3.11.* |
| numpy | conda | >=1.24,<2 |
| scipy | conda | >=1.10 |
| matplotlib | conda | >=3.7 |
| r-base | conda | >=4.2 |
| r-survival | conda | * |
| r-mvtnorm | conda | * |
| r-modeltools | conda | * |
| r-coin | conda | * |
| r-mass | conda | * |
| r-matrix | conda | * |
| rpy2 | conda | >=3.5 |
| biom-format | conda | >=2.1.12 |
| fastmcp | pypi | {'version': '==4.0.3'} |
| pytest | pypi | >=7 |
| pytest-asyncio | pypi | >=0.23 |

锁文件 SHA-256：`2d5cbd75220095426f653a62cd8f5a008f92794eff9533c3b20c190732db1dc6`。以下环境记录列出本次实测版本。

```bash
pixi install --locked --manifest-path pixi.toml
pixi run --manifest-path pixi.toml -e server python server.py
```

在仓库根目录运行，依赖版本以 pixi.lock 为准；每个环境的用途和依赖探测见 paper2agent-mcp.json。Paper2Quest 安装时分配专属 UID、HOME、TMP 与缓存；本地 Pixi 命令本身不提供安全沙箱。

## 5. 输入、输出与工作流

实际评测问题：使用 LEfSe 分析不同组别间的差异微生物特征。输入为官方 HMP aerobiosis 小规模示例丰度矩阵（resources/acceptance/hmp_aerobiosis_small.txt，SHA-256 93de04b7…462e），class/subclass/subject 行号 1/2/3，归一化 1000000；请完成格式转换、Kruskal-Wallis/Wilcoxon 与 LDA 效应量分析、LDA 柱状图与 cladogram，返回差异特征结果表与两张图。

实际调用的工具：
- run_full_lefse_workflow
- format_lefse_input
- run_lefse_analysis
- plot_lefse_lda
- plot_lefse_cladogram

复现步骤：
- 将下载包解压并在项目根目录执行 pixi install --locked --manifest-path pixi.toml。
- 启动 MCP：pixi run --manifest-path pixi.toml -e server python server.py。
- 调用 run_full_lefse_workflow，input_path=resources/acceptance/hmp_aerobiosis_small.txt，class_row=1，subclass_row=2，subject_row=3，normalization=1000000，anova_alpha=0.05，wilcoxon_alpha=0.05，lda_threshold=2。
- 检查 result_table 和 significance_summary；本次示例1091个特征、51个达到LDA阈值（High_O2=13、Low_O2=34、Mid_O2=4）。
- 读取返回 artifacts 的 lefse.res、lda_effect_size.png 和 cladogram.png。文件保存在当前运行环境 .work/output 下，每次调用使用独立子目录。
- 分步调用 format_lefse_input → run_lefse_analysis → plot_lefse_lda/plot_lefse_cladogram 可复用同一分析链。

产物路径（相对项目目录）：
- resources/acceptance/hmp_aerobiosis_small.txt
- resources/acceptance/hmp_aerobiosis_small.res
- .work/output/（每次工具调用返回实际子目录与路径）

## 6. 测试数据与复现条件

- HMP aerobiosis small (official LEfSe example)：来源 biobakery test_suite data/lefse/input/hmp_small_aerobiosis.txt (referenced by repo/example/bioconda-lefse_run.sh)；版本/校验 93de04b731427f5da7f9b113189d12fca0b64108a69968b6015ad68dd4ee462e；许可 官方 LEfSe/HMP 测试数据集；本任务未独立确认额外 license 声明

环境记录：
```json
{
  "python": "3.11.16",
  "fastmcp": "4.0.3",
  "numpy": "1.26.4",
  "scipy": "1.17.1",
  "matplotlib": "3.11.2",
  "rpy2": "3.6.8",
  "R": "4.5.3",
  "biom-format": "2.1.17",
  "random_seed": "LEfSe 上游固定 seed 1982（lrand.seed(1982)，见 repo/lefse/lefse.py init()）",
  "params": {
    "class_row": 1,
    "subclass_row": 2,
    "subject_row": 3,
    "normalization": 1000000.0,
    "anova_alpha": 0.05,
    "wilcoxon_alpha": 0.05,
    "lda_threshold": 2.0
  }
}
```

未记录的版本、参数和随机种子须在复现时补齐。

## 7. 验证结果与参考对比

验证层级：**完整工作流验收记录**

参考实现/教程：example/bioconda-lefse_run.sh

| 验收项目 | 预期 | 实测 | 记录结果 |
| --- | --- | --- | --- |
| workflow_end_to_end | run_full_lefse_workflow 在官方示例上完成 格式化→统计→绘图 并返回 significance_summary 与 >=5 artifacts | run_full_lefse_workflow 返回 total_tested=1091、significant_at_lda_threshold=51，artifacts=5（formatted.in、lefse.res、lda_effect_size.png、cladogram.png、formatted_table.txt） | 通过 |
| reference_numeric_agreement | 总测试特征数与显著特征数与上游参考一致（1091/51） | result_table 共 1091 行、51 行 lda_score 非空；与参考 resources/acceptance/hmp_aerobiosis_small.res 的 1091 行完全一致，显著行 feature/富集组/LDA/p 值 0 失配 | 通过 |
| figure_types | 同时生成 LDA 效应量柱状图与分类层级树图 cladogram（PNG） | 5 个 artifact 含 lda_effect_size.png 与 cladogram.png；plot_lefse_lda 与 plot_lefse_cladogram 组合调用均返回 PNG | 通过 |
| composition_and_plots | format_lefse_input -> run_lefse_analysis -> plot_lefse_lda/plot_lefse_cladogram 可组合执行 | 组合调用成功：format 返回 2 artifacts；run 返回 1091 行 result_table；两个 plot 工具分别返回 PNG artifact | 通过 |
| prompt_and_resources | 至少一个 workflow prompt 与可读 resource，prompt 引用真实工具名 | prompt lefse_diff_feature_analysis 渲染成功并引用 format_lefse_input/run_lefse_analysis/plot_lefse_lda/plot_lefse_cladogram/run_full_lefse_workflow；resources lefse://method/README、input-format、output-format 均可读取且非空 | 通过 |

证据文件：
- reports/studio-quality.json
- reports/delivery-validation.json
- reports/expected-mcp-tools.json
- reports/mcp-acceptance-cases.json

仅描述本次记录的验证范围；协议可用不等于科学结果正确，发布不强制测试。

## 8. 已知限制与未验证事项

- artifact_content_only_via_returned_paths：交付私有环境的 .work/output 无草稿侧读权限，图/表内容以 MCP 工具返回的权威 artifact 路径为证据，未在评测端二次打开二进制校验
- svm_rank_limited：LEfSe 上游 test_svm 未实现（返回 None）；rank_technique='svm' 仅保留参数，MCP 验证只覆盖 lda 路径
- pvalue_output_contract：结果字段 kruskal_wallace_pvalue 来自上游KW p值（字段拼写沿用当前工具）；Wilcoxon筛选已执行，但没有输出逐比较Wilcoxon p值。不得把KW p值解释为Wilcoxon p值。
- scope_and_figures：数值一致性已在这一份官方示例上确认，不表示所有研究数据均已验证。默认图较拥挤、字体偏小，正式论文应调整尺寸与DPI。

## 9. MCP 资源与报告格式

- 中文说明资源：`paper2agent://delivery/report`
- 结构化资源：`paper2agent://delivery/report.json`
- 固定 schemaVersion：`1`；文件 `mcp-report.json` 与本 README 同源。

## 10. 许可与再分发

保留交付包内原有 LICENSE / NOTICE。源代码、测试数据、模型和论文材料可能适用不同许可，分发前分别核对。


本说明于任务完成后根据现有证据修订；原验收 ZIP 和运行环境保留其已验收版本。
