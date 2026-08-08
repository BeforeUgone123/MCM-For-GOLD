# T0-T8 独立 Review 评分契约

本契约统一阶段 review 的评分、门禁、独立性、文件结构和状态映射。评分用于定位质量与返工优先级，不能抵消任何硬门禁。

## 目录

1. 双轨结论
2. 证据锚点
3. 通用 30 分
4. T0-T8 阶段专属 70 分
5. 独立 Reviewer 与合并
6. 固定输出三件套

## 一、双轨结论

- 每阶段总分 100：通用维度 30 分，阶段专属维度 70 分。
- 正式结论仍只取 `PASS|PASS_WITH_LIMITATIONS|NEEDS_HUMAN|BLOCKED`。
- 任一硬门禁 `FAIL` 时为 `BLOCKED`；需要真实人类签署或 reviewer 冲突裁决时为 `NEEDS_HUMAN`。
- 无硬失败且无人类待决时：总分 `>=85`、通用分 `>=24`、专属分 `>=56` 才可 `PASS`；总分 `>=70`、通用分 `>=18`、专属分 `>=42` 可 `PASS_WITH_LIMITATIONS`；其余为 `BLOCKED`。
- 分数、状态、硬门禁三者矛盾时，以更严格结论为准并阻断自动晋级。

## 二、证据锚点

除 T7 继承 rubric 外，每个评分项只能取以下档位，不允许凭感觉给任意分：

| level | multiplier | 含义 |
|---|---:|---|
| `MISSING` | 0 | 缺失、不可读取、无证据或证据与对象不符 |
| `PRESENT` | 0.5 | 有产物，但未实际核验或存在明显缺口 |
| `VERIFIED_LIMITED` | 0.8 | 已实际核验，限制明确且不推翻主要出口 |
| `VERIFIED` | 1.0 | 满足全部标准，实际回读且证据闭环 |

`score = weight * multiplier`。条件不适用时不得删除评分项、缩小分母或自动满分；rubric 必须执行该项预设的替代检查。

## 三、通用 30 分

| ID | 评分项 | 权重 | 满分证据 |
|---|---|---:|---|
| U-01 | 物理工件可定位 | 5 | 声明的产物真实存在、可打开，并位于 `MCM-Result/` 正确目录 |
| U-02 | 主张与来源可追溯 | 5 | 关键结论关联 R/S/D/H/F-id、输入哈希或题面页码 |
| U-03 | 实际核验 | 5 | reviewer 读取真实文件和命令输出，而非复述产出者结论 |
| U-04 | 反证与限制处理 | 5 | 负结果、失败样本、边界和降级均被保留并影响结论强度 |
| U-05 | 状态与交接一致 | 5 | STATE、冻结、supersession、handoff 和实际文件状态一致 |
| U-06 | 合规与人机边界 | 5 | 规则、匿名、AI 记录及适用人类签署无虚构或越权 |

## 四、阶段专属 70 分

### T0 赛前准备

| ID | 评分项 | 权重 |
|---|---|---:|
| T0-01 | 当前官方规则、时限与赛区附加要求核验 | 15 |
| T0-02 | 环境、依赖、字体、求解器、Office 与联网实测 | 15 |
| T0-03 | 30 分钟干净目录和干净环境最小闭环 | 20 |
| T0-04 | 模板、匿名扫描与 AI 披露基线 | 10 |
| T0-05 | rehearsal、时间盒、缺工具降级和交接准备 | 10 |

硬门禁：`T0-G1` 当前规则已核；`T0-G2` 赛区要求已查；`T0-G3` 干净烟雾测试跑通；`T0-G4` 匿名与 AI 披露路径已实测。

### T1 读题与选题

| ID | 评分项 | 权重 |
|---|---|---:|
| T1-01 | 每问字面交付、输入、输出与答对标准拆解 | 20 |
| T1-02 | 候选评分或预选题绕过依据 | 15 |
| T1-03 | 跨问接口、中心交付和主要证据 | 10 |
| T1-04 | 最后一问反推、风险、失败信号与降级路线 | 15 |
| T1-05 | H-001 简报、选择证据和决策记录 | 10 |

硬门禁：`T1-G1` 所选题全部小问有物理工件；`T1-G2` 题面原文与页码可追溯；`T1-G3` 最后一问有可交形态和降级；`T1-G4` live 模式 H-001 已确认。

### T2 情报与数学形式化

