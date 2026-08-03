# 内置 Nature 写作与 Office 规范

## 目录

1. SourceModel
2. 读者路径和章节职责
3. 摘要与语言
4. DOCX 路径
5. PPTX 路径
6. Office QA

## SourceModel

T7 先生成唯一 `MCM_SOURCE_MODEL.yaml`，再写论文或生成 Office 文件：

```yaml
classification:
  work_type: mechanism | optimization | prediction | simulation | method | data_resource | mixed
  narrative_arc: question_to_evidence | problem_to_solution | workflow_to_validation | design_to_inference
argument:
  contest_problem: ""
  central_delivery: ""
  gap_or_difficulty: ""
  approach: ""
  main_claims: []
  key_evidence: []
  trust_tests: []
  innovations: []
  reuse_value: ""
  limitations: []
artifacts:
  figures: []
  tables: []
  literal_deliverables: []
```

SourceModel 只引用已存在的 C/R/S/F-id。它是 LaTeX、DOCX、PPTX 和摘要的共同论证源，不另造第二套结论。

## 读者路径和章节职责

按评委阅读顺序组织：这题要求什么，难点是什么，模型为何合理，结果是什么，为何可信，创新在哪里，边界是什么。

- 问题重述：保留题面接口和字面交付，不堆背景。
- 假设：说明依据、影响与检验，不把方便当合理。
- 模型：先定义对象、目标、约束和接口，再给算法实现。
- 结果：先给主结论与物理含义，再给图表和验证。
- 评价：区分误差、局限、适用范围和可推广性。
- 每段一个控制思想，主题句后接数据、比较、解释或限制。

先修 `work_type -> section role -> paragraph logic -> claim/evidence/boundary`，最后才润色句子。

## 摘要与语言

摘要是微型论文：`问题/难点 -> 路线 -> 每问关键数值 -> 信任证据 -> 创新 -> 边界`。最后写，所有数字从 R-id 回读。

- 不让 AI 从零发明核心论证；核心主张来自团队决策和证据台账。
- 中文正文不强制期刊腔，优先明确主语、动作、数值、单位和限制。
- 英文翻译先提取命题，再重建逻辑，不逐分句机械翻译。
- 不新增数值、因果、机制、创新和引用；保留术语与不确定性强度。
- Results 报告观测，Discussion/评价解释含义；不要无意混写。

## DOCX 路径

`paper_format=word` 时从 SourceModel 建 `DocumentSpec`：文档类型、受众、样式、章节角色、字数预算、claim、证据、边界、图表、公式和引用需求。使用 `officecli` 创建/编辑 DOCX，先定义样式，再放内容。

必达：实际可编辑 DOCX、标题层级、页码、图表题注、公式、参考文献和赛事模板要求。不得只交 Markdown 大纲。

## PPTX 路径

只有题面要求或赛后汇报时生成。由同一 SourceModel 建 `SlideSpec`：结论式标题、页面目的、论证角色、视觉、takeaway、来源和讲稿。选图作为证据而非装饰，图缩小后不可读时裁剪、拆页或独占一页。

必达：实际 PPTX、采用图表、来源映射和短 QA 报告；不能停在提纲。

## Office QA

对 DOCX/PPTX 使用 `officecli` 直接回读：

- `officecli validate`
- `officecli view <file> stats`
- `officecli view <file> issues`
- `officecli view <file> annotated`
- `officecli view <file> text`
- DOCX 额外检查 outline、styles、页眉页脚、题注和参考文献。
- PPTX 额外检查页数、标题、来源、讲稿、重叠、裁剪、占位符和图表可读性。

完成声明必须基于实际命令输出和渲染预览。LaTeX 主线不为“Nature 风格”绕到 Office。
