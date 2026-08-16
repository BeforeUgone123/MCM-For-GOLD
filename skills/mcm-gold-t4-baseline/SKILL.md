---
name: mcm-gold-t4-baseline
description: 数学建模竞赛 T4 基线模型专家。用于为第一问建立笨但正确的最简模型，产出首个可复现数值，按内置 Nature figure contract 生成和回读第一张正文图，记录求解器原生日志、gap 与残差，回读官方模板并启动始终可交付版本。用户提到基线模型、第一问出数、结果图、求解状态或 T4 Gate 时使用。
---

# T4 基线模型

**安装依赖**：本 skill 与 `mcm-gold` **必须同级安装**（`skills/mcm-gold/` 与 `skills/mcm-gold-t0-prepare/` … `skills/mcm-gold-t8-submit/` 并列在同一目录）。下文全部 `../mcm-gold/…` 的必读文档、模板脚本与 Gate 引用都按这个布局解析：只装本阶段、或改动目录层级时，这些链接会一次性全断，必读门禁与机检随之全部失效。缺同级 `mcm-gold` 时先补齐再执行，不要绕过引用继续跑。

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[方法图谱](../mcm-gold/references/methods-atlas.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 科学图表规范](../mcm-gold/references/nature-figures.md)和[对抗门禁](../mcm-gold/references/adversarial-gates.md)。先证明最小闭环，再追求复杂度。

## 必需输入

- T1 第一问的字面工件和答对标准。
- T2 的数学定义、假设、接口和路线边界。
- T3 的冻结数据、拆分索引、哈希和已知缺陷；无数据题写明 N/A。

## 执行

1. 定义最简单、可解释、可独立核查的基线。写清输入、参数、输出、损失/目标、约束和失败条件。
2. 用小样本或退化情形先验证单位、边界、守恒和手算结果，再跑完整基线。
2b. **基线的每次运行都 MUST 附带守恒核对与量级合理性核对，并把两个数印在输出里**——不是「先验证一次」而是「每次都印」。二者都是 O(1) 的，却能在几分钟内否掉一个跑得通、看起来也完整的错模型。实测（2025D 矿井突水）：前锋传播基线让 663 个端点全部到达、977 条巷道全部进水，表面完美；但注入 30 m³/min，叶节点处流量之和只有 1.98 m³/min，**93% 的流量凭空消失**——根因是节点只保留最早到达的前锋、把后续汇流的流量直接丢弃。同一次运行里最大到达时刻是 2×10⁸ 分钟（合 386 年），而矿井逃生的固有时间尺度是分钟到小时。**任一核对不通过就不得把该基线的数值写进论文或台账**，哪怕它「跑完了」。

   守恒核对还 MUST **跨多个结构不同的算例**做，单例通过可能纯属巧合。同题续测：修好流量丢失后，附件 1 的守恒残差是 0.0、附件 2 却是 0.27。若只看附件 1 就会判定配流已正确——实际两者共用的配流代码都错，只是附件 1 的拓扑恰好不触发。根因是配流按「前锋到达时刻」遍历而非**有向图拓扑序**：节点 B 若同时被早到的 A 与晚到的 C 指向，处理 B 时 C 尚未处理，C 汇给 B 的那份就漏了；附件 1 恰好没有这种交叉汇流。改用拓扑序后四个算例的残差同时归零。**结构最简单的那个算例最容易给出假阳性，别拿它当验收依据。**
3. 以共享 [`run_all.py`](../mcm-gold/templates/run_all.py) 为入口，固定种子，保存标准输出、错误输出、环境与运行时间。
4. 产生第一问的实际数值、源表和第一张结果图；立即登记 R-id，并把可验证结果写进当前论文草稿。
5. 对优化模型读取求解器原生日志，记录终止原因、可行解目标、上下界/gap、时限、变量/约束数和最大可行性残差。封装层 `status` 不能代替原生日志。
6. 同时报告残差的绝对值与相对尺度。时限内仅得可行解时写“限时可行解”，不写“最优解”。
7. 若序列化导致连续变量微小越界，固定离散决策后重求连续量或做可证明边界修复，并报告修复前后目标差。
8. 有官方结果模板时，在工作副本填入基线结果并做业务值、显示格式、包结构和字节哈希四层回读；解析警告标 `SUSPECT`。
9. 记录基线指标、计算预算和失败模式，作为 T5 所有改进的对照组。
10. 第一张结果图进入论文前，为 F-id 写 figure contract：一句核心结论、角色、archetype、面板证据、最终尺寸、统计、源表、图像完整性、评委风险和 caption boundary。
11. 首次正文图尚未确认后端时，只问用户“Python 还是 R？”。确认后所有绘图、预览、SVG/PDF/PNG 导出和视觉 QA 使用同一后端；缺包时停止渲染，不跨语言代绘。
12. 打开实际 SVG/PDF/预览，在正文最终尺寸回读文字、数字、字体、颜色、遮挡和裁剪，并把观察写入 `NATURE_QA.csv`。

## 产物

- `MCM-Result/Intermediate-Outputs/T4_BASELINE.md`：定义、手算/边界检查、结果、限制和对照指标。
- `MCM-Result/Data-Scripts/src/baseline.*` 与 `Data-Scripts/run_all.py`；原生日志放 `Intermediate-Outputs/logs/`，结果源表和首张图放 `Data-Figures/`。
- `MCM-Result/Intermediate-Outputs/RESULTS.md` 的 R-id、`CLAIM_LEDGER.csv` 的候选主张。
- `MCM-Result/Review-Results/FIGURE_EVIDENCE.csv`、figure contract 与视觉 QA；源表和图放 `Data-Figures/`，脚本放 `Data-Scripts/`。
- `MCM-Result/Paper-Outputs/paper/` 当前可交版本；有模板时包含回读通过的工作副本。

## 独立 Review

冻结 T4 产物后，由不同上下文 reviewer 按通用 30 分与 T4 专属 70 分评分，逐条核验 `T4-G1` 至 `T4-G4`。reviewer 必须实际重跑或回读重跑证据、打开首图并核对源表，不能依据 producer 的成功摘要打分。

## Gate

第一问必须有可写入论文的可行数值、结果图、复现命令与实际回读证据；正文图有 figure contract、source data 和最终尺寸视觉 QA；求解状态、gap 和残差表述准确；输入哈希与假设可追溯。未过 Gate 时禁止使用前沿方法卡，也不得把复杂模型当成基线。

把基线定义、指标、R-id、日志、当前论文、失败条件和 T5 对照要求写入 `[HANDOFF T4]`。