| ID | 评分项 | 权重 |
|---|---|---:|
| T2-01 | 检索纪律、来源质量与 claim 支撑分级 | 15 |
| T2-02 | 变量、单位、方程、目标、约束和识别条件 | 20 |
| T2-03 | 机理、假设及其进入模型的映射 | 10 |
| T2-04 | 主、备、降级路线及停止条件 | 10 |
| T2-05 | claim-source、跨问接口和操作/探索边界 | 10 |
| T2-06 | H-002/H-003 待核证据包 | 5 |

硬门禁：`T2-G1` 无禁入域名采用；`T2-G2` 关键事实有有效 S-id；`T2-G3` 全部小问完成形式化；`T2-G4` 主路线有备选和停止条件；`T2-G5` live 模式 H-002/H-003 已确认。

### T3 数据审计

| ID | 评分项 | 权重 |
|---|---|---:|
| T3-01 | 原始数据冻结、来源与只读哈希 | 10 |
| T3-02 | 数据字典、单位、类型、范围和跨表口径 | 15 |
| T3-03 | 缺失、异常、重复、候选键覆盖和结构性零 | 15 |
| T3-04 | 可逆清洗、无泄漏拆分与预处理边界 | 15 |
| T3-05 | 官方模板四层保护；无模板时完成替代检查 | 5 |
| T3-06 | 冻结建模数据、SOURCE_DATA_MAP 和 supersession | 10 |

硬门禁：`T3-G1` 原件未被覆盖且哈希齐全；`T3-G2` 无可见数据泄漏；`T3-G3` 关键组合键覆盖已审；`T3-G4` 建模数据与拆分已冻结；`T3-G5` 模板保护或替代检查完成；`T3-G6` live 模式 H-003 已确认。

### T4 基线模型

| ID | 评分项 | 权重 |
|---|---|---:|
| T4-01 | 基线简单、可解释并匹配第一问接口 | 10 |
| T4-02 | 手算、边界、单位、守恒或退化情形核查 | 10 |
| T4-03 | 首个论文可用数值与 run_all 复现 | 15 |
| T4-04 | 求解状态、gap、残差；非优化模型用替代收敛证据 | 10 |
| T4-05 | 首图 figure contract、source data 和最终尺寸回读 | 15 |
| T4-06 | 当前可交论文版本与 T5 对照接口 | 10 |

硬门禁：`T4-G1` 有论文可用的实际数值；`T4-G2` run_all 能重跑关键结果；`T4-G3` 求解/收敛状态表述真实；`T4-G4` 首图、源表和视觉回读齐全。

### T5 主模型与求解

| ID | 评分项 | 权重 |
|---|---|---:|
| T5-01 | 全部小问模型定义、接口和物理工件 | 15 |
| T5-02 | 算法理由、标定、停止条件、种子与复现 | 15 |
| T5-03 | 同数据、同预算基线比较和创新收益 | 10 |
| T5-04 | 性能、非平凡性、支撑域判据运行前锁定 | 10 |
| T5-05 | 求解证据、候选覆盖、失败样本和范围声明 | 10 |
| T5-06 | 图表合同、源表、稳定视觉语义和最终尺寸 QA | 10 |

硬门禁：`T5-G1` 全部字面交付有实际工件；`T5-G2` 方案类问题已预注册三类判据；`T5-G3` 核心结论有基线；`T5-G4` 论文候选数字来自真实运行；`T5-G5` 未把候选内胜出写成全局最优；`T5-G6` 正文图有合同、源表和回读。

### T6 检验与稳健性

| ID | 评分项 | 权重 |
|---|---|---:|
| T6-01 | 正确性检验 | 10 |
| T6-02 | 灵敏度检验 | 10 |
| T6-03 | 误差分析 | 10 |
| T6-04 | 同输入、预算和指标的对照 | 10 |
| T6-05 | 稳健性与不确定性 | 10 |
| T6-06 | 干净环境复现 | 10 |
| T6-07 | 对抗攻击、主图审计和失败 claim 降级 | 10 |

硬门禁：`T6-G1` 六类检验均有证据或预设替代检查；`T6-G2` 摘要候选主张已受实际攻击；`T6-G3` 干净复现通过；`T6-G4` 失败 claim 已降级、替代或撤回；`T6-G5` 交叉实现独立性表述真实。

### T7 论文与图表

T7 不另造重复评分表。专属分读取通过结构校验的固定七维 `T7_RUBRIC_REVIEW.csv`，按 `stage_specific_score = rubric_total * 0.7` 折算。七维原始阈值与单项及格线仍是独立硬门禁；新总分不能覆盖它们。T7 专属行使用 `level=DERIVED`，七项权重依次为 `10.5, 7, 17.5, 15.4, 9.1, 8.4, 2.1`，分数按对应原始维度得分比例计算。

