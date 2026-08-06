---
name: mcm-gold-t0-prepare
description: 数学建模竞赛 T0 赛前准备专家。用于核验最新赛事规则，固化 Python/R/LaTeX/Word 环境与内置 Nature 绘图/Office 能力，准备模板、匿名与 AI 披露基线，执行近年真题演练并验证 30 分钟最小可复现闭环。用户提到赛前准备、环境检查、工具链、模板、演练、规则包或 T0 Gate 时使用。
---

# T0 赛前准备

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[赛事规则](../mcm-gold/references/rules-2026.md)、[训练协议](../mcm-gold/references/training-protocol.md)和[内置 Nature 总则](../mcm-gold/references/nature-integrated-playbook.md)。本阶段只建立可靠起点，不提前替正式赛题选择路线。

## 必需输入

- 赛事名称、组别、起止时间、目标奖项和官方规则入口。
- 计划使用的语言、求解器、论文格式、联网条件与设备限制。
- 绝对 `result_root` 与 `state_dir`；缺失时先用总控初始化 `MCM-Result/` 七目录。

## 执行

1. 从官方来源重新核验规则、页数、文件大小、匿名、支撑材料、AI 披露和提交窗口。距查证日超过 30 天或规则已更新时，不沿用旧摘要。
2. 逐条重核[规则包](../mcm-gold/references/rules-2026.md)第一节标为 `URL_ONLY` 的事实——**比赛起止时间、报名截止、相似度红线、报送比例**在仓库内没有快照和哈希，且评阅规范仍是上一届版本。CONFIG 的 `start_time`/`end_time` 直接决定 74 小时状态机，核对后写 S-id 再固化；核不到就标 `UNCONFIRMED` 并阻断 live 模式，不得沿用本表默认值开钟。
3. **查证本赛区附加要求**：格式规范第八条允许"各赛区可以对论文做相应的要求"，官方无统一入口，须从本校教务或赛区组委会渠道获取。查到的附加要求写入 CONFIG 与终检清单并记 S-id；确认无附加要求时同样记录查证渠道与时间，不得默认"只有全国级规则"。
4. 运行共享的 [`env_check.sh`](../mcm-gold/templates/env_check.sh)，把实际输出保存到 `MCM-Result/Intermediate-Outputs/logs/`，并记录版本、缺包、字体、LaTeX、Office、求解器和联网能力。
5. 固定依赖、随机种子、编码、时区和字体；用最小依赖集而非临时堆包。缺工具时选择可维护降级路线并写 `RISKS.md`。
6. 准备论文骨架、图表样式、引用方式、代码入口和状态台账。使用 [`paper-templates.md`](../mcm-gold/templates/paper-templates.md)、[`workspace-templates.md`](../mcm-gold/templates/workspace-templates.md)与 [`run_all.py`](../mcm-gold/templates/run_all.py)。
7. 建立匿名基线扫描：作者字段、PDF 元数据、代码路径、图片 EXIF、工作簿属性和压缩包文件名。
8. 选最近三年中的至少一道历年题做 rehearsal。先冻结题面和输入，再记录真实墙钟；读取同题讲评或展示论文前结束 holdout。
9. 在 30 分钟时间盒内完成“读数据 -> 最小模型 -> 结果图 -> PDF -> 支撑包重跑”的烟雾测试。烟雾测试 MUST 在**全新目录 + 全新虚拟环境**下按支撑包 README 原文执行，验证的是"评委照说明能跑通"，不是"我们自己的机器能跑通"。
10. 固化内置 Nature 工具链：确认 Python/R 绘图运行时、SVG/PDF 可编辑文本、字体回退、最终尺寸预览和矢量回读；`paper_format=word` 时同时实测 `officecli validate/view`。
11. 不在 T0 替用户选择绘图后端。已有明确单语言工作流时记录；否则标 `UNCONFIRMED`，留到第一张正文图前只问“Python 还是 R？”。

## 产物

- `MCM-Result/Review-Results/T0_READINESS.md`：规则查证、工具版本、缺口、降级路线与负责人。
- `MCM-Result/Intermediate-Outputs/logs/env_check_<timestamp>.txt`：环境检查原始输出。
- `MCM-Result/Data-Scripts/environment/`：依赖锁定、版本清单和安装说明。
- `MCM-Result/Intermediate-Outputs/smoke/`：最小闭环的中间结果与重跑日志；代码、图和 PDF 分别归入对应固定目录。
- `MCM-Result/Intermediate-Outputs/REHEARSAL_RECORD.md`：题目、污染边界、真实耗时、失败与时间盒校准。
- `MCM-Result/Review-Results/T0_NATURE_READINESS.md`：绘图后端状态、矢量导出、字体、Office 回读和降级路线。

每个外部规则事实写 S-id，每个实际 smoke 结果写 R-id。不要把“命令存在”当作“已运行”。

## Gate

仅在以下条件全部满足时返回 `PASS`：

- 规则包来自当前官方页面并记录查证时间；第一节 `URL_ONLY` 事实（尤其比赛起止时间）已逐条重核并写 S-id。
- **本赛区附加要求已查证**（有则登记并进终检清单，无则记录查证渠道与时间）。
- 30 分钟内从干净起点生成可打开 PDF，关键数值能从 `run_all` 重跑。
- 中文字体、论文编译、求解器、匿名扫描和 AI 披露路径均有实际测试。
- 内置 Nature 的绘图/导出/Office 适用能力已实测或明确标为 N/A/UNCONFIRMED，不假设可用。
- 当前缺口有明确、低脆弱性的降级方案。

未联网时设置 `research.online=false` 并返回限制；不得编造规则或来源。把 T1 所需题面入口、工具限制和剩余风险写入 `[HANDOFF T0]`。
