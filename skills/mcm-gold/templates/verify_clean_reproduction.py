#!/usr/bin/env python3
"""清环境复现红线的可执行版：解压支撑包 → 建全新 venv → 跑 run_all → 核对数值与写入边界。

存在的理由：格式规范第五条把「缺少必要源程序」「程序不能运行」「运行结果与论文不符」
列为取消资格红线，而此前这三条全靠人工按 README 敲命令，实测漏掉了三类问题：

1. `--all` 只跑了 1/5 的问题（src/ 下只有 p1.py，而 README 与附录都写 p1.py…p5.py），
   9.6 秒打出 [DONE]，看起来像全部复现。→ 本脚本强制传 --expect-problems。
2. 脚本用 `Path(__file__).parents[1]` 定位输出目录，在工作区指向 MCM-Result/，
   在支撑包里却指向**解压目录的父目录**：`import solve_all` 就会在评委的桌面上
   创建 Intermediate-Outputs/logs/。绝对路径检查查不到这种相对路径逃逸。
   → 本脚本对解压目录的父目录做前后快照，越界写入即 error。
3. 依赖装不上、字体缺失一类环境问题，在原机器上永远看不见。

用法：
    python3 verify_clean_reproduction.py \\
        --support-zip MCM-Result/Paper-Outputs/deliverables/submission/support.zip \\
        --expect-problems 5 \\
        --expect-value "1.391646" --expect-value "17188" \\
        --output MCM-Result/Review-Results/T8_CLEAN_REPRO.json

    # 只验结构与写入边界，不跑长时间求解（先用它快速排错，再跑完整版）
    python3 verify_clean_reproduction.py --support-zip ... --structure-only
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def snapshot(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {p.name for p in directory.iterdir()}


def run(command: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        return 124, f"TIMEOUT after {timeout}s\n{exc.stdout or ''}{exc.stderr or ''}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--support-zip", type=Path, required=True)
    parser.add_argument("--expect-problems", type=int, required=True,
                        help="论文实际问数；不传 run_all 只校验入口编号连续，防不住整体少一问")
    parser.add_argument("--expect-value", action="append", default=[],
                        help="必须出现在复现输出中的关键数值，可重复；取自论文/RESULTS.md")
    parser.add_argument("--requirements", default="requirements-lock.txt")
    parser.add_argument("--seed", type=int, default=20250904)
    parser.add_argument("--state-dir", default="intermediate")
    parser.add_argument("--timeout", type=int, default=3600, help="复现步骤超时秒数")
    parser.add_argument("--structure-only", action="store_true",
                        help="只解压、装依赖、验证入口完整与写入边界，不跑求解")
    parser.add_argument("--keep", action="store_true", help="保留临时目录供排错")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, object] = {
        "schema_version": 1,
        "support_zip": str(args.support_zip),
        "expect_problems": args.expect_problems,
        "structure_only": args.structure_only,
        "steps": {},
        "errors": errors,
        "warnings": warnings,
    }

    if not args.support_zip.is_file():
        errors.append(f"SUPPORT_ZIP_MISSING {args.support_zip}")
        return emit(report, args.output, 1)

    workdir = Path(tempfile.mkdtemp(prefix="clean-repro-"))
    # sandbox 的父目录用来检测越界写入：支撑包脚本只应写进 sandbox 自身。
    sandbox = workdir / "support"
    sandbox.mkdir()
    try:
        with zipfile.ZipFile(args.support_zip) as archive:
            bad = archive.testzip()
            if bad:
                errors.append(f"ZIP_CORRUPT 首个损坏条目：{bad}")
                return emit(report, args.output, 1)
            archive.extractall(sandbox)
        files = [p for p in sandbox.rglob("*") if p.is_file()]
        report["steps"]["extract"] = {"status": "OK", "files": len(files)}

        # 入口完整性：论文有几问，src/ 就该有几个入口
        entries = sorted(p.stem for p in (sandbox / "src").glob("p*.py")) if (sandbox / "src").is_dir() else []
        report["steps"]["entrypoints"] = {"found": entries, "expected": args.expect_problems}
        if len(entries) != args.expect_problems:
            errors.append(
                f"ENTRYPOINT_SHORTFALL src/ 下有 {len(entries)} 个问题入口 {entries}，"
                f"论文有 {args.expect_problems} 问。缺少必要源程序是格式规范第五条的取消资格红线"
            )

        requirements = sandbox / args.requirements
        if not requirements.is_file():
            errors.append(f"REQUIREMENTS_MISSING 支撑包缺 {args.requirements}")
            return emit(report, args.output, 1)

        venv = sandbox / ".venv"
        code, log = run([sys.executable, "-m", "venv", str(venv)], sandbox, 300)
        if code != 0:
            errors.append(f"VENV_FAILED {log[-500:]}")
            return emit(report, args.output, 1)
        python = venv / "bin" / "python"
        if not python.exists():
            python = venv / "Scripts" / "python.exe"
        code, log = run(
            [str(python), "-m", "pip", "install", "-q", "-r", str(requirements)], sandbox, 900
        )
        report["steps"]["install"] = {"status": "OK" if code == 0 else "FAIL"}
        if code != 0:
            errors.append(f"INSTALL_FAILED 评委装不上依赖即等同程序不能运行：{log[-800:]}")
            return emit(report, args.output, 1)

        # 写入边界快照：只应写进 sandbox 自身
        before = snapshot(workdir)

        command = [str(python), "run_all.py", "--seed", str(args.seed),
                   "--state-dir", args.state_dir, "--expect-problems", str(args.expect_problems)]
        if args.structure_only:
            # 只加载入口做完整性校验，不执行求解
            code, log = run(
                [str(python), "-c",
                 "import sys; sys.argv=['run_all.py','--all','--expect-problems',"
                 f"'{args.expect_problems}']; "
                 "import importlib.util,pathlib; "
                 "spec=importlib.util.spec_from_file_location('ra','run_all.py'); "
                 "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
                 f"print('[ENTRYPOINTS]', m._problem_numbers(True, None, {args.expect_problems}))"],
                sandbox, 120,
            )
        else:
            command.insert(2, "--all")
            started = time.time()
            code, log = run(command, sandbox, args.timeout)
            report["steps"]["run_all"] = {"exit": code, "wall_s": round(time.time() - started, 1)}

        report["steps"]["output_tail"] = log[-1500:]
        if code != 0:
            errors.append(f"RUN_ALL_FAILED exit={code}；这是「程序不能运行」红线")

        # 越界写入检查
        after = snapshot(workdir)
        escaped = sorted(after - before - {"support"})
        report["steps"]["write_boundary"] = {"escaped": escaped}
        if escaped:
            errors.append(
                f"WRITE_ESCAPED_SANDBOX 复现过程在解压目录**之外**创建了 {escaped}。"
                "支撑包脚本常用 Path(__file__).parents[1] 定位输出目录——在工作区指向"
                "MCM-Result/，在支撑包里却指向评委的下载/桌面目录。绝对路径检查查不到"
                "这种相对路径逃逸；输出目录必须自锚到脚本所在目录或走显式参数"
            )

        if not args.structure_only:
            # [DONE] 行必须报出实际运行的问数，且与论文一致
            if "[DONE]" in log:
                done_line = [ln for ln in log.splitlines() if "[DONE]" in ln][-1]
                report["steps"]["done_line"] = done_line
                if f"运行 {args.expect_problems} 问" not in done_line:
                    errors.append(
                        f"PROBLEM_COUNT_MISMATCH [DONE] 行未报出 {args.expect_problems} 问：{done_line}"
                    )
            else:
                errors.append("NO_DONE_MARKER 复现未跑到 [DONE]，不能视为跑通")

            missing_values = [v for v in args.expect_value if v not in log]
            report["steps"]["expected_values"] = {
                "checked": args.expect_value, "missing": missing_values
            }
            if missing_values:
                errors.append(
                    f"VALUE_MISMATCH 复现输出中找不到论文关键数值 {missing_values}。"
                    "「运行结果与论文不符」是格式规范第五条红线，必须追根因，不得改论文数字凑答案"
                )
            elif not args.expect_value:
                warnings.append(
                    "NO_VALUE_ASSERTION 未传 --expect-value：跑通不等于结果与论文一致，"
                    "至少断言每问一个关键数值"
                )
    finally:
        if args.keep:
            report["workdir"] = str(workdir)
        else:
            shutil.rmtree(workdir, ignore_errors=True)

    return emit(report, args.output, 1 if errors else 0)


def emit(report: dict, output: Path | None, code: int) -> int:
    report["status"] = "FAIL" if report["errors"] else (
        "PASS_WITH_WARNINGS" if report["warnings"] else "PASS"
    )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
