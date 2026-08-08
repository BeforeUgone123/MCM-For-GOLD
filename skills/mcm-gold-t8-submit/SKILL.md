---
name: mcm-gold-t8-submit
description: 数学建模竞赛 T8 终检与提交专家。用于冻结内容后执行机器检查和清环境复现，闭环内置 Nature 的证据、图表、SourceModel、Office 回读与包级一致性，核对匿名、AI 使用详情、文件白名单和回执，并准备 H-005 人类授权。用户提到终检、匿名检查、打包、提交、复现、Office QA 或 T8 Gate 时使用。
---

# T8 终检与提交

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[赛事规则](../mcm-gold/references/rules-2026.md)、[对抗门禁](../mcm-gold/references/adversarial-gates.md)、[内置 Nature 总则](../mcm-gold/references/nature-integrated-playbook.md)、[内置 Nature 写作与 Office 规范](../mcm-gold/references/nature-writing-office.md)和[人机责任边界](../mcm-gold/references/human-ai-charter.md)。最后 8 小时不引入新模型；最后 4 小时冻结内容，只修复交付、合规和会导致误读的问题。

## 必需输入

- T7 的显式 `*_submission.pdf`、`main.pdf`、`PAPER_COVERAGE_LEDGER.csv`、`T7_RUBRIC_REVIEW.csv`、`T7_PAPER_CONTRACT.json`、文件哈希、打包白名单、H-004 和剩余风险。
- 支撑材料、复现说明、依赖、`run_all`、AI 使用详情和规则包。
- 比赛截止时间、平台覆盖规则与提交责任人。

## 执行

1. 冻结候选文件，生成实际目录清单和 SHA-256；不手写猜测包内文件。提交白名单只能指向显式 `*_submission.pdf`，禁止把 `main.pdf` 重命名后当提交版。
2. **先建交付物分层再终检**：运行 [`../mcm-gold/templates/build_deliverables.py`](../mcm-gold/templates/build_deliverables.py) 生成 `deliverables/{submission,staging/support,print,archive}`，保存清单到 `MCM-Result/Review-Results/T8_DELIVERABLES.json`。**不得跳过这一步直接终检**——契约的 `--support-root`/`--source-root` 指向 staging 路径，路径不存在时逐文件列表核对与源码嵌入核对**整组静默跳过**，报告只剩一条 `MISSING_SUPPORT_ROOT`，极易被读成「支撑包已通过终检」。2025A 演练正是如此漏掉了一个论文完全没提到的源文件和四份未嵌入附录的代码。

3. 对冻结后的阅读版、提交版、覆盖账本、七维 rubric 和实际支撑/源程序目录重新运行 [`../mcm-gold/templates/verify_paper_contract.py`](../mcm-gold/templates/verify_paper_contract.py)，保存到 `MCM-Result/Review-Results/T8_PAPER_CONTRACT.json`。缺提交版、共享正文漂移、文件列表不实、代码未嵌入、覆盖缺项或 rubric 未达目标均阻断打包；T8 不得覆盖 T7 状态。
4. 按规则执行机器检查并保存原始输出：页数、文件大小、页码、纸张、字体嵌入、损坏、正文匿名词、PDF 属性、Office 属性、代码路径用户名、图片 EXIF、压缩包层级和非法文件。
5. 逐项核对正文数字、图表、`RESULTS.md`、引用、目录、页码和支撑文件名。检查当前可交版本而非旧副本。
6. 把支撑包复制到新目录，解压后建立全新环境，严格按 README/复现说明运行 `run_all`，**必须带 `--expect-problems <论文实际问数>`**；从实际输出核对关键数值、图和官方结果模板。不带该参数时 `--all` 只校验入口编号连续，防不住「整体少一问」——实测事故：支撑包 `src/` 下只有 `p1.py` 而 README 与附录都写 `p1.py…p5.py`，评委执行 `--all` 9.6 秒后看到 `[DONE]` 会认为五问全部复现，实际只跑了 1/5。核对 `[PLAN]`/`[DONE]` 行打印的问数与论文一致，不能只看有没有报错。**这一步对应格式规范第五条的取消资格红线**（缺源程序、程序不能运行、运行结果与论文不符），不是内部质量偏好：跑不通或对不上就是资格风险，必须修到通过或如实降级论文结论，不得跳过。
7. **逐条核验三条取消资格红线并留证**：① 附录代码 = 支撑包代码 = 清环境实跑通过（留完整日志）。三个等号各有专属机检，缺一不可：`build_deliverables.py --code-src` 管「支撑包 = 工作区」，`verify_clean_reproduction.py` 管「实跑通过」，`verify_paper_contract.py` 的 `APPENDIX_CODE_STALE` 管「附录 = 工作区」。**前两个全绿不蕴含第三个**——PDF 是快照而代码是活的，改完源码只重打包不重编论文，前两项照样全绿，而评委拿到的论文附录印着旧代码。2025C 实测就是这样漏过去的；② 清环境重跑的关键数值逐项等于论文/图表/`RESULTS.md`（留比对表，差异必须追根因，禁止改论文数字凑答案）；③ 支撑包与提交论文同版本冻结、哈希一致，未混入旧副本（格式规范第十一条：支撑材料与论文内容不相符可能被取消评奖资格）。
8. **核验本赛区附加要求**：读取 T0 登记的赛区要求逐条比对；T0 未登记时在此阻断并要求补查，不得默认只有全国级规则（格式规范第八条允许赛区另提要求）。
9. 检查代码没有依赖未打包的绝对路径、缓存、隐藏文件或私有数据；必要时只做可解释的低风险修复并重新全检。
9b. 跑 `verify_output_layout.py --workspace MCM-Result --write-index`：校验布局纪律（缓存与构建产物不得留在源码/交付目录、无第八个一级目录、论文已产出则结果台账必须在工作区内），并刷新工作区根的 `README.md` review 入口。**留到最后再刷新**，索引记录的是终态。
10. 在参考文献之前生成或核验 2026 版“AI 工具使用声明”。已使用 AI 时，支撑材料必须含文件名完全一致的 `AI 工具使用详情.pdf`，并从 `AI_USAGE.md` 回读名称/版本或型号、用途环节、提示与过程、采纳/人工修改/核验；同时核对核心建模与分析的队员主导证据。未使用声明必须与过程档案一致。
11. 核验 `MCM-Result/Reference-Papers/SEARCH_LOG.md` 无禁入域名采用记录；误命中已登记并弃用（参赛规则第 5 条把"浏览"本身列为严重违纪）。
12. 准备 H-005 简报：最终文件名和哈希、论文契约、机器检查、清环境复现、三条红线留证、赛区要求、AI 披露、剩余风险、提交与覆盖计划。
13. AI 不点击最终授权、不替人承担提交责任。由人确认 H-005 后执行平台操作并回读回执、下载文件、打开验证和哈希。
14. 截止前 2 小时完成首次保底提交；平台允许覆盖时最迟截止前 1 小时停止覆盖，每次覆盖后重新核验回执和下载文件。
15. 审计内置 Nature 闭环：`NATURE_QA.csv` 无未解释 DRAFT/BLOCKED，`SOURCE_DATA_MAP.csv` 的正文图/关键表均有真实路径和哈希，`MCM_SOURCE_MODEL.yaml` 与最终摘要/主图/限制一致。
16. 打开最终 SVG/PDF/PNG，检查最终尺寸、字体、重叠、裁剪、统计说明和 source data；不是只检查 T7 中间版本。
17. `paper_format=word` 或存在 PPTX 时，直接运行并读取 `officecli validate/view issues/view text`，同时做渲染预览；结构通过不等于视觉通过。
18. 检查引用无 metadata-only 支撑、期刊式数据声明没有虚构 DOI/仓储/许可、非必交 Nature 风格材料未混入提交白名单。

