---
name: mcm-gold-t8-submit
description: 数学建模竞赛 T8 终检与提交专家。用于冻结内容后执行机器检查和清环境复现，闭环内置 Nature 的证据、图表、SourceModel、Office 回读与包级一致性，核对匿名、AI 使用详情、文件白名单和回执，并准备 H-005 人类授权。用户提到终检、匿名检查、打包、提交、复现、Office QA 或 T8 Gate 时使用。
---

# T8 终检与提交

先读[阶段交接契约](../mcm-gold/references/stage-contract.md)、[赛事规则](../mcm-gold/references/rules-2026.md)、[对抗门禁](../mcm-gold/references/adversarial-gates.md)、[内置 Nature 总则](../mcm-gold/references/nature-integrated-playbook.md)、[内置 Nature 写作与 Office 规范](../mcm-gold/references/nature-writing-office.md)和[人机责任边界](../mcm-gold/references/human-ai-charter.md)。最后 8 小时不引入新模型；最后 4 小时冻结内容，只修复交付、合规和会导致误读的问题。

## 必需输入

- T7 的提交候选、阅读版、文件哈希、打包白名单、H-004 和剩余风险。
- 支撑材料、复现说明、依赖、`run_all`、AI 使用详情和规则包。
- 比赛截止时间、平台覆盖规则与提交责任人。

## 执行

1. 冻结候选文件，生成实际目录清单和 SHA-256；不手写猜测包内文件。
2. 按规则执行机器检查并保存原始输出：页数、文件大小、页码、纸张、字体嵌入、损坏、正文匿名词、PDF 属性、Office 属性、代码路径用户名、图片 EXIF、压缩包层级和非法文件。
3. 逐项核对正文数字、图表、`RESULTS.md`、引用、目录、页码和支撑文件名。检查当前可交版本而非旧副本。
4. 把支撑包复制到新目录，解压后建立全新环境，严格按 README/复现说明运行 `run_all`；从实际输出核对关键数值、图和官方结果模板。
5. 检查代码没有依赖未打包的绝对路径、缓存、隐藏文件或私有数据；必要时只做可解释的低风险修复并重新全检。
6. 生成或核验《AI 工具使用详情》PDF；若确实未使用 AI，按规则生成未使用声明。内容与 `AI_USAGE.md` 一致。
7. 准备 H-005 简报：最终文件名和哈希、机器检查、清环境复现、AI 披露、剩余风险、提交与覆盖计划。
8. AI 不点击最终授权、不替人承担提交责任。由人确认 H-005 后执行平台操作并回读回执、下载文件、打开验证和哈希。
9. 截止前 2 小时完成首次保底提交；平台允许覆盖时最迟截止前 1 小时停止覆盖，每次覆盖后重新核验回执和下载文件。
10. 审计内置 Nature 闭环：`NATURE_QA.csv` 无未解释 DRAFT/BLOCKED，`SOURCE_DATA_MAP.csv` 的正文图/关键表均有真实路径和哈希，`MCM_SOURCE_MODEL.yaml` 与最终摘要/主图/限制一致。
11. 打开最终 SVG/PDF/PNG，检查最终尺寸、字体、重叠、裁剪、统计说明和 source data；不是只检查 T7 中间版本。
12. `paper_format=word` 或存在 PPTX 时，直接运行并读取 `officecli validate/view issues/view text`，同时做渲染预览；结构通过不等于视觉通过。
13. 检查引用无 metadata-only 支撑、期刊式数据声明没有虚构 DOI/仓储/许可、非必交 Nature 风格材料未混入提交白名单。

## 产物

- `T8_FINAL_CHECK.md`、`REVIEW_PASS_ITEMS.csv` 与所有检查原始日志。
- `deliverables/` 实际白名单、`MANIFEST.sha256` 和最终压缩包。
- `reproduction/clean-<id>/`：解压、安装、运行和核对日志。
- AI 披露文件、`T8_H005_BRIEF.md`、提交回执和下载复核记录。
- `NATURE_QA.csv` 终态、最终图表/Office 回读日志与 SourceModel 一致性记录。

## Gate

机器可检项全部读取实际输出；最终包在新目录和全新环境复现；内置 Nature 的证据、图表、SourceModel 和适用 Office QA 已闭环；匿名与元数据扫描通过；AI 披露与日志一致；文件名、大小、哈希和回执可回读；H-005 由人签署。任何一项缺证据不得写“全绿”。

平台、规则或环境造成重大阻碍时，不使用脆弱绕过；报告影响和可选降级，等待用户决定。收到真实评委/导师反馈后按[内置反馈闭环](../mcm-gold/references/nature-feedback.md)建立逐点修订，不伪造修改。把最终文件、哈希、检查、复现、H-005、回执和归档位置写入 `[HANDOFF T8]`。
