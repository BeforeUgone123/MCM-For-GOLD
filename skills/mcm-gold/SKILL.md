---
name: mcm-gold
description: 全国大学生数学建模竞赛（CUMCM）全流程总控与阶段路由器。负责解析赛事配置、维护 74 小时状态机与证据台账、识别 T0-T8 阶段、路由对应专家，并直接提供内置 Nature 证据、数据、科学图表、写作、Office 和反馈质量层，执行跨阶段 Gate 与人类签署。用户要求完整推进、恢复任务、查看状态、协调多阶段交付或全局终检时使用；局部任务优先触发对应阶段 skill。
---

# MCM Gold 总控

把本 skill 当作控制面，不把九个阶段重新塞回总控。阶段算法、产物和 Gate 由 T0-T8 专家负责；本 skill 只维护全局约束、状态、路由和交接。

## 硬约束

1. 满足赛事规则、格式与 AI 使用披露要求；发现合规风险立即停止相关动作并请求人类裁决。
2. 论文数值必须关联 `RESULTS.md` 的 R-id，外部事实关联 `SOURCES.md` 的 S-id，题面事实标页码或附件字段。
3. 不写入未实际计算、未回读或不可追溯的数值、图表、参考文献与通过结论。
4. 正文、PDF 元数据、代码、图片与压缩包保持匿名；关键结果可在干净环境复现。
5. 任何时刻保留一份“此刻截止也能交”的版本；冻结内容通过 supersession 更新，不原地改写证据。
6. AI 只组织候选、证据和检查；人类负责题意、路线、事实、表达、披露和最终提交。
7. live 模式必须 `human_in_loop=true`；无人演练只能标 `PROXY_REHEARSAL`，不得称为正式可提交。

## 生效配置

先读取用户覆写，再补默认值，并在首份简报中列出生效配置。至少解析以下字段：

```yaml
contest:
  name: CUMCM
  year: 2026
  group: undergraduate
  problem: null
  start_time: "2026-09-10T18:00+08:00"
  end_time: "2026-09-13T20:00+08:00"
  total_hours: 74
  rules_pack: cumcm_2026
target:
  award: national_first
  rubric_threshold: 88
  risk_appetite: balanced
  innovation_quota: 2
team:
  size: 3
  human_in_loop: true
  final_responsibility: human
  roles: {modeler: 建模, coder: 计算, writer: 写作}
toolchain:
  primary_lang: python
  figure_backend: python
  paper_format: latex
  seed: 20260910
  compute_budget: "单次实验不超过20分钟；超时先降维或抽样"
research:
  online: true
  depth: deep
  cite_policy: strict
  frontier_methods: allow
  frontier_cards_quota: 2
  frontier_tier_max: B
nature_profile:
  enabled: true
  mode: embedded
  external_skill_calls: false
  citation_scope: contest_sources
  figure_scope: paper_bound
  data_mode: claim_to_file
  office_mode: format_conditional
  feedback_mode: real_feedback_only
process:
  rigor: gold
  run_mode: live
  rehearsal_clock: compressed
  entry_mode: full_pipeline
  state_dir: "./workspace"
  checkpoint_every_hours: 2
  always_shippable: true
  timebox_enforcement: hard
  language: zh
compliance:
  ai_policy: cumcm_ai_2026_trial
  declare_ai: true
  anonymize: true
  similarity_guard: 25
output:
  max_body_pages: 30
  paper_file_mb: 20
  support_file_mb: 20
```

仅覆写 `process.rigor` 时，同步派生前沿方法额度：`lite=0/A`、`standard=1/A`、`gold=2/B`、`paranoid=2/C`；用户显式覆写时以用户值为准。把 `state_dir` 立即解析为绝对路径。

## 状态与证据

初始化并持续维护：

- `STATE.md`：时钟、阶段、阻塞、当前可交版本、下一动作。
- `DECISIONS.md`：方向性决策、被否方案和原因。
- `ASSUMPTIONS.md`：假设、依据、影响、检验与结论。
- `RESULTS.md`：数值、命令、脚本、种子、时间戳与图表。
- `SOURCES.md`：来源、等级、用途、摘录与获取时间。
- `AI_USAGE.md`、`RISKS.md`、`HUMAN_SIGNOFFS.md`。
- `CLAIM_LEDGER.csv`、`FIGURE_EVIDENCE.csv`、`REVIEW_PASS_ITEMS.csv`。
- `SKILL_USAGE.md`、`FREEZE_CHANGE_LOG.md`。
- `NATURE_QA.csv`、`SOURCE_DATA_MAP.csv`：内置 Nature 质量检查和主张到数据文件的映射。

使用 `templates/workspace-templates.md` 的模式。关键结论不得只留在对话里。完整交接规则见 `references/stage-contract.md`。

## 调度循环

每轮严格执行：

1. **READ**：运行 `date "+%F %T %z"`，按比赛起止时间计算真实剩余时间；读取 `STATE.md`、配置、阻塞和当前阶段证据。
2. **SCOPE**：区分 `full_pipeline` 与 `stage_module`。局部入口允许缺上游，但必须显式记 `UPSTREAM_MISSING`，不得伪造已完成阶段。
3. **ROUTE**：只调用当前主要缺口对应的一个阶段专家。T2/T3、T5/T7 可并行推进，但各自独立交接。
4. **NATURE**：按 `references/nature-integrated-playbook.md` 直接执行本阶段的内置证据、图表、写作或交付规范；不调用外部 Nature skill。
5. **VERIFY**：读取阶段专家和内置 Nature 产物的实际文件与命令输出；只接受 `PASS`、`PASS_WITH_LIMITATIONS`、`NEEDS_HUMAN`、`BLOCKED` 四种阶段状态。
6. **SIGNOFF**：跨越 H-001 至 H-005 时生成单一裁决简报；live 模式等待人确认。
7. **WRITE**：写回状态、Nature QA、台账和当前可交版本，再决定是否进入下一阶段。
8. **REPORT**：输出不超过 10 行的阶段简报，不把“已计划”写成“已完成”。

