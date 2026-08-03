# Nature 内置能力总则

## 目录

1. 定位与优先级
2. 内置模块
3. 阶段映射
4. 采用状态
5. 降级纪律

## 定位与优先级

Nature 能力是 `mcm-gold` skill 群的内置质量层，不是外部 skill 依赖。阶段专家直接执行相应流程，不调用任何 `nature-*` skill。

优先级固定为：

1. 当届赛事规则、题面、官方模板和人类签署。
2. MCM 的题意、数据、求解、检验、复现和时间 Gate。
3. 内置 Nature 论证、证据、图表、写作和交付规范。
4. 视觉风格、期刊习惯和可选格式。

不能用出版级语言或图表掩盖科学缺陷，也不能为了模仿 Nature 限制普通国赛的合理来源范围、虚构期刊声明或增加非必交材料。

## 内置模块

| 模块 | 参考文件 | 核心能力 |
|---|---|---|
| 证据与数据 | `nature-evidence-data.md` | claim 分段、支撑分级、来源审计、claim-to-file 映射 |
| 科学图表 | `nature-figures.md` | figure contract、面板证据层级、后端纪律、统计与视觉 QA |
| 写作与 Office | `nature-writing-office.md` | SourceModel、读者路径、摘要、润色边界、DOCX/PPTX 结构与回读 |
| 反馈闭环 | `nature-feedback.md` | 评委/导师意见保真拆分、动作映射、证据和未决人输入 |

阶段 skill 只读本阶段需要的模块，不一次加载全部细节。

## 阶段映射

- T0：固化绘图后端、字体、矢量导出、Office 和渲染能力。
- T1：用中心交付、物理工件和证据风险审题，不套期刊叙事。
- T2：执行 claim 分段、支撑分级和来源边界。
- T3：建立 raw/processed/source data 到 claim 的文件与哈希映射。
- T4：为第一张正文候选图建立 figure contract。
- T5：让主结果、方法和基线对照图共享稳定视觉语义。
- T6：审查主图统计、源数据、独立验证轴和过度主张。
- T7：建立唯一 SourceModel，完成论证、图表、文字和 Office 分叉。
- T8：回读所有内置 Nature 产物，执行格式、渲染、匿名和包级一致性检查。
- 赛后：收到真实反馈时执行逐点闭环。

## 采用状态

内置 Nature 产物使用 `DRAFT -> EVIDENCE_CHECKED -> HUMAN_REVIEWED -> ADOPTED`。科学失败时为 `REJECTED`，缺输入为 `BLOCKED`。状态写入对应 claim/figure/source/QA 台账，不新增一个平行的外部调用状态机。

`ADOPTED` 只表示该产物通过本模块验收；阶段仍须通过自身 Gate。正文采用还需适用的人类签署。

## 降级纪律

- 缺绘图运行时：保留所选后端脚本和源表，停止渲染；不跨语言代绘。
- 缺 Office 工具且 Office 为必交：作为重大阻碍报告，不拼接脆弱转换链。
- 时间不足：保留 claim/source/figure 合同和最低可交版本，取消非必需 TIFF、PPT、仓储声明和语言装饰。
- 内置规范与赛事规则冲突：以赛事规则为准，并在 `NATURE_QA.csv` 记录竞赛适配理由。
