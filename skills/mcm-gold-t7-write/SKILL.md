---
name: mcm-gold-t7-write
description: 数学建模竞赛 T7 论文与图表专家。内置 Nature SourceModel、论证架构、figure contract、支撑分级、语言边界和 Office 规格，用于组织逐问叙事，确保正文/图表/RESULTS 一致，写出含数值与边界的摘要，并生成提交版和阅读版供 H-004 确认。用户提到建模论文、摘要、图表、DOCX/PPTX、写作或 T7 Gate 时使用。
---

# T7 论文与图表

**安装依赖**：本 skill 与 `mcm-gold` **必须同级安装**（`skills/mcm-gold/` 与 `skills/mcm-gold-t0-prepare/` … `skills/mcm-gold-t8-submit/` 并列在同一目录）。下文全部 `../mcm-gold/…` 的必读文档、模板脚本与 Gate 引用都按这个布局解析：只装本阶段、或改动目录层级时，这些链接会一次性全断，必读门禁与机检随之全部失效。缺同级 `mcm-gold` 时先补齐再执行，不要绕过引用继续跑。

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[写作与评分](../mcm-gold/references/rubric-and-writing.md)、[可引用书目](../mcm-gold/references/literature-library.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)、[内置 Nature 科学图表规范](../mcm-gold/references/nature-figures.md)、[内置 Nature 写作与 Office 规范](../mcm-gold/references/nature-writing-office.md)和[论文模板](../mcm-gold/templates/paper-templates.md)。从 T4 起滚动写作，不把写作留到最后。

## 必需输入

- T1 逐问字面工件，T2 冻结定义与来源，T4/T5 结果与基线。
- T6 的确认、受限、否决主张及可用表述边界。
- `MCM-Result/Intermediate-Outputs/RESULTS.md`、`MCM-Result/Reference-Papers/SOURCES.md`、`MCM-Result/Intermediate-Outputs/RISKS.md`、claim/figure 台账、规则包和当前论文。
- T1 的逐问接口清单与 T6 的 K-id、检验结论；缺上游证据时相应覆盖项只能标 `WEAK/MISSING`，不得用文字补成通过。

## 执行

