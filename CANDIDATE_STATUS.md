# V2.6 行文规范候选

状态：`CANDIDATE_NOT_LIVE`。

本候选基于 live `v2.4-paper-closure`（MCM-For-GOLD 仓库 HEAD `d1ffffd`），给论文契约增加"行文深度"机检与写作侧正向预算。它当前只位于训练候选区，没有同步到 `/home/user/.codex/skills/mcm-gold*`，也没有发布到公共仓库。唯一设计依据是 `mcm-gold-training/research/writing-norms-2026-08-06/SPEC.md`。

## 解决的问题

2025B 试运行（`MCM-Result/.../2025-full-rehearsal-v1`）阅读版正文仅 7 页/约 4320 汉字、每问建模求解 500–800 字、模型评价 221 字，但全部 Gate 放行（rubric 91/100，契约 PROXY_REHEARSAL）。根因：页数只产生诊断而没有后续，六项覆盖只查"可定位"不查"成段成表"，写作侧只有负向约束没有正向预算。异常信号（过薄）没有闭环。

## 设计

- **触发线闭环**：阅读版 <14 页或正文 <10000 汉字即自动执行深度形态核查；缺项写入 `expansion_items`（`NEEDS_EXPANSION`，退出码 2）；形态全过则记 `DEPTH_FORM_CHECKS_PASSED` 机检豁免（warning）后放行。页数本身仍不单独判失败，禁止为凑页数注水。
- **形态核查**（`templates/verify_paper_contract.py`）：每问区间 ≥800 汉字且 ≥1 编号式（`QUESTION_PROSE_FLOOR`/`QUESTION_EQUATION_FLOOR`）、全文 ≥3 表（`RESULT_TABLE_FLOOR`）、参考文献 ≥3 条（`REFERENCE_FLOOR`）随触发线执行；摘要 ≥550 字且 ≥4 处含单位数值（`ABSTRACT_DENSITY`）、模型评价 ≥200 字（`EVALUATION_FLOOR`）常开。区间由覆盖账本 `paper_anchor` 定位，定位失败只发 `SPAN_UNAVAILABLE` 降级，不伪造通过。报告新增 `depth_metrics`。
- **写作预算**（`references/rubric-and-writing.md`）：页数分配段改写为"篇幅预算（实测国一区间）"，新增每问正文必备清单与检验三种等价合规形态；rubric 满分证据列加深度措辞，分值结构不动。
- **评审锚点与写作指令**（`references/stage-review-scoring.md`、`mcm-gold-t7-write/SKILL.md`）：触线且无豁免时 `模型建立`/`求解与结果正确性` 两维封顶 `VERIFIED_LIMITED`；T7 REPORT 强制含"每问实测页数/汉字数与预算对比"小节；`NEEDS_EXPANSION` 必须实质扩写后重跑契约。

## 当前证据

- 调研笔记（`mcm-gold-training/research/writing-norms-2026-08-06/`）：`structure-and-budget.md`（5 篇国一结构实测）、`model-section-depth.md`（3 篇国一每问深度）、`judging-criteria.md`（官方按完成度给分）、`results-validation.md`（检验要素）、`abstract-analysis-evaluation.md`（摘要/评价实测）、`mcm-outstanding.md`（美赛仅作量级旁证）。门槛数值全部出自 SPEC §1 总表。
- 设计规格：同目录 `SPEC.md`。
- 单元回归：`tests/test_paper_contract.py` 16 项全绿——健康合成论文（每问 ≥800 字/≥1 式、3 表、摘要 680 字、评价 235 字、3 条文献、全文 13132 字）PASS；11 页简洁但完整论文只 warning（`DEPTH_FORM_CHECKS_PASSED` + `DEPTH_REVIEW_REQUIRED`）仍 PASS；薄文夹具被 `QUESTION_PROSE_FLOOR`/`QUESTION_EQUATION_FLOOR`/`RESULT_TABLE_FLOOR`/`REFERENCE_FLOOR` 阻断为 `NEEDS_EXPANSION`；既有错误/警告/expansion 三分语义无回归。
- post-hoc 负对照：`mcm-gold-training/validation/2025B-writing-norms-posthoc/`。冻结 2025B 工件重跑，双触发（7 页 <14、2945 字 <10000），状态 `NEEDS_EXPANSION`，含 Q1/Q2/Q3 `QUESTION_PROSE_FLOOR`（290/550/785 字）、`ABSTRACT_DENSITY`（469 字）、`RESULT_TABLE_FLOOR`（2 表）；errors 为空，rubric 与 PROXY_REHEARSAL 状态不变，冻结件未被修改。

这些只是结构回归与已知题 post-hoc，不是新问题 forward 验证。当前不得标 live。

## 验证债（SPEC §7.3）

1. **缺正对照**：尚无一篇形态检查全过的健康论文走完整契约（当前正对照只有合成夹具）。
2. **摘要/评价定位未在 Word 路线验证**：自动定位依赖"摘要/关键词/模型的评价/参考文献"标记，目前只在 LaTeX→pdftotext 路线实测。
3. **门槛数值未交叉核验**：floor/target 来自 5+3 篇自报获奖论文的实测区间，未与官方获奖名单交叉核验。

## 晋级 Gate

按仓库惯例（`training-protocol.md`），这是 Gate/契约与写作指令变更，至少需要：

1. 一个 discovery 运行和一个不同家族 validation，覆盖至少两个数学家族；
2. 一次健康论文正对照：深度形态检查全部达标时契约不误报 `NEEDS_EXPANSION`；
3. 三条验证债全部清零或有明确结论；
4. H-004 人工审查确认 expansion items 对应真实评审丢分点，且没有诱发凑字注水；
5. 与未晋升的 `v2.5-guided-decisions-candidate` 人工合并（两者同改 `stage-review-scoring.md` 与 `mcm-gold-t7-write/SKILL.md`）。

若机检诱发注水、误拦正常简洁论文、摘要/评价定位在真实路线频繁失败，或门槛数值被交叉核验证伪，则回滚本候选，不晋升。
