# V2.4 论文闭环晋升记录

状态：`PROMOTED_TO_LIVE_2026-08-05`。

本版本以 v2.3 工程加固版本为基线，针对“写作规则已经存在但 T7/T8 没有消费和验收”的根因增加机器可执行的论文闭环。2026-08-05 经用户明确授权晋升为本地 live 并发布；冻结回放与历史评分不变。

晋升决策将已知题 post-hoc Gate 作为上线前机器证据，并明确接受尚未完成的 forward discovery/validation 风险。这些项目转为上线后验证债，不得因已发布而追认为已验证。

## 2026-08-05 论文闭环

- **CC-032 逐问论证验收**：新增 `PAPER_COVERAGE_LEDGER.csv`。每问固定登记题意接口、数学定义、求解步骤、结果、验证和解释边界，必须回读实际阅读版 PDF 锚点并映射 C/K/R/P/V/D-id；`WEAK/MISSING` 不能继续伪装通过。
- **固定七维 rubric**：新增机器读取的 `T7_RUBRIC_REVIEW.csv`，只接受 `rubric-and-writing.md` 的七个维度。总分低于配置目标或单项低于及格线时返回 `NEEDS_EXPANSION`，不再允许自创四维评分表。
- **CC-033 双版本闭环**：阅读版和提交版从同一科学正文生成；提交版必须有最终支撑目录的真实文件列表和完整源程序，且 T8 禁止把 `main.pdf` 重命名成提交版。
- **确定性校验器**：`templates/verify_paper_contract.py` 回读账本、rubric、PDF 正文锚点、双版本一致性、支撑清单与代码内容；短于建议页数只给 `DEPTH_REVIEW_REQUIRED`，页数本身不判失败。
- **状态上限**：结构与机器检查不能替代 H-004/H-005。无人演练最高为 `PROXY_REHEARSAL`；缺人类验收为 `NEEDS_HUMAN`。

当前 2024 A v2.3 产物仅用于已暴露问题的红灯回归，不计独立盲测。已知题 post-hoc Gate 见下；未完成的新问题 T7-T8 discovery、不同家族 forward validation、H-004/H-005 和实际记账耗时已登记为上线后验证债。

### 2026-08-05 跨题 post-hoc Gate

- `B-2022-C-001`：原 8 页正文以 16 个 `WEAK` 覆盖项、合规单项 2/3 和总分 86/100 返回 `NEEDS_EXPANSION`；18 页证据扩写版以 24/24 覆盖、89/100 proxy、91/91 支撑文件和 24/24 源程序达到 `PROXY_REHEARSAL`。冻结 86 分和 H 状态未改。
- `B-2019-D-001`：18 页正文以 18/18 覆盖、89/100 proxy、0 error/0 warning 达到 `PROXY_REHEARSAL`，证明页数没有被当作质量配额；该测试不清除既有亚小时物理交付缺口。
- 实测发现 PDF 中同一 maxT 公式可能被 `pdftotext` 以不同字符顺序回读。校验器现仅在字符集合完全一致且相似度至少 0.995 时降为 `PDF_TEXT_ORDER_VARIANCE` 警告；否则仍报正文漂移。

以上满足已知题的红灯、修复和页数负对照，只是 post-hoc regression，不是新的 forward discovery/validation。上线后验证债仍包括一题新问题 T7-T8 discovery、另一题不同家族 forward validation、H-004/H-005 和实际记账耗时。

## 2026-08-05 加固

- `literature-library.md` 的 60 条书目补齐文献题名、完整作者、出处和 DOI/稳定标识；校验器拒绝省略号和不可解析 DOI。
- live 模式不再用通用搜索引擎做连通性探针或逐段查重；只直接访问安全 URL、强制域名白名单接口、赛事认可查重系统或本地语料。
- `run_all.py` 为 `RESULTS.jsonl`/`RESULTS.md` 增加跨进程锁、重复 R-id 原子检查、`fsync` 和 Markdown 原子替换。
- `tests/` 覆盖书目完整性、群组结构、清单、第三方声明、并发重复 ID、并行写入和核验时间戳；`trigger_cases.json` 固化人工前向触发样本。
- `THIRD_PARTY_NOTICES.md` 明确官方规则快照不适用 MIT License；再次分发仍须由发布者确认官方条款。

## 2026 规则快照

- `sources/official/2026/` 保存参赛规则、AI 工具使用规定和论文格式规范的字节级副本、来源说明与独立哈希清单。
- `rules-2026.md` 已切换到 2026 AI 声明位置、固定详情文件名、逐项人工核验和参赛队主导核心建模/分析要求。
- 论文模板、工作区台账、T7 写作、T8 提交和对抗式 Gate 使用同一规则口径。
- 2026 AI PDF 标注 2026-09-01 起试行，但官网规则索引在 2026-08-03 仍可能滞后；开赛前 24 小时必须重新核验官方原文。

### 2026-08-03 原文比对补漏

对三份 PDF 做了逐条回读，补齐此前只收了前半句、漏掉后果条款的地方：

