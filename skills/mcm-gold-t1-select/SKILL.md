---
name: mcm-gold-t1-select
description: 数学建模竞赛 T1 读题与选题专家。用于逐句拆解题面动词、列出每问必须交付的物理工件、识别中心交付、主要证据与验证标准、建立可行性评分矩阵、反查最后一问可交结论，并形成可审计的定题建议与 H-001 裁决。用户提到读题、赛题分析、选 A/B/C 题、题目拆解或 T1 Gate 时使用。
---

# T1 读题与选题

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[人机责任边界](../mcm-gold/references/human-ai-charter.md)和[内置 Nature 总则](../mcm-gold/references/nature-integrated-playbook.md)。本阶段优化的是“能否完整、可验证地答题”，不是方法名的新颖程度。

## 必需输入

- 候选题原文、附件清单、官方结果模板与页码稳定版本。
- CONFIG 中的题号状态、团队能力、工具限制、剩余时间与风险偏好。
- T0 的环境限制；局部入口缺失时标 `UPSTREAM_MISSING`。

## 执行

1. 对每道适用候选题精读两遍。第一遍只标题面实体、动词、范围和限定词；第二遍提取可量化要求与交付工件。
2. 为每个小问建立一行拆解：原文与页码、字面交付、输入、数学类型、输出形态、答对标准、验证方式、跨问依赖、最大风险、创新候选。
3. 把“分析、预测、评价、设计、给出方案”等动词翻译成评委能打开或定位的文件、图、表、参数、方案或结论。不要用“已建立模型”替代物理工件。
4. 为每问补充 `central_delivery`、候选 hero evidence、信任检验和最可能被评委攻击的证据风险；这是内置 Nature 论证入口，不得改写题意或套期刊叙事。
5. `contest.problem=null` 时，对每道候选题按数据可得性、机理熟悉度、方法匹配、计算成本、结果可验证性、创新空间和写作难度评分；统一量表并写权重依据。
6. 题号已由用户或队伍预选时，只拆所选题，记录选择来源和绕过比较的理由；不得补造其他题评分。
7. 从最后一问反推：在现有时间、数据和工具下能交付什么具体结论，如何验证，失败时如何降级。回答不出来的题不得作为首选。
8. 对推荐题给主风险、最早失败信号、备选降级和 12h 内可验证里程碑。
9. 生成一次只含一个问题的 H-001 裁决简报；AI 不代替人定题。

## 产物

- `MCM-Result/Intermediate-Outputs/T1_PROBLEM_BREAKDOWN.md`：逐问拆解和跨问接口。
- `MCM-Result/Review-Results/T1_FEASIBILITY_MATRIX.csv`：仅在待选模式生成。
- `MCM-Result/Review-Results/T1_SELECTION_BRIEF.md`：推荐、次选、证据、风险和降级。
- `MCM-Result/Intermediate-Outputs/DECISIONS.md`：定题 D-id、选择来源、被否题目和原因。

## 独立 Review

冻结 T1 产物后，由不同上下文 reviewer 按通用 30 分与 T1 专属 70 分评分，逐条核验 `T1-G1` 至 `T1-G4`。H-001 未确认时不因高分放行；review 三件套经 `verify_stage_review.py` 校验后才供总控读取。

## Gate

待选模式要求所有候选题的拆解和评分矩阵完整；预选模式只要求所选题完整拆解并有绕过记录。两种模式都必须满足：

- 每问有字面工件、输入、数学类型、验证标准、最大风险和创新候选。
- 每问的中心交付、主要证据与信任检验可定位，但没有用出版叙事替代题面原文。
- 题面原话与页码可追溯，没有把推测写成题意。
- 最后一问存在可交付形态与降级路线。
- live 模式 H-001 已由人确认；未确认时返回 `NEEDS_HUMAN`。

把所选题、逐问工件、未决歧义、D-id/H-001 和 T2/T3 所需输入写入 `[HANDOFF T1]`。
