#!/usr/bin/env python3
"""一键复现入口：运行 src/pN.py，并生成可审计的 RESULTS.jsonl/RESULTS.md。"""

import argparse
import contextlib
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

# 台账目录。默认相对 cwd 的 workspace/，让评委在支撑包根目录直接 `python run_all.py --all` 即可。
# MCM_STATE_DIR 供工作区内的核验脚本指向真实台账：硬编码相对路径时，从别的目录调用
# 会静默新建一个空 workspace/ 再报「未找到结果 ID」，把「路径不对」伪装成「数据不存在」。
STATE_DIR = pathlib.Path(os.environ.get("MCM_STATE_DIR", "workspace"))
HEADER = (
    "| ID | 内容 | 值/单位 | 输入 SHA-256 | 脚本/命令 | 种子 | 计算时间 | 核验时间 | 图表 | verify | 状态 |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def set_seed(seed: int) -> None:
    """固定随机源。numpy 延迟导入：--confirm 等纯记账操作不该被绘图/数值栈的缺失阻断，
    清环境复现时也不该因为一个模型根本没用到的包而失败在与模型无关的 ImportError 上。"""
    random.seed(seed)
    try:
        import numpy as np
    except ModuleNotFoundError:
        print("[WARN] 未安装 numpy：只固定了 random 种子。若模型用到 numpy 随机数，"
              "本次运行不可复现——先装 numpy 再重跑，不要拿这次结果进论文")
    else:
        np.random.seed(seed)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _escape(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str).strip('"').replace("|", "\\|").replace("\n", " ")


def _records_unlocked() -> list[dict]:
    path = STATE_DIR / "RESULTS.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


@contextlib.contextmanager
def _state_lock(timeout: float = 30.0):
    """Serialize ledger updates across parallel stage processes."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_stream = (STATE_DIR / ".results.lock").open("a+b")
    if lock_stream.tell() == 0:
        lock_stream.write(b"0")
        lock_stream.flush()
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while not acquired:
            try:
                if os.name == "nt":
                    import msvcrt

                    lock_stream.seek(0)
                    msvcrt.locking(lock_stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise SystemExit(f"等待结果台账锁超时：{STATE_DIR / '.results.lock'}")
                time.sleep(0.05)
        yield
    finally:
        if acquired:
            if os.name == "nt":
                import msvcrt

                lock_stream.seek(0)
                msvcrt.locking(lock_stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)
        lock_stream.close()


def _records() -> list[dict]:
    with _state_lock():
        return _records_unlocked()


def _write_markdown(records: list[dict]) -> None:
    latest = {item["id"]: item for item in records}
    target = STATE_DIR / "RESULTS.md"
    temporary = STATE_DIR / f".RESULTS.md.{os.getpid()}.{time.time_ns()}.tmp"
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write("# RESULTS\n\n" + HEADER)
            for item in latest.values():
                inputs = ", ".join(f"{p}:{h}" for p, h in item.get("inputs", {}).items())
                cells = [item.get(k, "") for k in ("id", "name", "value", "_inputs", "command", "seed",
                                                   "computed_at", "verified_at", "fig", "verify", "status")]
                cells[3] = inputs
                stream.write("| " + " | ".join(_escape(cell) for cell in cells) + " |\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _append(record: dict, *, reject_existing: bool = False) -> None:
    with _state_lock():
        records = _records_unlocked()
        if reject_existing and any(item["id"] == record["id"] for item in records):
            raise SystemExit(
                f"结果 ID {record['id']} 已存在：复现请使用空 state_dir；"
                "新计算请换新 R-id 并登记 SUPERSEDED"
            )
        with (STATE_DIR / "RESULTS.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        _write_markdown([*records, record])


def log_result(rid: str, name: str, value, script: str, seed: int, fig: str | None = None,
               inputs: list[str] | None = None) -> None:
    input_hashes = {path: _sha256(path) for path in (inputs or [])}
    record = {
        "id": rid, "name": name, "value": value, "inputs": input_hashes,
        "command": f"{script} | {shlex.join([sys.executable, *sys.argv])}", "seed": seed,
        "computed_at": _now(), "verified_at": "", "fig": fig or "",
        "verify": "", "status": "PENDING",
    }
    _append(record, reject_existing=True)
    print("[LOGGED]", json.dumps(record, ensure_ascii=False, default=str))


def confirm_result(rid: str, evidence: str, status: str) -> None:
    with _state_lock():
        records = _records_unlocked()
        matches = [record for record in records if record["id"] == rid]
        if not matches:
            raise SystemExit(f"未找到结果 ID: {rid}")
        record = dict(matches[-1])
        # 只写核验时间，绝不覆盖 computed_at：反幻觉铁律要求 R-id 关联"这个数是什么时候算出来的"，
        # 把计算时间改成核验时间会让 T8 的时间戳比对失去意义。
        record.update(verify=evidence, status=status, verified_at=_now())
        with (STATE_DIR / "RESULTS.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        _write_markdown([*records, record])
    print(f"[VERIFIED] {rid} -> {status}: {evidence}")


def _problem_numbers(all_problems: bool, problem: int | None) -> list[int]:
    if problem is not None:
        if not pathlib.Path(f"src/p{problem}.py").is_file():
            raise SystemExit(f"未找到 src/p{problem}.py（当前工作目录 {pathlib.Path.cwd()}）")
        return [problem]
    found = []
    for path in pathlib.Path("src").glob("p*.py"):
        match = re.fullmatch(r"p(\d+)", path.stem)
        if match:
            found.append(int(match.group(1)))
    if all_problems and not found:
        # 最常见原因不是"没写代码"，而是没先 cd 进支撑包根目录——评委照 README 跑最容易踩这个。
        raise SystemExit(
            f"未发现 src/p1.py、src/p2.py 等问题入口。\n"
            f"当前工作目录：{pathlib.Path.cwd()}\n"
            f"本脚本按相对路径查找 src/，请先 cd 到支撑包根目录（run_all.py 所在目录）再执行。"
        )
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