1. 先生成唯一 `MCM_SOURCE_MODEL.yaml`：工作类型、论证弧、中心交付、难点、路线、主张、关键证据、信任检验、创新、复用价值、限制和物理工件。只引用已有 C/R/S/F-id。
2. 冻结中心主张、证据层级、适用范围和限制。未经 T6 确认的结果不得进入摘要确定性结论。
3. 为每张主图完成 figure contract：核心结论、角色、archetype、面板、源表、脚本、视觉编码、统计、失败状态和 caption boundary。
4. 图表先行，再写正文。主证据为 hero，验证和控制视觉降级；最终尺寸核查读取真实 SVG/PDF/预览。**每次重画图或重导图源表，都要同步更新 `SOURCE_DATA_MAP.csv` 的哈希并重跑 [`verify_evidence_map.py`](../mcm-gold/templates/verify_evidence_map.py)**——这里是哈希过期的高发点：图改了、映射没改，映射表看着完整，指向的内容已经不是那一版了。
5. 按评委读者路径写：题目要求 -> 难点 -> 模型合理性 -> 结果 -> 信任证据 -> 创新 -> 边界。每个小问定位题意接口、数学定义、求解步骤、结果图/表、验证和解释边界。
6. 按[写作与评分](../mcm-gold/references/rubric-and-writing.md)的篇幅预算 target 列写作：阅读版正文 19–29 页、总汉字 ≥15000；每问建模求解 ≥1200 汉字、≥4 个编号公式、≥1 张结果表；摘要 600–850 字、≥8 处含单位数值、逐问段全覆盖；模型评价 230–450 字且每条优缺点带正文锚点（式号/图表号/专有名词）。每问落实“每问正文必备清单”（接口段 -> 编号公式定义 -> 算法步骤 -> 结果表五要素 -> 验证小节 -> 边界段）；简洁=每句有信息，低于 floor 的“简洁”按缺证据处理，不得为凑页数注水。
7. 检验形态三选一：独立成章、嵌入每问小节或并入模型评价章，形态自选但要素缺一即 `NEEDS_EXPANSION`；要素清单（误差分析数字句、≥2 类灵敏度各含扰动幅度+最大偏差+判定句、关键假设逐条回收、多次运行或基线对照、负结果保留）与判定标准见[写作与评分](../mcm-gold/references/rubric-and-writing.md)的“检验三种等价合规形态”。
8. 初始化 `PAPER_COVERAGE_LEDGER.csv`，每问固定 `interface/definition/algorithm/result/validation/boundary` 六行。先从 T1/T6 回填所需内容和 C/K/R/P/D-id（检验证据只有 `RESULTS.md` 的 R-id 与 `REVIEW_PASS_ITEMS.csv` 的 P-id 两个载体，不存在 V 系列编号）；完成实际 PDF 渲染后再回填可由 `pdftotext` 检索的 `paper_anchor`、`observed` 与状态。不得用目录标题、代码附录或支撑包路径冒充正文覆盖。
8b. **动任何润色之前，先留 before 快照**——`verify_prose_revision.py` 要 `--before/--after` 两个目录，原地润色后 before 就不存在了，这道被 Gate 点名的机检会物理上无法补做。快照落 `Intermediate-Outputs/`（它是过程中间件，不进 `Paper-Outputs/`）：

    ```bash
    snap="MCM-Result/Intermediate-Outputs/prose-revision/before-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$snap" && cp MCM-Result/Paper-Outputs/paper/*.tex "$snap"/
    ```

    时间戳用 `date` 取，不手写。Word 路线先把正文导成纯文本（`officecli view text`）存进快照目录，比对时传 `--pattern '*.txt'`；脚本按同名文件配对，快照里的文件名必须与润色后的一致。每轮润色各留一份快照，不要覆盖上一轮——多轮改写时只留最后一份，等于只查了最后一轮。
