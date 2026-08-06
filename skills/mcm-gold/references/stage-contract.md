# 阶段交接契约

## 目录

1. 运行模式
2. 输入发现
3. 证据写入
4. Gate 状态
5. 人类签署
6. 独立 Review
7. 交接格式

## 运行模式

- `full_pipeline`：读取当前阶段的全部上游交接；缺强制输入时不得宣告 Gate 通过。
- `stage_module`：从用户当前缺口起步。缺少上游材料时写 `UPSTREAM_MISSING`，给出结论强度限制；不得补造 T0-T8 历史。
- `live`：只用真实墙钟，H-001 至 H-005 必须由人签署。
- `rehearsal`：同时记录真实与逻辑耗时。无人的替代裁决标 `PROXY_REHEARSAL`，不得晋升为正式 paper-ready。

## 输入发现

每个阶段开始时：

1. 运行 `date "+%F %T %z"`。
2. 定位绝对 `state_dir`，读取 `STATE.md`、CONFIG、`RISKS.md` 和当前可交版本。
3. 检查阶段 skill 列出的必需输入、上游文件哈希和适用人类签署。
4. 检查本阶段适用的内置 Nature 模块、上游 `NATURE_QA.csv` 与 `SOURCE_DATA_MAP.csv` 限制；不额外调用 Nature skill。
5. 记录 `input_status=READY|PARTIAL|MISSING`。`PARTIAL` 或 `MISSING` 时只执行不依赖缺失输入的工作。
6. 在 `SKILL_USAGE.md` 记录阶段 skill 名、触发原因、预期产物和采用状态。

## 证据写入

- 方向性决定写 `DECISIONS.md`，同时写被否方案和理由。
- 新假设立即写 `ASSUMPTIONS.md`，检验后回填影响。
- 每个实际运行数值写 `RESULTS.md`，包含命令、脚本、种子、时间戳、输入哈希与图表路径。
- 每个外部事实写 `SOURCES.md`，包含来源等级、可访问地址、用途和获取时间。
- 论文主张通过 `CLAIM_LEDGER.csv` 关联 R/S/F-id、人类状态和冻结状态。
- 正文图表通过 `FIGURE_EVIDENCE.csv` 关联源表、脚本、主张、视觉核查和替代状态。
- 内置 Nature 的 claim/source、图表、SourceModel 和 Office 检查写 `NATURE_QA.csv`；主张到原始/处理/图源文件的映射写 `SOURCE_DATA_MAP.csv`。
- Gate 与终检实测写 `REVIEW_PASS_ITEMS.csv`；“已看过”“理论上可行”不是证据。
- 阶段冻结后按 `stage-review-scoring.md` 生成独立 review 的 SCORE/SUMMARY/REPORT；原始 R1/R2 与 FINAL 只追加不覆盖。
- 已冻结内容只通过 `FREEZE_CHANGE_LOG.md` 登记 supersession，不原地覆盖旧结论。

## Gate 状态

阶段只返回四种状态：

| 状态 | 含义 | 是否可路由下一阶段 |
|---|---|---|
| `PASS` | 所有适用项有实际证据，强制签署齐全 | 是 |
| `PASS_WITH_LIMITATIONS` | 核心 Gate 通过，但存在已披露、不会推翻出口的限制 | 可并行进入下游；限制必须随交接传递 |
| `NEEDS_HUMAN` | 证据已准备，等待 H 门或方向性裁决 | 不得把候选升级为最终结论 |
| `BLOCKED` | 缺输入、工具、时间或科学证据，无法满足核心 Gate | 否；执行降级或请求用户决定 |

不得使用 `DONE`、`基本完成`、`看起来通过` 等模糊状态。Gate 通过必须指向实际文件、R/S/D/H 编号和命令输出，并与 FINAL review 的分数、硬门禁及状态一致。

## 人类签署

H-001 定题，H-002 路线和简化，H-003 事实与口径，H-004 表达与主图，H-005 提交授权。AI 可生成单一裁决简报，但不得代签。重大阻碍不采用复杂、脆弱或成本失衡的绕过方案；说明影响后询问用户。

## 独立 Review

producer 只提交冻结工件和自检，不生成正式得分。总控路由不同上下文 reviewer，执行通用 30 分、阶段专属 70 分、硬门禁和条件替代检查；需要双 review 时逐项取低。`verify_stage_review.py` 只验证结构与算术，不能替代 reviewer 对科学内容的判断。

## 交接格式

每个阶段结束时向 `STATE.md` 追加或更新以下块：

```text
[HANDOFF Tn]
status: PASS | PASS_WITH_LIMITATIONS | NEEDS_HUMAN | BLOCKED
skill: mcm-gold-...
inputs: <路径与哈希，或 UPSTREAM_MISSING>
artifacts: <物理文件路径>
evidence: <R/S/D/F/H/pass-id/NQ-id/DS-id>
review_files: <Tn_REVIEW_SCORE_FINAL.csv; Tn_REVIEW_SUMMARY_FINAL.json; Tn_REVIEW_REPORT_FINAL.md>
review_score: <total/100; universal/30; stage_specific/70>
review_status: PASS | PASS_WITH_LIMITATIONS | NEEDS_HUMAN | BLOCKED
hard_gates: <PASS/FAIL/PENDING_HUMAN 摘要>
limitations: <无则 NONE>
next_stage: <Tn/Tn+1/并行阶段>
next_action: <唯一、可执行动作>
checked_at: <ISO8601>
```

阶段简报不超过 10 行，必须包含：阶段与时钟、完成证据、最大风险、当前可交版本、下一动作、待裁决。
