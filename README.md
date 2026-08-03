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

## 校验

```bash
for dir in skills/mcm-gold*; do
  python3 /home/user/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$dir"
done
python3 tooling/validate_skill_group.py
sha256sum -c MANIFEST.sha256
```
