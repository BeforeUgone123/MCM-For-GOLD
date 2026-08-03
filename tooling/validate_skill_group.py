#!/usr/bin/env python3
"""Validate the MCM stage skill repository and embedded Nature integration."""

from __future__ import annotations

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
    names: set[str] = set()

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
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("FAIL")
        for problem in problems:
            print(f"- {problem}")
        sys.exit(1)
    print(
        f"PASS: {len(EXPECTED)} skills, routes, metadata, links, and embedded Nature modules are consistent"
    )
