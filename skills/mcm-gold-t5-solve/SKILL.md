---
name: mcm-gold-t5-solve
description: 数学建模竞赛 T5 主模型与求解专家。用于依据题型和证据选择主模型，设计算法、标定、收敛与多种子实验，统一跨问接口，限制候选池结论范围，以基线筛选创新，并以内置 Nature 图表合同和稳定视觉语义产出各小问可复现工件。用户提到模型选型、优化求解、仿真、预测、主图、创新点或 T5 Gate 时使用。
---

# T5 主模型与求解

**安装依赖**：本 skill 与 `mcm-gold` **必须同级安装**（`skills/mcm-gold/` 与 `skills/mcm-gold-t0-prepare/` … `skills/mcm-gold-t8-submit/` 并列在同一目录）。下文全部 `../mcm-gold/…` 的必读文档、模板脚本与 Gate 引用都按这个布局解析：只装本阶段、或改动目录层级时，这些链接会一次性全断，必读门禁与机检随之全部失效。缺同级 `mcm-gold` 时先补齐再执行，不要绕过引用继续跑。

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[方法图谱](../mcm-gold/references/methods-atlas.md)、[对抗门禁](../mcm-gold/references/adversarial-gates.md)、[证据契约](../mcm-gold/references/evidence-contract.md)和[内置 Nature 科学图表规范](../mcm-gold/references/nature-figures.md)。只有 T4 Gate 通过后才按需读取[前沿方法卡](../mcm-gold/references/frontier-cards.md)。

## 必需输入

- T1 全部小问的字面工件与验证标准。
- T2 冻结形式化、来源、假设、主备路线和跨问接口。
- T3 冻结数据与拆分；T4 基线实现、指标、R-id 和失败条件。
- H-002 的路线与简化边界；缺失时只做候选 PoC。

## 执行

1. 用题型、假设、样本量、计算预算和验证能力选择模型，不按“听起来高级”选择。
2. 为每个小问定义算法理由、复杂度、参数标定、停止条件、随机种子、输出工件和独立核查方式。
3. 复用冻结跨问接口，不让各问各造一套有利口径。上游更新通过新 R-id/哈希和 supersession 传播。
4. 对优化、仿真和数值模型保存原生日志、状态、gap、残差、收敛曲线、运行时间和失败样本；包装器成功状态不等于科学正确。
5. 候选池或情景筛选必须报告生成规则、覆盖、多样性和搜索预算。候选内胜出不得写成全局最优；稳定性可能只是候选贫乏。
6. 每个核心结论与 T4 基线在同一数据、预算和指标下比较。只有实测改善才保留“改进”；未改善方法进入被否方案。
7. **方案验收判据先于建模声明**（见[对抗门禁](../mcm-gold/references/adversarial-gates.md)方案验收层）。任何"设计方案/给出推荐/提出改进"的小问，MUST 在建模前把判据写入文件并记时间戳，且至少覆盖三类：**性能**（是否更好）、**非平凡性**（方案与现状是否有实质区别）、**支撑域**（预测点是否落在训练特征包络内）。运行后不得改阈值；要改就作废重跑并记录。判据全 PASS 只说明未被这几项推翻，不等于方案成立。
8. 代码里的解读性文字 MUST 由计算值分支生成，不得与代码一同预写。凡形如“→ 说明/证实/表明……”的结论串，都要能指出它由哪个变量的取值决定。
9. 前沿卡总量受 CONFIG 限制，同族至多一张。先写引入假设、收益指标、失败条件和降级路线；最后 8h 不引入新模型。
10. 落地可被评委识别的创新点，并写“没有它会怎样”。仅换库、堆模型或增加术语不算创新。
11. 证据不足以支撑题面字面范围时，仍产出醒目标注的探索工件，但与操作结论在 90 秒内可区分，不进入确定性摘要。
12. 每次实验立刻登记 R-id、输入哈希、命令、种子、源表、图和状态；滚动更新论文当前版。
13. 为每张正文候选图建立 figure contract，明确 `discovery|method|main_result|comparison|validation|robustness|limitation` 角色；每个面板承担唯一证据，不让装饰面板挤占主证据。
14. 跨图保持方法、情景、数据集的颜色和符号稳定。主证据为 hero，验证/控制视觉降级；候选池结果不得使用暗示全局最优的标题、配色或注释。
15. 每个定量面板登记独立样本、种子/折数、中心与区间、指标、基线、预算、求解状态及 source data；用已确认单一后端导出并做最终尺寸 QA。

## 产物

- `MCM-Result/Intermediate-Outputs/T5_MODEL_SPEC.md`：逐问模型、算法、接口、范围和失败条件。
- `MCM-Result/Data-Scripts/src/` 下的代码与 `Data-Scripts/` 下的配置、`Intermediate-Outputs/logs/` 下的运行日志、`Data-Figures/` 下的结果源表和图表。
- `MCM-Result/Review-Results/T5_BASELINE_COMPARISON.csv`、`T5_CANDIDATE_COVERAGE.md`。
- `MCM-Result/Intermediate-Outputs/RESULTS.md`、`DECISIONS.md`、`ASSUMPTIONS.md` 与候选 claim 记录；figure review 记录放 `Review-Results/`。
- 各正文 F-id 的 figure contract 与 `NATURE_QA.csv` 放 `Review-Results/`，source data 和 SVG/PDF/预览放 `Data-Figures/`，脚本放 `Data-Scripts/`。

## 独立 Review

冻结 T5 产物后，由不同上下文 reviewer 按通用 30 分与 T5 专属 70 分评分，逐条核验 `T5-G1` 至 `T5-G6`。方案判据是否在运行前锁定、基线是否同预算、结论是否越出支撑域均须读取时间戳和实际结果。

## Gate

所有小问的字面交付均有可复现物理工件；凡提出方案/推荐的小问，其判据集含性能、非平凡性与支撑域三类且阈值有运行前时间戳；操作结论与探索工件清晰分离；数值有 R-id，外部参数有 S-id，跨问输入追溯到上游 R-id 或数据哈希；正文图有证据合同、源表和最终尺寸 QA；求解状态与范围声明准确；创新点有基线实测收益。探索工件进入正文需 H-002/H-004。

把逐问工件、R/S/D-id、范围限制、失败样本、基线比较和 T6 必检主张写入 `[HANDOFF T5]`。