篇幅异常档位封顶：阅读版触及深度触发线（正文 <14 页或正文汉字 <10000，以 `T7_PAPER_CONTRACT.json` 的 `depth_metrics` 实测值为准）且契约未记录 `DEPTH_FORM_CHECKS_PASSED` 豁免时，`模型建立`与`求解与结果正确性`两维折算档位封顶 `VERIFIED_LIMITED`（得分比例取 min(原始比例, 0.8)），原始 rubric 得分再高也不得取满；已记录豁免则按实际比例折算。

REPORT 强制对比小节：T7 的 REPORT.md 在固定顺序之外必须包含"每问实测页数/汉字数与预算对比"小节，数据取自 `T7_PAPER_CONTRACT.json` 的 `depth_metrics`，对照篇幅预算 target 列逐问列出实测与缺口；任一缺口写为 P1 finding，不得被总分掩盖。

联动说明：`T7-G3` 已要求 T7 paper contract 通过，契约判 `NEEDS_EXPANSION`（每问正文、编号公式、结果表低于 floor，或摘要、模型评价密度不足）时该门禁自动 FAIL，无需新增硬门禁；触线但形态检查全过的豁免以契约记录的 `DEPTH_FORM_CHECKS_PASSED` 为准，H-004 仍须人工阅读实际 `main.pdf` 复核表达层。

硬门禁：`T7-G1` 每问六项覆盖无 WEAK/MISSING；`T7-G2` 七维总分和单项达到原阈值；`T7-G3` T7 paper contract 通过；`T7-G4` 数字、图表、RESULTS 和引用一致；`T7-G5` 两版共享正文且提交版含真实清单和完整代码；`T7-G6` live 模式 H-004 已确认。

### T8 终检与提交

| ID | 评分项 | 权重 |
|---|---|---:|
| T8-01 | 最终文件冻结、清单、哈希与提交白名单 | 10 |
| T8-02 | paper contract、覆盖和 rubric 继承闭环 | 10 |
| T8-03 | 页数、大小、字体、元数据和包结构机器检查 | 10 |
| T8-04 | 干净环境复现及论文/图表/RESULTS 数字一致 | 20 |
| T8-05 | 匿名、AI、检索纪律和赛区附加要求 | 10 |
| T8-06 | 打包、H-005、平台回执和下载哈希 | 10 |

`review_mode=pre_submit` 时，T8-06 的替代检查是提交计划、文件白名单和覆盖策略；阶段最多为 `NEEDS_HUMAN`。只有 `review_mode=post_submit` 且真实回执与下载哈希已回读，T8 才可 `PASS`。

硬门禁：`T8-G1` 最终 paper contract 通过；`T8-G2` 三条取消资格红线有实测证据；`T8-G3` 全国及赛区要求均核验；`T8-G4` 匿名、AI 和检索纪律通过；`T8-G5` 最终包干净复现通过；`T8-G6` H-005 已确认；`T8-G7` post-submit 回执和下载文件已核验。

## 五、独立 Reviewer 与合并

- 产出者只能自检，不能生成正式分数。正式 reviewer 的 `reviewer_context_id` 必须不同于 `producer_context_id`。
- T0-T5 默认一名独立 reviewer；R1 总分落在 80-90 分时必须增加 R2。
- T6-T8 固定两名独立 reviewer。R2 在提交自己的原始评分前不得读取 R1 分数。
- 双 reviewer 逐项取较低分，硬门禁取更严格状态；不得平均。
- 总分差超过 10 分、单项相差两个证据档位或硬门禁判断冲突时，标记 `NEEDS_HUMAN`，保留冲突证据。客观硬失败在被证伪前仍保持 `BLOCKED`。
- 原始 review 只追加不覆盖；重新 review 使用新 `review_run_id` 并登记 supersession。

## 六、固定输出三件套

全部放入 `MCM-Result/Review-Results/`：

```text
Tn_REVIEW_SCORE_R1.csv
Tn_REVIEW_SUMMARY_R1.json
Tn_REVIEW_REPORT_R1.md
Tn_REVIEW_SCORE_R2.csv        # 触发双 review 时
Tn_REVIEW_SUMMARY_R2.json
Tn_REVIEW_REPORT_R2.md
Tn_REVIEW_SCORE_FINAL.csv
Tn_REVIEW_SUMMARY_FINAL.json
Tn_REVIEW_REPORT_FINAL.md
```

### SCORE.csv

固定表头：