9. 先修 `work_type -> section role -> paragraph logic -> claim/evidence/boundary`，最后润色句子。不得用流畅语言隐藏证据缺口或让 AI 新造核心论证。**凡用 AI 做过润色、降重或"拟人化"改写，必须跑 [`verify_prose_revision.py`](../mcm-gold/templates/verify_prose_revision.py) 比对修订前后并读实际输出**（`--before` 取步骤 8b 的快照目录，`--after` 取当前 `MCM-Result/Paper-Outputs/paper/`，`--out MCM-Result/Review-Results/T7_PROSE_REVISION.json`），不得凭"只是改了措辞"推定安全。2025D 实测一轮 60 段 AI 改写：范围号 `$15$--$198$ \si{m}`（15 到 198 米）被改成 `$15$:$198$`（读作 15 比 198）共 5 处，数字与 LaTeX 结构都没变、段落级的占位符/数字/语言/长度四道闸一道没响；确定结论被"可能"弱化 5 处；明令禁止的模板连接词净增 18 次；句长标准差 20.4 → 17.8——**以"降 AI 率"为目的的改写，实测把 AI 味改重了**。数字守恒是这一步的最低门槛而不是充分条件，润色也不可假定为改进。
10. 模型假设说明依据与影响；创新点用同预算基线收益表达；失败或不确定性放在结果附近，不埋在结尾。
11. 凡把模型输出用于新场景/新数据的结论，正文 MUST 给出支撑域比例与被拒绝的外推部分，并写明对域外样本不给结论的理由。诚实标注拒答范围比给出一个域外的漂亮数字更容易得分——后者评委一核对分布就会当场质疑。
12. 摘要最后写成微型论文：问题/难点、路线、每问具体数值、信任证据、创新和关键边界。所有数字从 R-id 回读。
13. 逐项核对正文数字 = 图表数字 = `RESULTS.md` 数字，claim 的引用与 `SOURCES.md` 支撑等级对齐，metadata-only 不进入正文。
14. **`PAPER_COVERAGE_LEDGER.csv` 的 `paper_anchor` 必须全文唯一且不含数学符号**。契约按锚点切分每问区间再统计字数与编号公式：锚点用「任务接口」「解释边界」这类各章都有的小节名时，区间会串到别章，实测出现「某问报 11 式而实际 3 式、另一问报 0 式而实际 8 式」；锚点写成 `$\hat T_i$` 一类数学式会直接 `ANCHOR_NOT_FOUND`，因为契约回读的是 PDF 渲染后的文本。锚点取该问独有的一句话前半段最稳。
15. 参考文献逐条取自 [`literature-library.md`](../mcm-gold/references/literature-library.md)、前沿卡源列或 `SOURCES.md` 中实际核验过的条目；**禁止凭印象补写卷期页**。环境缺 `bibtex/natbib` 时手写 `thebibliography`，每条著录完成后用 `https://doi.org/<DOI>` 或本地全文实核一次——编造文献按反幻觉铁律视为造假。
16. `paper_format=word` 时，从 SourceModel 建 DocumentSpec，并直接用 `officecli` 生成和回读实际 DOCX；LaTeX 主线不绕到 Office。题面要求 PPTX 时从同一 SourceModel 建 SlideSpec 和实际 PPTX，不停在大纲。
17. 论文正文不出现训练状态、内部 H/R 编号、责任边界、支撑清单或不可提交横幅；这些只留在论文外工作区。
18. 在参考文献之前设置 2026 版“AI 工具使用声明”，从实际 `AI_USAGE.md` 二选一回填原文。使用 AI 时生成 `AI 工具使用详情.pdf` 并逐项回读工具名称/版本或型号、用途环节、提示与过程、采纳/人工修改/核验及核心建模与分析的队员主导证据；不把 AI 工具列入参考文献，不沿用 2025 版正文逐处标注旧模板。
19. LaTeX 路线只维护一个 `MCM-Result/Paper-Outputs/paper/body.tex` 科学正文源；`main.tex` 只引入正文，`*_submission.tex` 引入同一正文后追加由最终支撑目录实际遍历生成的文件列表与全部 `\lstinputlisting` 源程序。Word 路线也必须从同一 DocumentSpec 生成两版并做正文回读比对。
20. 逐行填写固定七维 `T7_RUBRIC_REVIEW.csv`。总分低于 `CONFIG.target.rubric_threshold` 或任一单项低于及格线时，修复实质缺口并让论文契约返回 `NEEDS_EXPANSION`；T7 阶段不得 `PASS/PASS_WITH_LIMITATIONS`，不能以自创评分表绕过。
21. 对最终阅读版、提交版、覆盖账本、rubric 和实际支撑/源程序目录运行 [`../mcm-gold/templates/verify_paper_contract.py`](../mcm-gold/templates/verify_paper_contract.py)，保存到 `MCM-Result/Review-Results/T7_PAPER_CONTRACT.json`。**带 `--results-ledger MCM-Result/Intermediate-Outputs/RESULTS.md`**，核验每条 R-id 的数值确实进了论文——终检清单的「正文数字 = RESULTS.md」此前全靠人工比对，台账登记了结果而论文里查无此数，说明两者已脱节。契约错误必须修复；`NEEDS_EXPANSION` 必须按 expansion_items 逐条实质扩写（补齐每问正文、编号公式、结果表或摘要、模型评价密度）并重跑契约直至通过，不得只调阈值或用文字掩饰缺口；阅读版触线（<14 页或 <10000 字）时以形态检查为准，形态项缺失即 `NEEDS_EXPANSION`，全过则契约记录 `DEPTH_FORM_CHECKS_PASSED` 豁免留痕，不按页数填充。
22. H-004 必须阅读实际 `main.pdf`，逐问确认解释、结果、主图、验证和边界；契约已记录 `DEPTH_FORM_CHECKS_PASSED` 豁免时 H-004 仍须人工复核表达层，不得以机检豁免替代人工阅读。演练只能把覆盖行写成 `PROXY_REHEARSAL`，最终状态不得冒充正式 `PASS`。

