# V2.2 2026 规则已吸收的内置 Nature 阶段 Skill 群

状态：`CANDIDATE_NOT_LIVE`。

本仓库以已提交的 v2.1 内置 Nature 阶段 skill 群为基线，把用户提供的三份 CUMCM 2026 官方细则原文、哈希、执行规则、模板与终检门禁吸收到总控和 T7/T8。运行时不调用任何额外 `nature-*` skill。

## 2026 规则快照

- `sources/official/2026/` 保存参赛规则、AI 工具使用规定和论文格式规范的字节级副本、来源说明与独立哈希清单。
- `rules-2026.md` 已切换到 2026 AI 声明位置、固定详情文件名、逐项人工核验和参赛队主导核心建模/分析要求。
- 论文模板、工作区台账、T7 写作、T8 提交和对抗式 Gate 使用同一规则口径。
- 2026 AI PDF 标注 2026-09-01 起试行，但官网规则索引在 2026-08-03 仍可能滞后；开赛前 24 小时必须重新核验官方原文。

## 已内置

- Claim 分段、来源层级、`strong/partial/background/limiting/metadata-only` 支撑判定。
- Raw/processed/figure source/model output 到 C/R/S/F-id 的文件与哈希映射。
- Figure contract、单后端纪律、面板证据层级、统计/source data、矢量导出和视觉 QA。
- 唯一 `MCM_SOURCE_MODEL.yaml`、读者路径、摘要、语言边界、DOCX/PPTX 规格与 officecli 回读。
- 真实评委/导师反馈的保真拆分、动作映射和证据闭环。

## 未晋升原因

静态校验只能证明结构、自包含路由和元数据正确，不能证明：

- 内置 Nature 流程不会在 74 小时内造成不成比例的负担。
- 不同数学家族都能从 figure/source/SourceModel 合同获益。
- 触发边界不会让 T0-T8 同时加载过多上下文。
- 人类 H-001 至 H-005 的实际干扰成本可接受。

完成一题新问题 discovery、一题不同家族 validation 和人工审查前，不复制到 live skills，不改 workspace source mirror，也不吸收未晋升的 v1.8 deliverable-ledger 变更。
