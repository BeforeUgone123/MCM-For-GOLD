#!/usr/bin/env python3
"""Validate the MCM stage skill repository and embedded Nature integration."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
EXPECTED = [
    "mcm-gold",
    "mcm-gold-t0-prepare",
    "mcm-gold-t1-select",
    "mcm-gold-t2-formalize",
    "mcm-gold-t3-audit-data",
    "mcm-gold-t4-baseline",
    "mcm-gold-t5-solve",
    "mcm-gold-t6-validate",
    "mcm-gold-t7-write",
    "mcm-gold-t8-submit",
]
NATURE_MODULES = [
    "nature-integrated-playbook.md",
    "nature-evidence-data.md",
    "nature-figures.md",
    "nature-writing-office.md",
    "nature-feedback.md",
]
STAGE_NATURE_LINKS = {
    "mcm-gold-t0-prepare": ["nature-integrated-playbook.md"],
    "mcm-gold-t1-select": ["nature-integrated-playbook.md"],
    "mcm-gold-t2-formalize": ["nature-evidence-data.md"],
    "mcm-gold-t3-audit-data": ["nature-evidence-data.md"],
    "mcm-gold-t4-baseline": ["nature-figures.md"],
    "mcm-gold-t5-solve": ["nature-figures.md"],
    "mcm-gold-t6-validate": ["nature-figures.md"],
    "mcm-gold-t7-write": [
        "nature-evidence-data.md",
        "nature-figures.md",
        "nature-writing-office.md",
    ],
    "mcm-gold-t8-submit": [
        "nature-integrated-playbook.md",
        "nature-writing-office.md",
        "nature-feedback.md",
    ],
}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_NATURE_RE = re.compile(r"\$nature-|/skills/nature-|nature_adapter")
OFFICIAL_PDFS = {
    "cumcm-participation-rules-2026.pdf": "46d3837906bfd7049eb04c40cfc8b8436912d7edae98462ba064abfa381a8d3a",
    "cumcm-ai-tool-policy-2026.pdf": "4cf6f30cdd37d6ef2cdb3439c5dba4d9f207c12d6aafe24419e81f3c69acf59a",
    "cumcm-paper-format-2026.pdf": "cece4bb3a900a0435160032b98ea26e03b0f2d7eca58424b0d023e26085aed26",
}
RULES_REQUIRED = [
    "参考文献之前",
    "本参赛队在竞赛过程中未使用任何 AI 工具。",
    "本参赛队在竞赛过程中使用了 AI 工具，主要用于",
    "AI 工具使用详情.pdf",
    "核心建模与分析由参赛队主导",
    "逐项人工审查与核实",
    # 格式规范原文中三条"可能被取消评奖资格"的红线，以及赛区可另提要求的授权条款。
    # 这些是 T8 复现 Gate 与赛区核验的官方依据，漏收会让终检失去强制力。
    "程序不能运行",
    "运行结果与论文不符",
    "支撑材料文件与论文内容不相符",
    "各赛区可以对论文做相应的要求",
    "附录页数不限",
    # 参赛规则第 5 条点名的平台禁令，必须落成可执行的检索纪律。
    "csdn.net",
    "github.com",
    "检索纪律",
    "live 模式禁止通用网页查重",
    # 未快照事实必须显式标注证据等级，避免与已哈希的官方原文混为一谈。
    "URL_ONLY",
    "SNAPSHOT+HASH",
]
RULES_FORBIDDEN = [
    "cumcm_ai_2025",
    "参考文献之后",
    "正文已标注 + 参考文献已著录",
]
# 阶段 skill 必须真正落地这些要点，否则规则只停在 references 里没人执行。
STAGE_RULE_LINKS = {
    "mcm-gold-t0-prepare": ["URL_ONLY", "赛区"],
    "mcm-gold-t2-formalize": ["检索纪律", "强制域名白名单", "literature-library.md"],
    "mcm-gold-t5-solve": ["非平凡性", "支撑域", "阈值"],
    "mcm-gold-t7-write": ["支撑域", "literature-library.md"],
    "mcm-gold-t8-submit": ["取消资格红线", "赛区"],
}
# 可引用书目库：反幻觉铁律第 3 条要求参考文献真实可访问，书目库是其落地物。
# 校验它存在、含引用纪律，且五大方法族齐全（与 methods-atlas 对齐）。
LITERATURE_REQUIRED = [
    "引用纪律",
    "不代表你读过这篇文献",
    "文献题名",
    "A · 优化与规划",
    "B · 评价与决策",
    "C · 预测与时间序列",
    "D · 分类、聚类与判别",
    "E · 机理建模与仿真",
    "本地全文清单",
]
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
# 方案验收层的四条互相依赖：缺"阈值锁定"时，另三条可被事后调阈值架空，
# 反而产出"已严格验收"的假象。故要求四条同时存在。
ACCEPTANCE_LAYER_REQUIRED = [
    "方案验收层",
    "性能 + 非平凡性 + 支撑域",
    "解读由数值生成",
    "非平凡性",
    "支撑域",
    "阈值锁定",
]


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---\n", 2)
    values: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def validate() -> list[str]:
    errors: list[str] = []
    coordinator = (SKILLS_ROOT / "mcm-gold" / "SKILL.md").read_text(encoding="utf-8")
    rules = (SKILLS_ROOT / "mcm-gold" / "references" / "rules-2026.md").read_text(
        encoding="utf-8"
    )
    names: set[str] = set()

    source_root = REPO_ROOT / "sources" / "official" / "2026"
    for filename, expected_hash in OFFICIAL_PDFS.items():
        path = source_root / filename
        if not path.is_file():
            errors.append(f"missing official 2026 source PDF: {filename}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(
                f"official source hash mismatch: {filename}: {actual_hash} != {expected_hash}"
            )
        # 只校验 OFFICIAL_PDFS 常量的话，换 PDF 时改了常量却忘改 markdown 表格会静默放行
        if expected_hash not in rules:
            errors.append(
                f"rules-2026.md 第七节未登记 {filename} 的实际哈希 {expected_hash}"
            )

    for phrase in RULES_REQUIRED:
        if phrase not in rules:
            errors.append(f"rules-2026.md missing required 2026 policy text: {phrase}")
    for phrase in RULES_FORBIDDEN:
        if phrase in rules:
            errors.append(f"rules-2026.md contains stale policy text: {phrase}")
    if "cumcm_ai_2026_trial" not in coordinator:
        errors.append("coordinator does not select the 2026 trial AI policy")

    gates = (SKILLS_ROOT / "mcm-gold" / "references" / "adversarial-gates.md").read_text(
        encoding="utf-8"
    )
    for phrase in ACCEPTANCE_LAYER_REQUIRED:
        if phrase not in gates:
            errors.append(f"adversarial-gates.md 缺方案验收层要点: {phrase}")

    lit_path = SKILLS_ROOT / "mcm-gold" / "references" / "literature-library.md"
    if not lit_path.is_file():
        errors.append("missing references/literature-library.md")
    else:
        lit = lit_path.read_text(encoding="utf-8")
        for phrase in LITERATURE_REQUIRED:
            if phrase not in lit:
                errors.append(f"literature-library.md 缺要点: {phrase}")
        bibliography = lit.split("## 本地全文清单", 1)[0]
        if "…" in bibliography:
            errors.append("literature-library.md 书目字段含省略号，不能生成完整引用")
        for line_number, line in enumerate(bibliography.splitlines(), start=1):
            if not line.startswith("|") or "`10." not in line:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            doi = cells[-2].strip("`")
            if not DOI_RE.fullmatch(doi):
                errors.append(
                    f"literature-library.md:{line_number} DOI 不完整或不可解析: {doi}"
                )
        if "literature-library.md" not in coordinator:
            errors.append("coordinator 未在共享参考中列出 literature-library.md")

    for module in NATURE_MODULES:
        path = SKILLS_ROOT / "mcm-gold" / "references" / module
        if not path.is_file():
            errors.append(f"missing embedded Nature module: {module}")

    for name in EXPECTED:
        skill_dir = SKILLS_ROOT / name
        skill_file = skill_dir / "SKILL.md"
        agent_file = skill_dir / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"missing skills/{name}/SKILL.md")
            continue
        if not agent_file.is_file():
            errors.append(f"missing skills/{name}/agents/openai.yaml")

        text = skill_file.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if meta.get("name") != name:
            errors.append(f"{name}: frontmatter name mismatch")
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        names.add(name)

        if EXTERNAL_NATURE_RE.search(text):
            errors.append(f"{name}: external Nature skill dependency found")

        if name != "mcm-gold":
            if "../mcm-gold/references/stage-contract.md" not in text:
                errors.append(f"{name}: stage contract not routed")
            if f"${name}" not in coordinator:
                errors.append(f"coordinator does not route ${name}")
            for module in STAGE_NATURE_LINKS[name]:
                if module not in text:
                    errors.append(f"{name}: embedded Nature module not routed: {module}")
            for token in STAGE_RULE_LINKS.get(name, []):
                if token not in text:
                    errors.append(f"{name}: 2026 合规要点未落到阶段 skill: {token}")

        if agent_file.is_file():
            agent_text = agent_file.read_text(encoding="utf-8")
            if f"${name}" not in agent_text:
                errors.append(f"{name}: default_prompt does not mention ${name}")

        for link in LINK_RE.findall(text):
            if link.startswith(("http://", "https://", "#")):
                continue
            target = (skill_dir / link.split("#", 1)[0]).resolve()
            if not target.exists():
                errors.append(f"{name}: broken link {link}")

    shared_files = list((SKILLS_ROOT / "mcm-gold" / "references").glob("*.md"))
    for path in shared_files:
        if EXTERNAL_NATURE_RE.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.name}: external Nature skill dependency found")

    manifest = (REPO_ROOT / "GROUP.yaml").read_text(encoding="utf-8")
    for name in EXPECTED:
        if f'"{name}"' not in manifest:
            errors.append(f"GROUP.yaml missing {name}")
    if "external_nature_skill_dependency: false" not in manifest:
        errors.append("GROUP.yaml does not declare embedded Nature self-containment")

    notice_path = REPO_ROOT / "THIRD_PARTY_NOTICES.md"
    if not notice_path.is_file():
        errors.append("missing THIRD_PARTY_NOTICES.md for official PDF snapshots")
    else:
        notice = notice_path.read_text(encoding="utf-8")
        for phrase in ("sources/official/2026/", "not covered", "rights holders"):
            if phrase not in notice:
                errors.append(f"THIRD_PARTY_NOTICES.md missing licensing boundary: {phrase}")

    trigger_path = REPO_ROOT / "tests" / "trigger_cases.json"
    if not trigger_path.is_file():
        errors.append("missing tests/trigger_cases.json")
    else:
        try:
            trigger_cases = json.loads(trigger_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid tests/trigger_cases.json: {exc}")
        else:
            covered = {case.get("target") for case in trigger_cases if isinstance(case, dict)}
            missing = set(EXPECTED) - covered
            unknown = covered - set(EXPECTED)
            if missing:
                errors.append(f"trigger matrix missing skills: {sorted(missing)}")
            if unknown:
                errors.append(f"trigger matrix contains unknown skills: {sorted(unknown)}")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("FAIL")
        for problem in problems:
            print(f"- {problem}")
        sys.exit(1)
    print(
        f"PASS: {len(EXPECTED)} skills, routes, metadata, links, embedded Nature modules, and 2026 rule sources are consistent"
    )
