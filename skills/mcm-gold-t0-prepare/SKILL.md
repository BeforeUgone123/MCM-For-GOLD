---
name: mcm-gold-t0-prepare
description: 数学建模竞赛 T0 赛前准备专家。用于核验最新赛事规则，固化 Python/R/LaTeX/Word 环境与内置 Nature 绘图/Office 能力，准备模板、匿名与 AI 披露基线，执行近年真题演练并验证 30 分钟最小可复现闭环。用户提到赛前准备、环境检查、工具链、模板、演练、规则包或 T0 Gate 时使用。
---

# T0 赛前准备

**安装依赖**：本 skill 与 `mcm-gold` **必须同级安装**（`skills/mcm-gold/` 与 `skills/mcm-gold-t0-prepare/` … `skills/mcm-gold-t8-submit/` 并列在同一目录）。下文全部 `../mcm-gold/…` 的必读文档、模板脚本与 Gate 引用都按这个布局解析：只装本阶段、或改动目录层级时，这些链接会一次性全断，必读门禁与机检随之全部失效。缺同级 `mcm-gold` 时先补齐再执行，不要绕过引用继续跑。

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[赛事规则](../mcm-gold/references/rules-2026.md)、[训练协议](../mcm-gold/references/training-protocol.md)和[内置 Nature 总则](../mcm-gold/references/nature-integrated-playbook.md)。本阶段只建立可靠起点，不提前替正式赛题选择路线。

## 必需输入

- 赛事名称、组别、起止时间、目标奖项和官方规则入口。
- 计划使用的语言、求解器、论文格式、联网条件与设备限制。
- 绝对 `result_root` 与 `state_dir`；缺失时先用总控初始化 `MCM-Result/` 七目录。

## 执行

1. 从官方来源重新核验规则、页数、文件大小、匿名、支撑材料、AI 披露和提交窗口。距查证日超过 30 天或规则已更新时，不沿用旧摘要。
2. 逐条重核[规则包](../mcm-gold/references/rules-2026.md)第一节标为 `URL_ONLY` 的事实——**比赛起止时间、报名截止、相似度红线、报送比例**在仓库内没有快照和哈希，且评阅规范仍是上一届版本。CONFIG 的 `start_time`/`end_time` 直接决定 74 小时状态机，核对后写 S-id 再固化；核不到就标 `UNCONFIRMED` 并阻断 live 模式，不得沿用本表默认值开钟。
3. **查证本赛区附加要求**：格式规范第八条允许"各赛区可以对论文做相应的要求"，官方无统一入口，须从本校教务或赛区组委会渠道获取。查到的附加要求写入 CONFIG 与终检清单并记 S-id；确认无附加要求时同样记录查证渠道与时间，不得默认"只有全国级规则"。
4. 运行共享的 [`env_check.sh`](../mcm-gold/templates/env_check.sh)，把实际输出保存到 `MCM-Result/Intermediate-Outputs/logs/`，并记录版本、缺包、字体、LaTeX、Office、求解器和联网能力。
5. 固定依赖、随机种子、编码、时区和字体；用最小依赖集而非临时堆包。缺工具时选择可维护降级路线并写 `RISKS.md`。
6. 准备论文骨架、图表样式、引用方式、代码入口和状态台账。使用 [`paper-templates.md`](../mcm-gold/templates/paper-templates.md)、[`workspace-templates.md`](../mcm-gold/templates/workspace-templates.md)与 [`run_all.py`](../mcm-gold/templates/run_all.py)。
7. 建立匿名基线扫描：作者字段、PDF 元数据、代码路径、图片 EXIF、工作簿属性和压缩包文件名。
7b. **同机有别的题目工作区时，登记本题专属词**：跑 `verify_output_layout.py --workspace MCM-Result --suggest-topic-terms` 拿候选，删掉「文件」「网络」「位置」这类通用词，把剩下的五六个题目名词存成 `MCM-Result/Competition-Materials/TOPIC_TERMS.txt`（一行一个）。读赛题时顺手就做完了，换来的是 `FOREIGN_TOPIC_CONTENT` 能拦住跨工作区串题——shell 的 cwd 跨命令持久，实测发生过一整节内容写进隔壁题目的论文并连带重编译，路径与结构全部合法、无一检查报警。词表必须人确认：自动指纹试过三种，误报都高到会训练人忽略警告。
8. 选最近三年中的至少一道历年题做 rehearsal。先冻结题面和输入，再记录真实墙钟；读取同题讲评或展示论文前结束 holdout。
9. 在 30 分钟时间盒内完成“读数据 -> 最小模型 -> 结果图 -> PDF -> 支撑包重跑”的烟雾测试。烟雾测试 MUST 在**全新目录 + 全新虚拟环境**下按支撑包 README 原文执行，验证的是"评委照说明能跑通"，不是"我们自己的机器能跑通"。
10. 固化内置 Nature 工具链：确认 Python/R 绘图运行时、SVG/PDF 可编辑文本、字体回退、最终尺寸预览和矢量回读；`paper_format=word` 时同时实测 `officecli validate/view`。
11. 不在 T0 替用户选择绘图后端。已有明确单语言工作流时记录；否则标 `UNCONFIRMED`，留到第一张正文图前只问“Python 还是 R？”。
12. **预置文献库全文**。**先查同机有没有既有工作区已经备好的库**——兄弟工作区（`MCM-Result-2025B/` 这类）的 `Reference-Papers/papers/` 若带 `MANIFEST.sha256`，整目录复制再核哈希只要几分钟，而逐篇联网取证要数小时；网络受限时它还是唯一可行路径：

    ```bash
    cp -R <既有工作区>/Reference-Papers/papers MCM-Result/Reference-Papers/
    cd MCM-Result/Reference-Papers/papers && shasum -a 256 -c MANIFEST.sha256 | grep -v ': OK$'   # 无输出 = 逐篇字节一致
    ```

    任何一行不是 `OK` 就**不要将就**：那一篇已损坏或被改过，按下面的流程单独重取。`ACQUISITION_LOG.md` 一起复制——它记的是取证过程，不随工作区变化。复制完仍要跑本条末尾的 `verify_reference_papers.py`：它比对本工作区的书目表 `✔`、清单声明、磁盘实际与哈希四者，**复制不豁免验收**（复制来的库也可能缺本届书目表新增的条目）。

    没有可复制的既有库时，逐篇获取：[可引用书目](../mcm-gold/references/literature-library.md)的「本地全文清单」逐条落到 `MCM-Result/Reference-Papers/papers/`——竞赛期间禁入域名收紧、网络不可靠，赛前不备赛中就没有。取文件只走 arXiv、出版社与学会开放页、机构知识库、大学/研究所官方域名的作者自存档；**先用 Crossref/arXiv/Unpaywall 核验书目真实存在，再找全文**；每篇下载后用 `pdftotext` 首页逐字核对标题/作者/年份/卷期页，文本层缺失的用 `pdftoppm` 渲染读图确认。取不到合法开放全文的**标 `~~文件名~~` 并写明原因，不下载非授权转载**。落盘后生成 `MANIFEST.sha256` 与 `ACQUISITION_LOG.md`（逐篇记来源 URL、版本性质、取证过程），再跑验收：

    ```bash
    python3 <skills-root>/mcm-gold/templates/verify_reference_papers.py \
        --workspace MCM-Result --output MCM-Result/Review-Results/T0_LIBRARY_CHECK.json
    ```

    该脚本比对「书目表 `✔` 标记 / 清单声明 / 磁盘实际 / MANIFEST 哈希」四者，任一不一致即非零退出。**注意作者自存档的接受稿页码与刊载页码不一致**，此类条目在 `ACQUISITION_LOG.md` 标注版本性质，引用时只能用 DOI 与卷期页。

