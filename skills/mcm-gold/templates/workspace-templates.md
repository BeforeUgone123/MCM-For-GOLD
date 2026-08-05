# 状态与证据文件模板

在 `CONFIG.process.state_dir` 下建立；示例只定义最小字段，按记录重复行。

## STATE.md

```markdown
# STATE | updated=<ISO8601> | mode=<live/rehearsal> | wall_used=<h> | logical_used=<h> | remaining=<h> | stage=<T0-T8>
已定案=<D-id...>｜进行中=<任务+负责人+ETA>｜已交付=<路径+R-id>｜阻塞=<问题+预案>
下一步（≤3）=<...>｜可提交版本=<路径>｜缺口=<...>
```

`live` 模式令 `logical_used=wall_used`；压缩演练可单独推进 `logical_used`，但不得省略 `wall_used`，复盘耗时一律读取墙钟值。

## DECISIONS.md

```markdown
## D-<nnn> | <ISO8601> | <决策标题>
决策=<...>｜理由/实测证据=<R/S-id>｜被否方案及原因=<...>
影响/回滚触发=<...>｜核心建模先行依据（涉及 AI 时）=<时间戳+队员原始判断>
```

## ASSUMPTIONS.md

```markdown
| ID | 假设 | 依据(Q页/附件/S-id) | 影响范围 | 检验方式 | 结论/R-id |
|---|---|---|---|---|---|
| A-<nnn> | <...> | <...> | <小问/公式> | <替代情景或范围> | <...> |
```

## RESULTS.md

由 `templates/run_all.py` 从同目录 `RESULTS.jsonl` 生成，不手工改表；复现核对后用 `--confirm` 回填。

```markdown
| ID | 内容 | 值/单位 | 输入 SHA-256 | 脚本/命令 | 种子 | 计算时间 | 核验时间 | 图表 | verify | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| R-<nnn> | <...> | <...> | <path:hash> | <...> | <...> | <ISO8601> | <ISO8601或空> | <...> | <evidence> | PENDING/CONFIRMED/SUSPECT/STALE |
```

**计算时间与核验时间必须分列**：`computed_at` 是这个数被算出来的时刻，`--confirm` 只写 `verified_at`、绝不覆盖 `computed_at`。合成一列会让"数值何时产生"不可考，T8 比对时间戳时失去意义。

## SOURCES.md

```markdown
| ID | 类型 | 标题 | URL/DOI/题面位置 | 可信度 | 对应claim/用途 | 支撑等级 | 关键内容 | 获取时间 |
|---|---|---|---|---|---|---|---|---|
| S-<nnn> | 标准/论文/题面 | <...> | <...> | A/B/C | <C-id/参数/口径> | strong/partial/background/limiting/metadata-only | <短摘录或字段> | <ISO8601> |
```

可信度：A=官方/标准/同行评议；B=机构报告/数据文档，须交叉验证；C=博客/题解/AI，只作线索；`metadata-only`不得成为论文支撑。

## RISKS.md

```markdown
| ID | 风险 | 触发条件 | 概率/影响 | 预案 | 状态/D-id |
|---|---|---|---|---|---|
| K-<nnn> | <...> | <可观测阈值> | <低中高/范围> | <动作+截止时间> | <...> |
```

## AI_USAGE.md

使用 AI 时从第一次交互起维护，赛末导出为支撑材料中的 `AI 工具使用详情.pdf`；未使用时不建本文件。无论是否使用，均在论文**参考文献之前**放置 2026 版“AI 工具使用声明”。

```markdown
# AI 工具使用详情
工具=<名称/版本或型号>｜用途与环节=<...>｜主要提示方式与使用过程=<...>
核心建模与分析的队员主导证据=<H/D-id+队员原始判断>｜采用及人工修改=<...>｜人工核验=<动作+R/pass-id+结果>
典型交互 <ISO8601>：提示词/完整要点=<...>｜回复/完整要点=<...>｜采用状态=<采用/部分/否决>｜对应 C/D/R/F-id=<...>
```

语言润色可不在官方详情 PDF 中展开“采纳、人工修改和核验”小项，但仍须逐项人工审查与核实；工作区建议保留记录以便 H-005 判断。

## HUMAN_SIGNOFFS.md

只记录人的真实确认；演练代理不得伪装成人签署。签署含义见 `references/human-ai-charter.md`。

```markdown
| ID | 阶段 | 决策/核验范围 | 证据包 | AI 推荐 | 人的决定 | 状态 | 确认人/时间 | 被替代条目 |
|---|---|---|---|---|---|---|---|---|
| H-001 | T1 | <题意与交付物> | <Q页/D-id> | <...> | <原话或摘要> | PENDING/HUMAN_CONFIRMED/HUMAN_REJECTED/PROXY_REHEARSAL/SUPERSEDED | <...> | <...> |
```

## CLAIM_LEDGER.csv

```csv
claim_id,location,claim_text,value,unit,result_ids,source_ids,figure_ids,status,human_signoff,updated_at
C-001,摘要,<可核查结论>,<数值>,<单位>,R-001,S-001,F-001,candidate,H-004,2026-09-12T10:00:00+08:00
```

## FIGURE_EVIDENCE.csv

```csv
figure_id,file,claim_ids,core_conclusion,panel_roles,backend,final_size,statistics,source_table,script,run_ids,caption_boundary,visual_check,status,updated_at
F-001,figures/example.pdf,C-001,<一句可证伪结论>,<主证据/验证/控制>,python,<栏宽×高度>,<n/区间/检验>,intermediate/example.csv,src/plot_example.py,R-001,<图能与不能说明什么>,<分辨率/遮挡/数值回读>,checked,2026-09-12T10:00:00+08:00
```

## PAPER_COVERAGE_LEDGER.csv

