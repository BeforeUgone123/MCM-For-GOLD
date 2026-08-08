# 轻量证据链与冻结规则

## 一、状态

结论、结果、图表依次使用：`candidate -> computed -> checked -> confirmed -> frozen`。

- `candidate`：候选思路/措辞，不可写成论文事实。
- `computed`：真实运行有输出，但未独立核验。
- `checked`：通过对应验证，仍可能等待人的解释确认。
- `confirmed`：证据完整且通过相应 Gate；正式赛时还需对应 HUMAN signoff。
- `frozen`：已被论文/摘要引用，禁止原地改数。

演练无人签署时最高状态为 `rehearsal_confirmed`。

## 二、最小登记表

- `RESULTS.jsonl/RESULTS.md`：数值、命令、输入哈希、种子、日志和验证。
  **复现入口打印的值必须与台账同格式**（同精度、同字段、同顺序）。实测踩过：入口打印
  `航向 177.76538403852268 deg` 而台账记 `航向 177.765 deg`，另一条入口少打印了「重叠」项——
  两条数值其实完全相同，逐条比对却判成不一致，人只能退回去逐位核对，等于把机检退回人工。
  台账登记哪几个量、保留几位，入口就打印哪几个量、保留几位。
- `CLAIM_LEDGER.csv`：claim_id、位置、措辞、数值/单位、R/S/F-id、状态、人确认。
- `FIGURE_EVIDENCE.csv`：figure_id、claim_id、源表/脚本/run、图注、视觉检查和边界。
- `SOURCE_DATA_MAP.csv`：raw/processed/figure source/model output 到 C/R/S/F-id、实际文件和哈希的映射。
- `NATURE_QA.csv`：内置 Nature 证据、图表、写作/Office 和反馈检查的实际观察与状态。
- `REVIEW_PASS_ITEMS.csv`：具体通过项，必须有文件、位置、观测值、期望值和证据。
- `FREEZE_CHANGE_LOG.md`：已冻结结果的替代关系、原因、旧/新证据和人确认。

不是所有局部诊断都要建全套表；一旦内容将进入论文、摘要或提交包，就必须补齐相应链路。

## 三、冻结与替代

R-id 不可复用：主工作区再次计算必须生成新 R-id，旧记录标 `SUPERSEDED` 并在 change log 解释差异；干净复现必须使用空 `state_dir`。模板应拒绝复用已有 R-id，防止新 `PENDING` 记录遮蔽已确认结果；正文、图表、摘要和结果模板必须一起更新并通过一致性审查。

“已检查”不能作为 pass evidence。有效通过项至少写：检查对象、文件/位置、实际观测、期望/容差、命令或 R-id、检查者（AI/人）和时间。XLSX/PDF/ZIP 等复合工件分开验收业务值/结构、显示或渲染、包成员与关系、最终字节哈希；只有前三层等价且时间戳等非确定来源已定位时，才允许字节哈希不同。

## 四、论文就绪门

paper-ready claim 至少可追到：

```text
claim -> R-id/S-id -> 输入哈希/权威来源 -> 模型与运行 -> 验证/诊断
      -> source data/图表/表格 -> 内置 Nature QA -> 一致性检查 -> H-004
```

缺任一关键边时降级为 `candidate`、`diagnostic-only` 或 `SUSPECT`，不得靠流畅表述补证。