## 产物

- `MCM-Result/Paper-Outputs/paper/main.*` 与 `paper/main.pdf` 阅读审查版。
- `MCM-Result/Paper-Outputs/paper/*_submission.*` 与明确打包白名单。
- `MCM-Result/Review-Results/PAPER_COVERAGE_LEDGER.csv`、`T7_RUBRIC_REVIEW.csv` 与 `T7_PAPER_CONTRACT.json`。
- `MCM-Result/Intermediate-Outputs/MCM_SOURCE_MODEL.yaml`；Word/PPT 路线的 DocumentSpec/SlideSpec 放同处，实际 Office 文件放 `Paper-Outputs/`，QA 放 `Review-Results/`。
- `MCM-Result/Review-Results/T7_FIGURE_CONTRACTS.md` 与视觉核查记录；源表和图表放 `Data-Figures/`。
- 从覆盖账本派生的 `MCM-Result/Review-Results/T7_ARGUMENT_AUDIT.md`、`NATURE_QA.csv`；`SOURCE_DATA_MAP.csv` 放 `Intermediate-Outputs/`。
- 更新后的 claim 台账放 `Intermediate-Outputs/`，figure review 台账放 `Review-Results/`。
- `MCM-Result/Review-Results/T7_H004_BRIEF.md`：结果解释、摘要结论、主图和剩余风险。
- 正文经 AI 润色/改写时：`MCM-Result/Intermediate-Outputs/prose-revision/before-<timestamp>/`（步骤 8b 的润色前快照，每轮一份）与 `MCM-Result/Review-Results/T7_PROSE_REVISION.json`（`verify_prose_revision.py` 的输出），并在 `AI_USAGE.md` 登记该环节的模型、提示与人工核验。

## 独立 Review

冻结 T7 产物后，必须由两名独立 reviewer 盲审。专属 70 分只从已校验的固定七维 `T7_RUBRIC_REVIEW.csv` 按 0.7 折算，不另造重复评分表；同时核验 `T7-G1` 至 `T7-G6`。R1/R2 逐项取低生成 FINAL，原 rubric 阈值、paper contract 和 H-004 均不得被总分覆盖。

## Gate

SourceModel、claim/figure/source-data 台账与论文一致；全文数字可追溯；摘要有具体数值和边界；`PAPER_COVERAGE_LEDGER.csv` 每问六项无 `WEAK/MISSING` 且锚点能在实际阅读版检索，validation 与主要 K-id 和检验证据闭环；图表经真实渲染核查；引用可访问且支撑等级足够，每条参考文献可追到书目库、前沿卡源列或已核验 S-id；2026 版 AI 声明位于参考文献之前且与过程记录一致；适用 Office 文件经 `officecli validate/view` 回读；两版共享科学正文且提交版确含实际文件列表和完整源程序；固定七维 rubric 总分达到目标且无单项低于及格线；**正文若经 AI 润色或改写，`T7_PROSE_REVISION.json` 无 error，warning 逐条看过并记录采纳与否**——不得以"只改了措辞"跳过这一项。live 模式的 `T7_PAPER_CONTRACT.json` 必须为 `PASS` 且由人完成 H-004，否则阶段返回 `NEEDS_HUMAN` 或 `BLOCKED`；无人演练契约上限为 `PROXY_REHEARSAL`，只能以非正式演练状态交接。

把最终主张、论文文件哈希、主图状态、H-004、剩余表达风险和 T8 打包白名单写入 `[HANDOFF T7]`。