```csv
review_id,stage,criterion_id,scope,criterion,weight,level,multiplier,score,observed,evidence_paths,evidence_ids,gate_refs,deduction_reason,repair_action,reviewer_id,source_review_ids,producer_context_id,reviewer_context_id,reviewed_at
```

`scope` 仅取 `universal|stage_specific`。`observed` 必须写实际观察，`evidence_paths` 必须指向可读取文件；只写“已检查”“质量良好”或阶段专家口头结论按 `MISSING` 计。R1/R2 的 `source_review_ids` 写自身 `review_id`；FINAL 由机械合并过程生成，每行记录实际提供较低分的原始 review id，平分时同时记录。

### SUMMARY.json

至少包含：

```json
{
  "schema_version": "1.0",
  "review_run_id": "T4-20260911T120000-R1",
  "review_kind": "R1",
  "stage": "T4",
  "review_mode": "standard",
  "producer_context_id": "producer-context",
  "reviewer_context_id": "independent-review-context",
  "review_independence": "independent_context",
  "scores": {"universal": 0, "stage_specific": 0, "total": 0},
  "hard_gates": [{"gate_id": "T4-G1", "status": "PASS", "evidence": ["path#anchor"]}],
  "run_mode": "live",
  "requires_second_review": false,
  "review_conflict": false,
  "status": "BLOCKED",
  "limitations": [],
  "top_repairs": [],
  "source_score_file": "T4_REVIEW_SCORE_R1.csv",
  "source_reviews": ["T4-20260911T120000-R1"],
  "generated_at": "2026-09-11T12:00:00+08:00"
}
```

R1/R2 的 `review_independence` 只接受 `independent_context|independent_agent`。FINAL 允许 `independent_merge`，但只能机械执行逐项取低，不得改写原始观察、证据或分数；`source_reviews` 必须列出参与合并的原始 review。同上下文自评不得生成 `_FINAL`。

### REPORT.md

顺序固定为：阶段结论与总分、硬门禁、P0/P1/P2 findings、逐项扣分、前三项修复动作、限制与 handoff。finding 必须引用实际文件和锚点；没有问题时也要写剩余测试空白。

运行 `templates/verify_stage_review.py` 校验 SCORE 与 SUMMARY 的字段、权重、证据档位、分数计算、硬门禁、状态映射和本阶段必读文档登记。结构校验通过不代表科学判断正确。

```bash
python3 templates/verify_stage_review.py --stage T4 \
  --score  MCM-Result/Review-Results/T4_REVIEW_SCORE_R1.csv \
  --summary MCM-Result/Review-Results/T4_REVIEW_SUMMARY_R1.json \
  --skill-usage MCM-Result/Intermediate-Outputs/SKILL_USAGE.md
```

### 硬门禁状态

`hard_gates[].status` 取 `PASS|FAIL|PENDING_HUMAN|REHEARSAL_NA`。

`REHEARSAL_NA` 只用于**演练场景下客观无法满足**的门禁——例如 T0-G2「本赛区附加要求」须向本校教务或赛区组委会查证，而演练没有赛区归属。它必须同时满足：`run_mode` 为 `rehearsal`，且该 gate 写明 `rehearsal_na_reason`。带 `REHEARSAL_NA` 的阶段**上限为 `PASS_WITH_LIMITATIONS`，永不判 `PASS`**。

把「演练里查不到」记成 `FAIL` 会让整条流水线卡在一个与被测对象无关的门上；记成 `PASS` 则抹掉了真实比赛中必须补做的动作。这个状态存在的意义是把二者分开，而不是给漏查开后门——live 模式下使用它直接判错。

### 必读文档门禁

`--skill-usage` 指向 `SKILL_USAGE.md`，脚本核对其「必读文档登记」表是否覆盖 `SKILL.md` 中本阶段的必读清单，并拒收「已读」「符合要求」一类空洞占位。**该参数必传**，且门禁没有旁路：原先的 `--no-doc-gate` 已移除——它名义上「仅当阶段确无必读清单时使用」，而 T0–T8 每个阶段都有非空必读清单、`DOC_GATE_UNIVERSAL` 还无条件追加，因此它对任何合法调用都没有正当用途，实测一个 flag 即可让 `doc_gate=SKIPPED`、`status=PASS`、退出码 0。

设立这道门的原因是实测失效：某次完整演练中 18 份 references 只被读了 2 份，写作 target、图表契约、文献纪律、反幻觉铁律全部落空，而所有机检仍然全绿——**没有任何既有检查能发现「规范没被读」**。
