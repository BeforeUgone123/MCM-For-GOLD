#!/usr/bin/env python3
"""按 adversarial-gates.md 五、建立交付物分层目录，并做提交前的物理校验。

存在的理由：那一节只用文本描述了 submission/staging/print/archive 四层结构，
既没有脚本也没有机检。2025A 演练的实测结果是——四个目录一个都没建，产物平铺在
deliverables/ 下，终检清单里的路径全部落空，而没有任何检查发现这一点。
文档描述的结构如果既不能执行也不被校验，它就不会存在。

同时修掉一个实测缺陷：用系统 zip 打包含中文名的文件时，未设 UTF-8 标志位，
评委解压会看到「AI 工�?�使�?�详�??.pdf」这样的乱码。Python zipfile 对非 ASCII
文件名会自动置 bit 11，故本脚本重新打包而不是沿用既有 zip。

幂等：重复运行只覆盖生成物，不触碰源文件。冻结件一律复制，不移动。

用法：
    python3 build_deliverables.py \\
        --workspace MCM-Result \\
        --submission-pdf MCM-Result/Paper-Outputs/paper/main_submission.pdf \\
        --support-src MCM-Result/Paper-Outputs/deliverables/_support_src \\
        --print-pdf MCM-Result/Paper-Outputs/paper/main.pdf \\
        --extra MCM-Result/Paper-Outputs/deliverables/result1.xlsx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB，规则规定的单文件上限
# 不进 support.zip 的噪声：编译中间件与系统产物。列表保守，宁可多带也不误删证据。
EXCLUDE_NAMES = {".DS_Store", "__pycache__", ".ipynb_checkpoints"}
EXCLUDE_SUFFIXES = {".aux", ".log", ".out", ".toc", ".synctex.gz", ".pyc"}
# 台账类文件归 archive/，不随提交包上传。
ARCHIVE_PATTERNS = (
    "STATE.md", "DECISIONS.md", "RESULTS.md", "RISKS.md", "SOURCES.md",
    "HUMAN_SIGNOFFS.md", "AI_USAGE.md", "SKILL_USAGE.md", "FREEZE_CHANGE_LOG.md",
)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_noise(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES or path.name.startswith("._"):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_NAMES for part in path.parts)


def visible_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and not is_noise(path.relative_to(root))
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--workspace", type=Path, default=Path("MCM-Result"))
    parser.add_argument("--submission-pdf", type=Path, required=True,
                        help="提交版论文，首页须为摘要页")
    parser.add_argument("--support-src", type=Path, required=True,
                        help="支撑材料源目录：README、requirements、run_all.py、src/、data/、figures/、intermediate/ 等")
    parser.add_argument("--print-pdf", type=Path, default=None,
                        help="纸质版（含承诺书与编号页）；缺省时 print/ 留空并记 warning")
    parser.add_argument("--extra", type=Path, nargs="*", default=[],
                        help="额外随支撑包提交的文件，如 result1.xlsx")
    parser.add_argument("--archive-src", type=Path, nargs="*", default=[],
                        help="台账目录；其中的过程文件复制进 archive/，不进提交包")
    parser.add_argument("--output", type=Path, default=None, help="清单 JSON 落盘路径")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    root = args.workspace / "Paper-Outputs" / "deliverables"

    if not args.submission_pdf.is_file():
        errors.append(f"SUBMISSION_PDF_MISSING 提交版不存在：{args.submission_pdf}")
    if not args.support_src.is_dir():
        errors.append(f"SUPPORT_SRC_MISSING 支撑材料源目录不存在：{args.support_src}")
    if errors:
        emit({"status": "FAIL", "errors": errors, "warnings": warnings}, args.output)
        return 1

    submission = root / "submission"
    staging = root / "staging" / "support"
    print_dir = root / "print"
    archive = root / "archive"
    for directory in (submission, staging, print_dir, archive):
        directory.mkdir(parents=True, exist_ok=True)

    # --- staging/support：重建为源目录的干净副本 ---
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    copied = 0
    for path in visible_files(args.support_src):
        target = staging / path.relative_to(args.support_src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    for extra in args.extra:
        if not extra.is_file():
            warnings.append(f"EXTRA_MISSING 跳过不存在的附加文件：{extra}")
            continue
        shutil.copy2(extra, staging / extra.name)
        copied += 1

    # --- submission/：论文 + 支撑包 ---
    paper_target = submission / "paper.pdf"
    shutil.copy2(args.submission_pdf, paper_target)

    zip_target = submission / "support.zip"
    if zip_target.exists():
        zip_target.unlink()
    files = visible_files(staging)
    with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive_zip:
        for path in files:
            # arcname 传 str 而非 bytes，zipfile 遇非 ASCII 会置 UTF-8 flag，
            # 评委在 Windows 解压不再乱码。
            archive_zip.write(path, path.relative_to(staging).as_posix())

    # --- print/ ---
    if args.print_pdf is not None and args.print_pdf.is_file():
        shutil.copy2(args.print_pdf, print_dir / "paper_print.pdf")
    else:
        warnings.append(
            "PRINT_PDF_ABSENT print/paper_print.pdf 未生成；纸质版须含承诺书与编号页，"
            "提交前必须补齐"
        )

    # --- archive/：台账，不提交 ---
    archived = 0
    for source in args.archive_src:
        if not source.is_dir():
            warnings.append(f"ARCHIVE_SRC_MISSING 跳过：{source}")
            continue
        for pattern in ARCHIVE_PATTERNS:
            for path in source.rglob(pattern):
                if path.is_file():
                    shutil.copy2(path, archive / path.name)
                    archived += 1

    # --- 物理校验 ---
    sizes = {}
    for label, path in (("paper.pdf", paper_target), ("support.zip", zip_target)):
        size = path.stat().st_size
        sizes[label] = size
        if size > SIZE_LIMIT:
            errors.append(
                f"SIZE_LIMIT_EXCEEDED {label} {size} bytes > {SIZE_LIMIT}；须压缩或移出非必要内容"
            )
    if not files:
        errors.append("SUPPORT_EMPTY staging/support 为空，支撑包不能只有壳")

    report = {
        "schema_version": 1,
        "status": "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS"),
        "root": str(root),
        "submission": {
            "paper.pdf": {"bytes": sizes.get("paper.pdf"), "sha256": sha256_of(paper_target)},
            "support.zip": {
                "bytes": sizes.get("support.zip"),
                "sha256": sha256_of(zip_target),
                "entries": len(files),
            },
        },
        "staging_files": copied,
        "archive_files": archived,
        "print_ready": (print_dir / "paper_print.pdf").is_file(),
        "errors": errors,
        "warnings": warnings,
    }
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