## 产物

- `MCM-Result/Review-Results/T0_READINESS.md`：规则查证、工具版本、缺口、降级路线与负责人。
- `MCM-Result/Intermediate-Outputs/logs/env_check_<timestamp>.txt`：环境检查原始输出。
- `MCM-Result/Data-Scripts/environment/`：依赖锁定、版本清单和安装说明。
- `MCM-Result/Intermediate-Outputs/smoke/`：最小闭环的中间结果与重跑日志；代码、图和 PDF 分别归入对应固定目录。
- `MCM-Result/Intermediate-Outputs/REHEARSAL_RECORD.md`：题目、污染边界、真实耗时、失败与时间盒校准。
- `MCM-Result/Review-Results/T0_NATURE_READINESS.md`：绘图后端状态、矢量导出、字体、Office 回读和降级路线。
- `MCM-Result/Reference-Papers/papers/`：文献库本地全文 + `MANIFEST.sha256` + `ACQUISITION_LOG.md`。
- `MCM-Result/Review-Results/T0_LIBRARY_CHECK.json`：`verify_reference_papers.py` 的验收输出。

每个外部规则事实写 S-id，每个实际 smoke 结果写 R-id。不要把“命令存在”当作“已运行”。

## 独立 Review

冻结 T0 产物后，由不同上下文 reviewer 按契约的通用 30 分与 T0 专属 70 分评分，逐条核验 `T0-G1` 至 `T0-G4`。产出者只做自检；正式 R1、按条件触发的 R2 和 FINAL 三件套均写入 `MCM-Result/Review-Results/`，并通过 `verify_stage_review.py` 后方可进入 Gate。

## Gate

仅在以下条件全部满足时返回 `PASS`：

- 规则包来自当前官方页面并记录查证时间；第一节 `URL_ONLY` 事实（尤其比赛起止时间）已逐条重核并写 S-id。
- **本赛区附加要求已查证**（有则登记并进终检清单，无则记录查证渠道与时间）。
- 30 分钟内从干净起点生成可打开 PDF，关键数值能从 `run_all` 重跑。
- 中文字体、论文编译、求解器、匿名扫描和 AI 披露路径均有实际测试。
- 内置 Nature 的绘图/导出/Office 适用能力已实测或明确标为 N/A/UNCONFIRMED，不假设可用。
- **文献库全文已预置且通过 `verify_reference_papers.py`**（退出码 0）；未获得的条目已在库中标 `~~文件名~~` 并写明原因。库里标 `✔` 而磁盘无文件属伪造证据，直接判 FAIL。
- 当前缺口有明确、低脆弱性的降级方案。

未联网时设置 `research.online=false` 并返回限制；不得编造规则或来源。把 T1 所需题面入口、工具限制和剩余风险写入 `[HANDOFF T0]`。
