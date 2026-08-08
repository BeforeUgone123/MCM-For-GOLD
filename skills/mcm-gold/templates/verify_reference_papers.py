#!/usr/bin/env python3
"""校验文献库三者一致：literature-library.md 的声明、MANIFEST.sha256、papers/ 实际文件。

存在的理由：`literature-library.md` 的 `✔`（本地有全文可核对细节）与「本地全文清单」
此前没有任何机检，可以随手标而无人发现。2026-08-08 审查实测：该表声明 30 篇本地全文、
11 个条目标 `✔`，而 `papers/` 目录当时根本不存在——一篇也没有。本脚本把这类声明变成
可证伪的断言。

设计约束（避免制造假门禁）：
- 只检查**能被证伪的事实**：文件在不在、哈希对不对、被声明的条目有没有对应文件。
  不试图判断"这篇文献读没读过"——那不是脚本能知道的，硬查只会产出"已核验"的假象。
- "没查"与"查了没问题"在输出里必须不同：跳过时相关计数写 null 而非 0。
- 退出码 1 只对应真实不一致；环境性缺失（未预置）用独立状态码表达，由调用方决定是否阻断。

用法：
    # T0 预置后验收（默认路径按工作区约定解析）
    python3 verify_reference_papers.py --workspace MCM-Result

    # 显式指定
    python3 verify_reference_papers.py \
        --papers-root MCM-Result/Reference-Papers/papers \
        --library <skills-root>/mcm-gold/references/literature-library.md \
        --output MCM-Result/Review-Results/T0_LIBRARY_CHECK.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def first_author_surname(authors: str) -> str | None:
    """'William Ogilvy Kermack; A. G. McKendrick' -> 'kermack'"""
    first = authors.split(";")[0].strip()
    if not first:
        return None
    parts = [p for p in re.split(r"\s+", first) if p]
    while parts and parts[-1].lower().strip(".,") in SUFFIXES:
        parts.pop()
    if not parts:
        return None
    return re.sub(r"[^a-z]", "", parts[-1].lower()) or None


def parse_library(text: str) -> dict:
    """抽出两类断言：A-E 族表格里标 ✔ 的条目，以及「本地全文清单」里的文件名。"""
    fulltext_claims = []   # 标了 ✔ 的书目条目
    listed_files = []      # 清单里声明应存在的文件
    waived_files = []      # 清单里以删除线显式标注为「未获得」的文件

    in_list_section = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("## "):
            in_list_section = "本地全文清单" in line
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]

        if in_list_section:
            m = re.search(r"`([^`]+\.pdf)`", cells[0]) if cells else None
            if m:
                (waived_files if "~~" in cells[0] else listed_files).append(
                    {"filename": m.group(1), "line": lineno,
                     "note": cells[1] if len(cells) > 1 else ""}
                )
            continue

        # A-E 族书目表：末列为全文标记，列数固定为 7
        if len(cells) == 7 and cells[-1] in {"✔", "✓"}:
            surname = first_author_surname(cells[2])
            year = cells[3].strip()
            if surname and re.fullmatch(r"\d{4}", year):
                fulltext_claims.append(
                    {"line": lineno, "title": cells[1], "year": year,
                     "surname": surname, "expect_prefix": f"{year}-{surname}"}
                )
    return {"fulltext_claims": fulltext_claims,
            "listed_files": listed_files,
            "waived_files": waived_files}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=Path, default=Path("MCM-Result"),
                    help="任务工作区根，用于推导 Reference-Papers/papers（默认 MCM-Result）")
    ap.add_argument("--papers-root", type=Path, default=None,
                    help="显式指定全文目录，优先于 --workspace")
    ap.add_argument("--library", type=Path, default=None,
                    help="literature-library.md 路径；默认取本脚本同级的 ../references/literature-library.md")
    ap.add_argument("--output", type=Path, default=None, help="结果 JSON 落盘路径")
    args = ap.parse_args()

    papers = args.papers_root or (args.workspace / "Reference-Papers" / "papers")
    library = args.library or (Path(__file__).resolve().parent.parent
                               / "references" / "literature-library.md")

    errors: list[str] = []
    warnings: list[str] = []
    report = {
        "schema_version": 1,
        "papers_root": str(papers),
        "library": str(library),
        "status": None,
        "manifest_check": None,
        "listed_files_check": None,
        "fulltext_claims_check": None,
        "errors": errors,
        "warnings": warnings,
    }

    # --- 库文件本身 ---
    if not library.is_file():
        errors.append(f"LIBRARY_UNREADABLE 读不到 {library}")
        report["status"] = "LIBRARY_UNREADABLE"
        emit(report, args.output)
        return 1
    parsed = parse_library(library.read_text(encoding="utf-8"))

    # --- 全文目录 ---
    if not papers.is_dir():
        errors.append(
            f"NOT_PROVISIONED 全文目录不存在：{papers}。"
            f"库中仍声明 {len(parsed['listed_files'])} 篇本地全文、"
            f"{len(parsed['fulltext_claims'])} 个条目标 ✔——这些声明当前全部无据。"
            " T0 应执行文献库预置，或把库中相应标记改为空白。"
        )
        report["status"] = "NOT_PROVISIONED"
        emit(report, args.output)
        return 1

    on_disk = {p.name: p for p in papers.iterdir() if p.suffix.lower() == ".pdf"}

    # --- MANIFEST 比对 ---
    manifest_path = papers / "MANIFEST.sha256"
    if not manifest_path.is_file():
        errors.append(f"MANIFEST_MISSING 缺 {manifest_path}，全文未被哈希锁定")
        report["manifest_check"] = {"status": "MISSING", "matched": None,
                                    "mismatched": None, "missing": None, "untracked": None}
    else:
        recorded: dict[str, str] = {}
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            digest, _, name = line.partition("  ")
            if digest and name:
                recorded[Path(name.strip()).name] = digest.strip().lower()
        matched, mismatched, missing = [], [], []
        for name, digest in sorted(recorded.items()):
            path = on_disk.get(name)
            if path is None:
                missing.append(name)
                continue
            actual = sha256_of(path)
            (matched if actual == digest else mismatched).append(name)
        untracked = sorted(set(on_disk) - set(recorded))
        if mismatched:
            errors.append(f"MANIFEST_HASH_MISMATCH 内容与记录不符：{', '.join(mismatched)}")
        if missing:
            errors.append(f"MANIFEST_FILE_MISSING 记录在册但文件不存在：{', '.join(missing)}")
        if untracked:
            warnings.append(f"MANIFEST_UNTRACKED 目录中有未入册文件：{', '.join(untracked)}")
        report["manifest_check"] = {
            "status": "CHECKED", "matched": len(matched), "mismatched": mismatched,
            "missing": missing, "untracked": untracked,
        }

    # --- 清单声明 vs 磁盘 ---
    listed_missing = [e["filename"] for e in parsed["listed_files"]
                      if e["filename"] not in on_disk]
    if listed_missing:
        errors.append(
            "LIBRARY_FULLTEXT_MISSING 清单声明存在但磁盘上没有："
            + ", ".join(listed_missing)
            + "。要么补齐文件，要么在清单里按 ~~文件名~~ 标注为未获得并写明原因。"
        )
    waived_present = [e["filename"] for e in parsed["waived_files"]
                      if e["filename"] in on_disk]
    if waived_present:
        warnings.append(f"LIBRARY_WAIVED_BUT_PRESENT 已标注未获得却存在于磁盘：{', '.join(waived_present)}")
    report["listed_files_check"] = {
        "status": "CHECKED", "listed": len(parsed["listed_files"]),
        "present": len(parsed["listed_files"]) - len(listed_missing),
        "missing": listed_missing,
        "waived": [e["filename"] for e in parsed["waived_files"]],
    }

    # --- ✔ 标记 vs 磁盘 ---
    unbacked, backed, unresolved = [], [], []
    for claim in parsed["fulltext_claims"]:
        hits = [n for n in on_disk if n.lower().startswith(claim["expect_prefix"])]
        if hits:
            backed.append({"line": claim["line"], "title": claim["title"], "file": hits[0]})
        else:
            # 年份+姓氏前缀匹配不到：可能是文件命名不合约定，而非标记造假。
            # 只有当该年份下没有任何文件时才判定为无据，否则留给人工——
            # 宁可漏报也不误判，误判会诱使人去改标记而不是改命名。
            same_year = [n for n in on_disk if n.startswith(claim["year"] + "-")]
            (unresolved if same_year else unbacked).append(
                {"line": claim["line"], "title": claim["title"],
                 "expect_prefix": claim["expect_prefix"],
                 "same_year_files": same_year}
            )
    if unbacked:
        errors.append(
            "LIBRARY_FULLTEXT_CLAIM_UNBACKED 标了 ✔ 但磁盘上没有对应全文："
            + "; ".join(f"L{c['line']} {c['title']}（期望前缀 {c['expect_prefix']}-*）"
                        for c in unbacked)
            + "。✔ 表示可核对全文细节，无文件而标 ✔ 属于伪造证据。"
        )
    if unresolved:
        warnings.append(
            "LIBRARY_FULLTEXT_CLAIM_UNRESOLVED 标了 ✔ 且该年份有文件，但文件名不符"
            " `<年份>-<第一作者姓氏>-*.pdf` 约定，无法自动核对，需人工确认："
            + "; ".join(f"L{c['line']} {c['title']} → {c['same_year_files']}"
                        for c in unresolved)
        )
    report["fulltext_claims_check"] = {
        "status": "CHECKED", "claims": len(parsed["fulltext_claims"]),
        "backed": len(backed), "unbacked": unbacked, "unresolved": unresolved,
    }

    report["status"] = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    emit(report, args.output)
    return 1 if errors else 0


def emit(report: dict, output: Path | None) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    sys.exit(main())