- **三条取消资格红线**入 `rules-2026.md` 第二节、第五节 checklist、`adversarial-gates.md` 终检清单和 T8 Gate：① 缺源程序 / 程序不能运行 / 运行结果与论文不符（格式规范第五条）；② 支撑材料与论文内容不相符（第十一条）；③ 不符合格式规范（第十二条）。前两条是 `run_all.py` 清环境复现存在的官方依据，此前只作为内部质量标准执行。
- **赛区附加要求**（第八条"各赛区可以对论文做相应的要求"）：T0 新增查证步骤与 Gate 项，T8 终检新增核验项，未登记时阻断补查。此前全流程只核全国级规则。
- **平台禁令可执行化**（参赛规则第 5 条点名贴吧/知乎/小红书/CSDN/GitHub 等，"浏览"本身即违纪）：`rules-2026.md` 第五节新增「检索纪律」小节，T2 情报协议落成禁入域名清单 + `SEARCH_LOG.md` 记录格式 + 误命中处置，T2/T8 Gate 增加对应检查。此前只有原则表述，而本 skill 默认 `research.online=true, depth=deep`，中文检索极易命中 CSDN/GitHub。
- **证据等级分层**：第一节表格新增证据等级列，区分 `SNAPSHOT+HASH`（三份 PDF，已锁哈希可离线回查）与 `URL_ONLY`（第一次通知、赛区评阅规范）。比赛起止时间、报名截止、相似度红线、报送比例均属后者，且评阅规范仍是 **2025** 版。CONFIG 的 `start_time`/`end_time` 直接决定 74 小时状态机却属 `URL_ONLY`，T0 新增重核步骤与 Gate 项。
- 补收：附录**页数不限**、电子版**必须是单独一个文件**、指导教师禁止指导的具体形式、被动接收讨论信息同样违纪。

`tooling/validate_skill_group.py` 同步加固：新增红线/赛区/检索纪律短语校验、`URL_ONLY`+`SNAPSHOT+HASH` 证据分层校验、阶段 skill 落地校验（`STAGE_RULE_LINKS`），并校验 `rules-2026.md` 第七节内嵌哈希与实际 PDF 一致（此前只校验脚本内常量，改 PDF 忘改表格会静默放行）。三项新校验均已做负向测试确认能 FAIL。

## 已内置

- Claim 分段、来源层级、`strong/partial/background/limiting/metadata-only` 支撑判定。
- Raw/processed/figure source/model output 到 C/R/S/F-id 的文件与哈希映射。
- Figure contract、单后端纪律、面板证据层级、统计/source data、矢量导出和视觉 QA。
- 唯一 `MCM_SOURCE_MODEL.yaml`、读者路径、摘要、语言边界、DOCX/PPTX 规格与 officecli 回读。
- 真实评委/导师反馈的保真拆分、动作映射和证据闭环。

## 2026-08-03 工程修复（均经实测复现与回归）

- `run_all.py`：`numpy` 改为延迟导入。此前顶层 `import numpy` 会让**纯记账的 `--confirm` 也无法运行**；清环境复现时若模型根本没用到 numpy 而 `requirements.txt` 漏装，T8 复现 Gate 会失败在与模型无关的 ImportError 上。缺 numpy 时降级为只固定 `random` 种子并打印复现性警告。
- `run_all.py`：`time` 拆为 `computed_at` / `verified_at`。此前 `--confirm` 会用核验时刻**覆盖原始计算时间戳**，使 `RESULTS.md` 的"时间"列语义从"这个数何时算出"漂移为"何时核对"，与反幻觉铁律第 1 条要求的时间戳追溯冲突。`workspace-templates.md` 的表结构同步更新。
- `run_all.py`：`--problem N` 指向不存在的入口时给出可读报错（此前抛裸 `ModuleNotFoundError` 栈）；`--all` 找不到 `src/` 时提示先 `cd` 到支撑包根目录。
- `paper-templates.md`：支撑材料 README 的复现命令补 `cd <解压目录>`。入口按相对路径查找 `src/`，评委在解压目录之外执行会报"未发现 src/p1.py"——看起来像代码没交全，而这正对应格式规范第五条的取消资格红线。`adversarial-gates.md` 的复现脚本本就有 `cd`，两处此前不一致。
- `README.md`：校验命令去掉硬编码的 `/home/user/...` 绝对路径（改用 `${CODEX_HOME:-$HOME/.codex}` 并在缺失时跳过），`sha256sum` 补 macOS 的 `shasum -a 256` 回退。
- `GROUP.yaml`：仓库 URL 修正（此前尾部多一个 `-`）。
- 前沿方法的 8 条使用纪律与选卡索引表此前在 `methods-atlas.md` 第五节和 `frontier-cards.md` 第 0 节**逐字重复**，改一处忘另一处即不一致。现改为单点维护：纪律以 `frontier-cards.md` 为准（atlas 只留三条最易踩的红线摘要 + 指针），选卡索引以 `methods-atlas.md` 为准（cards 改为指回）。

## 上线后验证债

静态校验只能证明结构、自包含路由和元数据正确，不能证明：

- 内置 Nature 流程不会在 74 小时内造成不成比例的负担。
- 不同数学家族都能从 figure/source/SourceModel 合同获益。
- 触发边界不会让 T0-T8 同时加载过多上下文。
- 人类 H-001 至 H-005 的实际干扰成本可接受。

本次晋升不吸收未晋升的 v1.8 deliverable-ledger 变更。`GROUP.yaml` 登记的前向 Gate、人工审查和耗时审计必须继续记录；未完成前不得宣称 v2.4 已取得跨新题完整行为验证。