每问固定六行；这是论文论证的验收账本，不与通用 `REVIEW_PASS_ITEMS.csv` 混用。`paper_anchor` 必须是阅读版 PDF 经 `pdftotext` 后可检索的真实标题、表题或句首。`validation` 关联主要 K-id 和 R/P/V-id；`result` 关联可复核 R/P/V-id。`interface/definition/algorithm/result` 不允许 `N_A`；其他 `N_A` 必须关联 D-id 和理由。

```csv
question_id,component,required_content,claim_or_risk_ids,paper_anchor,evidence_ids,observed,status,human_status
Q1,interface,<输入/待求对象/跨问接口/物理工件>,C-001,4.1 问题一任务接口,Q1页2;<题面字段>,<回读到输入与输出>,PASS,HUMAN_ACCEPTED
Q1,definition,<变量/单位/目标/方程/约束及选型理由>,C-001,4.2 问题一模型定义,R-001,<回读到定义和理由>,PASS,HUMAN_ACCEPTED
Q1,algorithm,<数据/参数/算法/停止条件>,C-001,4.3 问题一求解,R-002,<回读到可复现步骤>,PASS,HUMAN_ACCEPTED
Q1,result,<数值/单位/图表/基线/关键样本>,C-002,表 3 问题一结果,R-003,<回读到结果和单位>,PASS,HUMAN_ACCEPTED
Q1,validation,<匹配主要风险的实际检验>,K-001,4.5 问题一稳健性检验,R-004;P-021,<回读到检验范围和结论>,PASS,HUMAN_ACCEPTED
Q1,boundary,<代表什么/不代表什么/依赖与复核触发>,C-002;K-001,4.6 问题一解释边界,D-008;<R-id>,<回读到拒答或适用边界>,PASS,HUMAN_ACCEPTED
```

`status` 仅取 `PASS/WEAK/MISSING/N_A`；`human_status` 仅取 `PENDING/HUMAN_ACCEPTED/PROXY_REHEARSAL`。机器结构通过不能替代 H-004；无人演练全部写 `PROXY_REHEARSAL`。

## T7_RUBRIC_REVIEW.csv

必须逐行使用 `references/rubric-and-writing.md` 的七个维度、满分和及格线，不得临时发明四维或等权评分表。

```csv
dimension,score,max_score,pass_score,evidence,observed,status
摘要页,13,15,10,<实际页码/句子>,<数值结论与边界回读>,PASS
问题分析与假设,8,10,6,<实际页码/表>,<假设依据与回收方式>,PASS
模型建立,22,25,16,<实际页码/公式>,<定义、理由与基线关系>,PASS
求解与结果正确性,19,22,15,<实际页码/图表/R-id>,<算法、参数、结果与复现>,PASS
检验与稳健性,11,13,8,<实际页码/K/R/P-id>,<六类检验或合理N/A>,PASS
写作与图表,11,12,8,<实际页码/图号>,<数字一致与渲染回读>,PASS
合规与附录,3,3,3,<提交版/清单/代码>,<规则与附录回读>,PASS
```

总分低于 `CONFIG.target.rubric_threshold` 或任一维低于及格线时，论文契约只能为 `NEEDS_EXPANSION`，T7 阶段不得写 `PASS/PASS_WITH_LIMITATIONS`。

## REVIEW_PASS_ITEMS.csv

“已检查”不是证据；每行必须写实际观测和期望/容差。

```csv
pass_id,stage,item,file_location,observed,expected_or_tolerance,evidence,checker,checked_at,status
P-001,T4,销量约束残差,workspace/solver.log,0,<=1e-6,R-001,AI,2026-09-11T12:00:00+08:00,PASS
```

## SKILL_USAGE.md

```markdown
| 时间 | 证据缺口 | 调用 skill | 产物 | 采用/否决 | 边界 |
|---|---|---|---|---|---|
| <ISO8601> | <为什么需要> | <skill-name> | <路径> | <采用/部分/否决+理由> | <不替代哪项人类判断> |
```

## NATURE_QA.csv

记录内置 Nature 模块的实际检查。`ADOPTED` 只表示产物通过模块验收，不代表阶段 Gate 自动通过。

```csv
qa_id,stage,module,artifact,claim_refs,observed,expected,evidence,human_gate,status,updated_at
NQ-001,T4,figure_contract,figures/F-001.pdf,"C-001;R-001;F-001",<实际观察>,<合同与容差>,P-001,H-004,EVIDENCE_CHECKED,2026-09-11T12:00:00+08:00
```

## SOURCE_DATA_MAP.csv

把 Nature 的数据可用性原则适配为竞赛支撑包证据映射；没有真实仓库或标识符时留空，不得虚构。

```csv
dataset_id,kind,claim_ids,result_ids,source_ids,actual_location,sha256,access_route,restriction,license_or_terms,generated_by,status,updated_at
DS-001,figure_source,C-001,R-001,S-001,intermediate/fig1.csv,<sha256>,support_package,NONE,<官方附件条款>,src/plot_fig1.py,VERIFIED,2026-09-12T10:00:00+08:00
```

## MCM_SOURCE_MODEL.yaml

T7 的唯一论证源；完整说明见 `references/nature-writing-office.md`。

```yaml
classification:
  work_type: optimization
  narrative_arc: problem_to_solution
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

## FREEZE_CHANGE_LOG.md

```markdown
## FC-<nnn> | <ISO8601> | <旧 R/C/F-id> -> <新 R/C/F-id>
原因=<...>｜旧值/旧措辞=<...>｜新值/新措辞=<...>｜影响位置=<摘要/正文/图/表/模板>
回归检查=<P-id...>｜人类确认=<H-id/status>｜旧记录状态=SUPERSEDED
```