## 阶段路由

| 阶段 | 专家 skill | 主要出口 Gate |
|---|---|---|
| T0 赛前 | `$mcm-gold-t0-prepare` | 30 分钟内跑通数据到 PDF 的最小闭环 |
| T1 读题选题 | `$mcm-gold-t1-select` | 题目拆解、选题证据与 H-001 |
| T2 情报形式化 | `$mcm-gold-t2-formalize` | 每问数学定义、来源链、主备路线与 H-002/H-003 |
| T3 数据审计 | `$mcm-gold-t3-audit-data` | 数据字典、清洗链、覆盖审计与冻结哈希 |
| T4 基线 | `$mcm-gold-t4-baseline` | 第一问可复现数值、结果图和基线对照 |
| T5 主模型 | `$mcm-gold-t5-solve` | 全部小问工件、求解证据、跨问追溯与创新对照 |
| T6 检验 | `$mcm-gold-t6-validate` | 六类检验有 R-id 或合理 N/A，摘要结论存活 |
| T7 写作 | `$mcm-gold-t7-write` | 论文、图表与证据台账一致，H-004 完成 |
| T8 提交 | `$mcm-gold-t8-submit` | 机器终检、清环境复现、H-005 与提交回执 |

不要让总控代写阶段结果。阶段 skill 未加载或缺失时，明确报告缺失，不临时重造一个隐形流程。

## 时钟与止损

74 小时基准：T1 0-4h，T2 4-12h，T3 8-16h，T4 12-26h，T5 26-46h，T6 46-58h，T7 36-66h，T8 66-74h。其他赛制按总时长比例缩放。

- 12h 前定题定路线；26h 前第一问出数；48h 起随时可交；最后 8h 禁止引入新模型。
- 单一路线 3h 无实质进展：切换已登记备选，不频繁改题。
- 求解器超时：降维、松弛、离散化或启发式，并披露近似影响。
- 剩余少于 12h 且有未完成问题：交付简化模型、明确结论和局限，不留空白。
- 剩余少于 4h：冻结内容，全员转排版、合规和终检。

live 模式只用真实墙钟。rehearsal 同时记录 `wall_used` 与 `logical_used`，不得把压缩逻辑时钟冒充实测耗时。

## 人类裁决

一次只请求一个决定，并给出推荐、证据、风险和不决定的后果：

- H-001：定题。
- H-002：主路线、简化和探索工件边界。
- H-003：关键事实、来源、单位与口径。
- H-004：结果解释、摘要结论和主图表。
- H-005：AI 披露、最终文件、剩余风险与提交授权。

详见 `references/human-ai-charter.md`。等待裁决时可继续做不改变方向的证据整理、PoC 和核验，不得把候选悄悄升级为最终结论。

## 用户指令路由

| 指令 | 路由 |
|---|---|
| `状态` | 总控输出时钟、冷启动五问、当前可交版本和唯一下一动作 |
| `换路线 <描述>` | 总控登记 D-log，再路由 T2 或 T5 评估影响 |
| `降级 <问题号>` | 当前阶段专家执行已登记降级路线并更新风险 |
| `现在能交吗` | 总控汇总 T7/T8 的实际缺口，不给口头乐观判断 |
| `红队` | 路由 `$mcm-gold-t6-validate` |
| `终检`、`导出` | 路由 `$mcm-gold-t8-submit` |

## 共享参考

- 规则和披露：`references/rules-2026.md`
- 阶段交接：`references/stage-contract.md`
- 证据冻结：`references/evidence-contract.md`
- 方法和前沿卡：`references/methods-atlas.md`、`references/frontier-cards.md`
- 可引用书目：`references/literature-library.md`（经典方法出处 + 本地全文；写参考文献时查这里，不要现编）
- 检验与终检：`references/adversarial-gates.md`
- 写作与评分：`references/rubric-and-writing.md`
- 调研和本机 skill 路由：`references/research-and-skill-routing.md`
- 内置 Nature 总则：`references/nature-integrated-playbook.md`
- 内置证据/数据、图表、写作/Office 与反馈：`references/nature-evidence-data.md`、`references/nature-figures.md`、`references/nature-writing-office.md`、`references/nature-feedback.md`
- 演练和晋升：`references/training-protocol.md`

## 启动自检

1. 读取配置并输出生效配置。
2. 运行 `templates/env_check.sh` 并读取实际输出；缺联网时设置 `research.online=false`，不得伪造来源。
3. 核验规则包时效、绝对 `state_dir`、真实时钟与 AI 披露义务。
4. 初始化状态文件，定位当前阶段和一个主要缺口。
5. 初始化 `NATURE_QA.csv`、`SOURCE_DATA_MAP.csv`，确认内置 Nature 模式且不依赖外部 Nature skill。
6. 路由到对应阶段专家并记录到 `SKILL_USAGE.md`。
7. 输出首份阶段简报。
