# MCM For Gold

面向数学建模竞赛的分阶段 Codex skill 仓库。当前架构为一个总控和九个阶段专家，并将 Nature 风格的证据、数据、科学图表、写作、Office 与反馈闭环直接内置到 skill 群中。

本项目与 Nature Portfolio 无官方关联。“Nature”表示高影响力科学传播中的论证与质量控制方法，赛事规则、题面和科学正确性始终优先。

## Skill 群

| Skill | 阶段 | 专长 |
|---|---|---|
| `mcm-gold` | 总控 | CONFIG、时钟、状态、证据台账、阶段路由和人类签署 |
| `mcm-gold-t0-prepare` | T0 | 规则、环境、模板、最小复现和内置 Nature 能力预检 |
| `mcm-gold-t1-select` | T1 | 读题、中心交付、证据风险和选题 |
| `mcm-gold-t2-formalize` | T2 | 调研、claim 支撑分级、形式化和路线 |
| `mcm-gold-t3-audit-data` | T3 | 数据审计、无泄漏清洗和 claim-to-file 映射 |
| `mcm-gold-t4-baseline` | T4 | 第一问基线、求解证据和首张科学主图 |
| `mcm-gold-t5-solve` | T5 | 主模型、求解、创新对照和证据化图表 |
| `mcm-gold-t6-validate` | T6 | 六类检验、红队和主图证据审计 |
| `mcm-gold-t7-write` | T7 | SourceModel、论文、图表、DOCX/PPTX 和 H-004 |
| `mcm-gold-t8-submit` | T8 | 清环境复现、内置 Nature 闭环、终检和 H-005 |

## 内置 Nature 能力

运行时不调用额外 `nature-*` skill。共享能力位于 `skills/mcm-gold/references/`：

- `nature-evidence-data.md`
- `nature-figures.md`
- `nature-writing-office.md`
- `nature-feedback.md`
- `nature-integrated-playbook.md`

## 可引用书目库

`skills/mcm-gold/references/literature-library.md` 收录五大方法族的经典方法出处
（60 条，经 Crossref 逐条核验）与 30 篇本地全文清单。它服务于反幻觉铁律第 3 条：
参考文献必须真实可访问，宁可少引不可编引。前沿方法的出处仍在 `frontier-cards.md` 源列。
全文 PDF 不随仓库分发，默认置于训练区 `research/papers/`，由 T0 赛前预置。

阶段 skill 只读取本阶段需要的参考文件。优先级为：赛事规则与题面 > MCM 科学 Gate > 内置 Nature 质量规范 > 视觉风格。

## 安装布局

十个目录必须保持同级关系，因为阶段专家通过相对路径读取总控的共享参考与模板：

```text
${CODEX_HOME:-$HOME/.codex}/skills/
  mcm-gold/
  mcm-gold-t0-prepare/
  ...
  mcm-gold-t8-submit/
```

当前版本仍是候选，不应直接覆盖 live skill。先完成 `CANDIDATE_STATUS.md` 中的跨题验证和人工审查。

## 2026 官方规则快照

用户提供的三份 2026 细则按内容重命名后保存在 `sources/official/2026/`，PDF 字节未改写，并由 `SOURCE_PDFS.sha256` 单独锁定：参赛规则、AI 工具使用规定、论文格式规范。可执行摘要在 `skills/mcm-gold/references/rules-2026.md`；摘要不替代原文，争议条款必须回查 PDF。

当前候选已把新 AI 声明、固定详情文件名、人工核验责任和论文/支撑材料格式同步到 T7、T8、模板与 Gate。开赛前 24 小时仍须重新核验官网最新发布，发现冲突时以届时官方原文为准。

## 许可边界

仓库原创代码、skill 指令、模板和文档采用 MIT License。`sources/official/2026/`
中的官方规则 PDF 是第三方原文快照，**不在 MIT 授权范围内**；权利仍归原权利人。
具体说明见 `THIRD_PARTY_NOTICES.md`。再次分发这些 PDF 前须核验官方条款；不能确认
转载许可时，应移除 PDF，只保留官方链接与预期哈希，并将快照校验标为不可用。

## 校验

```bash
# 1. 单个 skill 的元数据校验（需要本机装有 skill-creator；路径随 Agent 而变，故用变量）
SKILL_CREATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
if [ -f "$SKILL_CREATOR" ]; then
  for dir in skills/mcm-gold*; do python3 "$SKILL_CREATOR" "$dir"; done
else
  echo "跳过 quick_validate：未找到 $SKILL_CREATOR"
fi

# 2. 本仓库自带的群组校验（无外部依赖，任何平台都应通过）
python3 tooling/validate_skill_group.py

# 3. 自动化回归测试
python3 -m unittest discover -s tests -v

# 4. 清单校验（Linux 用 sha256sum，macOS 用 shasum -a 256）
command -v sha256sum >/dev/null && sha256sum -c MANIFEST.sha256 || shasum -a 256 -c MANIFEST.sha256

# 重建清单时基于版本控制内容，不要用文件系统遍历——否则 .DS_Store / __pycache__
# 这类被 .gitignore 忽略的产物会混进清单，使其随开发机环境漂移
git ls-files | grep -v '^MANIFEST.sha256$' | LC_ALL=C sort -f | xargs shasum -a 256 > MANIFEST.sha256
```

`tests/trigger_cases.json` 是前向触发评估样本，不是静态校验通过的替代品。晋升前须在
实际 Codex 环境逐条运行，记录目标 skill 是否唯一触发、兄弟 skill 是否正确交接以及
上下文负担；未经这一步不得宣称阶段路由已完成行为验证。