## 产物

- `MCM-Result/Review-Results/T8_FINAL_CHECK.md`、`REVIEW_PASS_ITEMS.csv`；所有检查原始日志放 `Intermediate-Outputs/logs/`。
- `MCM-Result/Review-Results/T8_PAPER_CONTRACT.json`，其输入路径和哈希必须指向冻结后的最终文件。
- `MCM-Result/Paper-Outputs/deliverables/` 按 `submission/staging/print/archive` 四层分好，含实际白名单、`MANIFEST.sha256` 和最终压缩包。
- `MCM-Result/Review-Results/T8_DELIVERABLES.json`：`build_deliverables.py` 的清单与大小校验输出。
- `MCM-Result/Review-Results/T8_OUTPUT_LAYOUT.json` 与工作区根的 `README.md`：布局校验结果与人类 review 导航入口（`verify_output_layout.py` 生成，不得手改）。
- `MCM-Result/Intermediate-Outputs/reproduction/clean-<id>/`：解压、安装、运行和核对日志。
- AI 披露文件、提交回执和下载复核记录放 `Paper-Outputs/`；`T8_H005_BRIEF.md` 放 `Review-Results/`。
- `MCM-Result/Review-Results/NATURE_QA.csv` 终态、最终图表/Office 回读结果与 SourceModel 一致性记录；原始回读日志放 `Intermediate-Outputs/logs/`。

## 独立 Review

冻结 T8 候选包后，必须由两名独立 reviewer 盲审，按通用 30 分与 T8 专属 70 分核验 `T8-G1` 至 `T8-G7`。`pre_submit` 只能形成待 H-005 的 `NEEDS_HUMAN`；真实提交后必须以 `post_submit` 新 run 回读回执和下载哈希，才能生成最终结论。

## Gate

机器可检项全部读取实际输出；live 模式的 `T8_PAPER_CONTRACT.json` 对最终文件为 `PASS`，演练可为 `PROXY_REHEARSAL` 但不得称为正式可提交；逐问覆盖、固定七维 rubric、两版共享正文、实际文件列表与完整源程序均闭环；提交白名单包含显式 `*_submission.pdf` 且不含 `main.pdf`；最终包在新目录和全新环境复现；**三条取消资格红线（源程序可运行、运行结果与论文一致、支撑材料与论文相符）各有实测证据**，其中「附录代码 = 支撑包代码」必须由 `APPENDIX_CODE_STALE` 无命中来支撑，不得只凭 `code_check` 全绿推定；`T8_OUTPUT_LAYOUT.json` 为 `PASS` 且 `README.md` 索引为 `FRESH`；**赛区附加要求已核验**；内置 Nature 的证据、图表、SourceModel 和适用 Office QA 已闭环；匿名与元数据扫描通过；AI 披露与日志一致；检索日志无禁入域名采用记录；文件名、大小、哈希和回执可回读；H-005 由人签署。任何一项缺证据不得写“全绿”。

平台、规则或环境造成重大阻碍时，不使用脆弱绕过；报告影响和可选降级，等待用户决定。收到真实评委/导师反馈后按[内置反馈闭环](../mcm-gold/references/nature-feedback.md)建立逐点修订，不伪造修改。把最终文件、哈希、检查、复现、H-005、回执和归档位置写入 `[HANDOFF T8]`。
