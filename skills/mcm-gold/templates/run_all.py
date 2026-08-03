#!/usr/bin/env python3
"""一键复现入口：运行 src/pN.py，并生成可审计的 RESULTS.jsonl/RESULTS.md。"""

import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
import pathlib
import random
import re
import shlex
import sys
import time

import numpy as np

STATE_DIR = pathlib.Path("workspace")
HEADER = (
    "| ID | 内容 | 值/单位 | 输入 SHA-256 | 脚本/命令 | 种子 | 时间 | 图表 | verify | 状态 |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _escape(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str).strip('"').replace("|", "\\|").replace("\n", " ")


def _records() -> list[dict]:
    path = STATE_DIR / "RESULTS.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _append(record: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "RESULTS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    latest = {item["id"]: item for item in _records()}
    with (STATE_DIR / "RESULTS.md").open("w", encoding="utf-8") as stream:
        stream.write("# RESULTS\n\n" + HEADER)
        for item in latest.values():
            inputs = ", ".join(f"{p}:{h}" for p, h in item.get("inputs", {}).items())
            cells = [item.get(k, "") for k in ("id", "name", "value", "_inputs", "command", "seed", "time", "fig", "verify", "status")]
            cells[3] = inputs
            stream.write("| " + " | ".join(_escape(cell) for cell in cells) + " |\n")


def log_result(rid: str, name: str, value, script: str, seed: int, fig: str | None = None,
               inputs: list[str] | None = None) -> None:
    if any(record["id"] == rid for record in _records()):
        raise SystemExit(f"结果 ID {rid} 已存在：复现请使用空 state_dir；新计算请换新 R-id 并登记 SUPERSEDED")
    input_hashes = {path: _sha256(path) for path in (inputs or [])}
    record = {
        "id": rid, "name": name, "value": value, "inputs": input_hashes,
        "command": f"{script} | {shlex.join([sys.executable, *sys.argv])}", "seed": seed,
        "time": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "fig": fig or "",
        "verify": "", "status": "PENDING",
    }
    _append(record)
    print("[LOGGED]", json.dumps(record, ensure_ascii=False, default=str))


def confirm_result(rid: str, evidence: str, status: str) -> None:
    matches = [record for record in _records() if record["id"] == rid]
    if not matches:
        raise SystemExit(f"未找到结果 ID: {rid}")
    record = dict(matches[-1])
    record.update(verify=evidence, status=status,
                  time=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    _append(record)
    print(f"[VERIFIED] {rid} -> {status}: {evidence}")


def _problem_numbers(all_problems: bool, problem: int | None) -> list[int]:
    if problem is not None:
        return [problem]
    found = []
    for path in pathlib.Path("src").glob("p*.py"):
        match = re.fullmatch(r"p(\d+)", path.stem)
        if match:
            found.append(int(match.group(1)))
    if all_problems and not found:
        raise SystemExit("未发现 src/p1.py、src/p2.py 等问题入口")
    return sorted(found)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--problem", type=int)
    mode.add_argument("--confirm", metavar="R_ID")
    parser.add_argument("--evidence", help="复现命令、差值或文件哈希")
    parser.add_argument(
        "--status",
        choices=["CONFIRMED", "REHEARSAL_CONFIRMED", "SUSPECT", "STALE"],
        default="CONFIRMED",
    )
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--state-dir", default=os.environ.get("MCM_STATE_DIR", "workspace"))
    args = parser.parse_args()

    global STATE_DIR
    STATE_DIR = pathlib.Path(args.state_dir).expanduser().resolve()
    if args.confirm:
        if not args.evidence:
            parser.error("--confirm 必须同时提供 --evidence")
        confirm_result(args.confirm, args.evidence, args.status)
        return

    set_seed(args.seed)
    started = time.time()
    for number in _problem_numbers(args.all, args.problem):
        module = importlib.import_module(f"src.p{number}")
        if not hasattr(module, "main"):
            raise SystemExit(f"src/p{number}.py 缺少 main(seed, log_result)")
        module.main(args.seed, log_result)
    print(f"[DONE] 用时 {time.time() - started:.1f}s，种子 {args.seed}，状态目录 {STATE_DIR}")


if __name__ == "__main__":
    main()
