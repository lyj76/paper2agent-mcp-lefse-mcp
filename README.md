# LEfSe 差异微生物特征分析 MCP（Paper2MCP 转换）

基于 LEfSe 分析不同组别间的差异微生物特征，返回差异特征结果表（特征名、分类层级、富集组、统计检验 p 值与 LDA 效应量）并生成 LDA 效应量柱状图与分层进化树图（cladogram）

## 1. 用途与适用范围

核心任务：基于 LEfSe 分析不同组别间的差异微生物特征，返回差异特征结果表（特征名、分类层级、富集组、统计检验 p 值与 LDA 效应量）并生成 LDA 效应量柱状图与分层进化树图（cladogram）

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

| `format_lefse_input` | Convert an abundance matrix with group metadata rows into the LEfSe input format. Abundance matrix (with class/subclass/subject rows) -> formatted LEfSe input file and plain-text table. | input_path, output_dir, class_row, subclass_row, subject_row, normalization, features_dir |

| `plot_lefse_cladogram` | Visualize LEfSe biomarkers on their hierarchical taxonomy tree as a cladogram. LEfSe result table (.res) -> cladogram image. | result_path, output_dir, format, dpi, title |

| `plot_lefse_lda` | Visualize LEfSe LDA effect-size scores as a bar chart. LEfSe result table (.res) -> LDA effect-size bar chart image. | result_path, output_dir, format, dpi, title, orientation, feature_font_size |

| `run_full_lefse_workflow` | Run the complete LEfSe differential-feature workflow (format, analyze, plot). Abundance matrix with group rows -> result table, LDA effect-size chart and cladogram. | input_path, output_dir, class_row, subclass_row, subject_row, normalization, anova_alpha, wilcoxon_alpha, lda_threshold, n_bootstrap, bootstrap_fraction, min_samples_per_subclass, multiclass_strategy, plot_format, timeout_seconds |

| `run_lefse_analysis` | Run LEfSe Kruskal-Wallis, Wilcoxon and LDA effect-size analysis. Formatted LEfSe input (.in) -> differential feature result table (.res) plus parsed records. | input_path, output_dir, anova_alpha, wilcoxon_alpha, lda_threshold, n_bootstrap, bootstrap_fraction, min_samples_per_subclass, multiclass_strategy, rank_technique, run_wilcoxon, timeout_seconds |

完整输入/输出 Schema 见 `mcp-report.json`；实际服务的 tools/list 是调用依据。

预期输出：
- 差异特征结果表（含特征名、分类层级、富集组别、Kruskal-Wallis/Wilcoxon p 值、LDA 效应量）
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

```bash
pixi install --locked --manifest-path pixi.toml
pixi run --manifest-path pixi.toml -e server python server.py
```

在仓库根目录运行，依赖版本以 pixi.lock 为准；每个环境的用途和依赖探测见 paper2agent-mcp.json。Paper2Quest 安装时分配专属 UID、HOME、TMP 与缓存；本地 Pixi 命令本身不提供安全沙箱。

## 5. 输入、输出与工作流

实际评测问题：基于 LEfSe，分析不同组别间的差异微生物特征。输入为微生物丰度表和样本分组信息，可选提供亚组及受试者信息。输出差异特征结果表，包含特征名称、所属分类层级、富集组别、统计检验结果和 LDA 效应量，并生成 LDA 效应量柱状图及分类层级树图（cladogram）。支持配置显著性阈值、LDA 阈值和归一化参数。保留原始结果、参数、依赖版本及中文分析说明。使用官方小规模示例验证 MCP 与原 LEfSe 程序结果的一致性，优先采用 CPU 运行。

实际调用的工具：
- 未记录

复现步骤：
- 未记录

产物路径（相对项目目录）：
- 未记录

## 6. 测试数据与复现条件

未记录结构化测试数据来源、版本和许可；不能据此声称任意数据均可复现。

环境记录：
```json
{}
```

未记录的版本、参数和随机种子须在复现时补齐。

## 7. 验证结果与参考对比

验证层级：**记录的工具调用通过**

参考实现/教程：未记录

| 验收项目 | 预期 | 实测 | 记录结果 |
| --- | --- | --- | --- |

| 未记录 | 未记录 | 未记录 | 不作通过声明 |

平台记录的严格工具调用：
- reports/mcp-project-environment.json；私有环境 jobenv-31083348e13108ffb8620d7108bd1930bc02624c；验证编号 ba223523adac464e9f624eae441d0a13
- reports/mcp-clean-environment.json；私有环境 jobenv-7189f53d70126ea2fb048408a99276ccdd7e29c2；验证编号 daf16d22e0bd4131ad71ec7f77efe5ce

证据文件：
- reports/mcp-project-environment.json
- reports/mcp-clean-environment.json

两份报告对应同一源码在两个独立私有环境的严格工具调用；不代表独立科学复现、最终发布包重建或报告资源读取已通过。

## 8. 已知限制与未验证事项

未记录额外限制；这不表示不存在限制。请按上面的验证层级判断可用范围。

## 9. MCP 资源与报告格式

- 中文说明资源：`paper2agent://delivery/report`
- 结构化资源：`paper2agent://delivery/report.json`
- 固定 schemaVersion：`1`；文件 `mcp-report.json` 与本 README 同源。

文档文件已生成；上述资源 URI 尚未通过 resources/list 与读取验证，不能据此认定服务已经暴露报告资源。

## 10. 许可与再分发

保留交付包内原有 LICENSE / NOTICE。源代码、测试数据、模型和论文材料可能适用不同许可，分发前分别核对。
