import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/mcm-gold/templates/verify_paper_contract.py"
COVERAGE_COLUMNS = [
    "question_id",
    "component",
    "required_content",
    "claim_or_risk_ids",
    "paper_anchor",
    "evidence_ids",
    "observed",
    "status",
    "human_status",
]
RUBRIC_COLUMNS = [
    "dimension",
    "score",
    "max_score",
    "pass_score",
    "evidence",
    "observed",
    "status",
]
ANCHORS = {
    "interface": "问题一任务接口",
    "definition": "问题一数学定义",
    "algorithm": "问题一求解算法",
    "result": "问题一结果表",
    "validation": "问题一稳健性检验",
    "boundary": "问题一解释边界",
}
RUBRIC = [
    ("摘要页", 15, 15, 10),
    ("问题分析与假设", 9, 10, 6),
    ("模型建立", 23, 25, 16),
    ("求解与结果正确性", 20, 22, 15),
    ("检验与稳健性", 11, 13, 8),
    ("写作与图表", 10, 12, 8),
    ("合规与附录", 3, 3, 3),
]

# 深度机检（SPEC §2）引入后，默认夹具必须是一篇满足全部形态下限的"健康论文"：
# 每问区间 ≥800 汉字且 ≥1 编号式、全文 ≥3 表、摘要 ≥550 字且 ≥4 处含单位数值、
# 模型评价 ≥200 字、参考文献 ≥3 条、正文 ≥10000 汉字（配合 --reader-pages 18 不触线）。
FILLER_SENTENCES = (
    "本节从机理出发逐条建立变量关系，参数取值随式给出并标注单位，来源按题给数据、文献、拟合与估计四类逐句说明。",
    "推导过程中相邻公式之间给出操作动词衔接句，对新引入的方程补充一句可解性论证，说明未知数个数与方程个数相匹配。",
    "数值实验采用固定随机种子的重复运行，结果保留四位有效数字，与基线方案逐项对照，偏差均在工程可接受范围内。",
    "灵敏度分析对关键参数施加百分之五扰动，记录最大偏差并给出判定句，逐条回收前文假设并说明其稳健性影响。",
)
ABSTRACT_BLOCK = (
    "本文针对赛题三个问题建立机理驱动的数学模型，给出完整求解与检验流程。"
    "问题一拟合误差 0.35 mm，单次求解耗时 12 秒；"
    "问题二在正负 5% 扰动下最大偏差 2.1%，独立运行 50 次均收敛；"
    "问题三样本量 1000 个，方案效率提升 1.8 倍，工作温度 25 ℃。"
)
EVALUATION_BLOCK = (
    "优点：相位定义与拟合结果相互印证，灵敏度分析显示关键参数扰动下结论稳健，假设均已逐条回收；"
    "缺点：边界段所述线性化假设在极端工况下精度下降，结果外推需结合对照实验谨慎使用。"
)
APPENDIX = (
    "附录 A 支撑材料文件列表\n"
    "solve.py\n"
    "附录 B 完整源程序\n"
    "solve.py\n"
    "result = compute_solution(data, seed=2024)\n"
)


def filler_paragraphs(cycles: int) -> str:
    """生成中性论证段落；刻意不含摘要/关键词/评价/参考文献/附录等定位标记词。"""
    return "\n".join("".join(FILLER_SENTENCES) for _ in range(cycles)) + "\n"


def build_healthy_reader() -> str:
    """构造满足全部深度形态下限的合成阅读版正文。"""
    return (
        "2025 年赛题论文阅读版\n"
        + "一、问题重述\n"
        + filler_paragraphs(4)
        + "二、问题分析\n"
        + filler_paragraphs(4)
        + "摘要\n"
        + "\n".join([ABSTRACT_BLOCK] * 8)
        + "\n关键词：数学建模；灵敏度分析；优化求解；稳健性检验\n"
        + "三、问题一建模与求解\n"
        + ANCHORS["interface"]
        + "\n"
        + filler_paragraphs(10)
        + ANCHORS["definition"]
        + "\n"
        + filler_paragraphs(10)
        + "y_i = a_0 + a_1 x_i + e_i (1)\n"
        + "Phi = sum_i w_i y_i (2)\n"
        + "min J(theta) s.t. g_k(theta) <= 0 (3)\n"
        + ANCHORS["algorithm"]
        + "\n"
        + filler_paragraphs(10)
        + ANCHORS["result"]
        + "\n"
        + filler_paragraphs(10)
        + "表 1 主要结果与基线对照表\n"
        + "表 2 灵敏度分析扰动结果表\n"
        + "表 3 稳健性检验汇总表\n"
        + ANCHORS["validation"]
        + "\n"
        + filler_paragraphs(8)
        + ANCHORS["boundary"]
        + "\n"
        + filler_paragraphs(6)
        + "四、模型的评价\n"
        + "\n".join([EVALUATION_BLOCK] * 3)
        + "\n五、参考文献\n"
        # 反编造校验默认开启后，健康夹具的参考文献必须**真的可追溯**：三条均取自
        # references/literature-library.md，分别覆盖 ISBN 命中与 DOI 命中两条路径。
        # 用「张三/李四」这类占位条目会（正确地）判 REFERENCE_UNSOURCED。
        + "[1] 姜启源, 谢金星, 叶俊. 数学模型(第五版). 高等教育出版社, 2018. ISBN 978-7-04-049222-4.\n"
        + "[2] Sobol' I M. Global Sensitivity Indices for Nonlinear Mathematical Models and Their "
        "Monte Carlo Estimates. Mathematics and Computers in Simulation, 2001, 55(1-3): 271-280. "
        "doi:10.1016/S0378-4754(00)00270-6.\n"
        + "[3] Dantzig G B, Wolfe P. Decomposition Principle for Linear Programs. "
        "Operations Research, 1960, 8(1): 101-111. doi:10.1287/opre.8.1.101.\n"
    )


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class PaperContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reader = self.root / "main.txt"
        self.submission = self.root / "paper_submission.txt"
        self.coverage = self.root / "PAPER_COVERAGE_LEDGER.csv"
        self.rubric = self.root / "T7_RUBRIC_REVIEW.csv"
        self.source = self.root / "support"
        self.source.mkdir()
        (self.source / "solve.py").write_text(
            "def solve(data):\n    result = compute_solution(data, seed=2024)\n    return result\n",
            encoding="utf-8",
        )
        body = build_healthy_reader()
        self.reader.write_text(body, encoding="utf-8")
        self.submission.write_text(body + APPENDIX, encoding="utf-8")
        self.coverage_rows = []
        for component, anchor in ANCHORS.items():
            self.coverage_rows.append(
                {
                    "question_id": "Q1",
                    "component": component,
                    "required_content": f"Q1 {component} 的实质内容",
                    "claim_or_risk_ids": "K-001" if component == "validation" else "C-001",
                    "paper_anchor": anchor,
                    "evidence_ids": "R-002" if component == "validation" else ("R-001" if component == "result" else "C-001"),
                    "observed": f"已在 {anchor} 回读",
                    "status": "PASS",
                    "human_status": "HUMAN_ACCEPTED",
                }
            )
        self.write_valid_files()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_valid_files(self) -> None:
        write_csv(self.coverage, COVERAGE_COLUMNS, self.coverage_rows)
        write_csv(
            self.rubric,
            RUBRIC_COLUMNS,
            [
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": f"{name}页/图/表锚点",
                    "observed": f"实读得分 {score}",
                    "status": "PASS" if score >= passing else "FAIL",
                }
                for name, score, maximum, passing in RUBRIC
            ],
        )

    def run_contract(self, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--coverage",
            str(self.coverage),
            "--rubric",
            str(self.rubric),
            "--reader",
            str(self.reader),
            "--submission",
            str(self.submission),
            "--source-root",
            str(self.source),
            "--support-root",
            str(self.source),
            "--reader-pages",
            "18",
            "--submission-pages",
            "21",
            *extra,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def test_complete_contract_passes(self) -> None:
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["rubric_total"], 91)

    def test_concise_complete_paper_only_warns(self) -> None:
        # 触线（11 页 < 14）但深度形态项齐全：机检豁免留痕，不阻断 PASS。
        result, report = self.run_contract("--reader-pages", "11")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        codes = {item["code"] for item in report["warnings"]}
        self.assertIn("DEPTH_FORM_CHECKS_PASSED", codes)
        self.assertIn("DEPTH_REVIEW_REQUIRED", codes)

    def test_missing_component_fails_contract(self) -> None:
        self.coverage_rows.pop()
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "FAIL_CONTRACT")
        self.assertIn("MISSING_COMPONENT", {item["code"] for item in report["errors"]})

    def test_weak_coverage_routes_to_expansion(self) -> None:
        self.coverage_rows[2]["status"] = "WEAK"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_EXPANSION")

    def test_invented_four_dimension_rubric_is_rejected(self) -> None:
        rows = []
        for name, score, maximum, passing in RUBRIC[:4]:
            rows.append(
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": "anchor",
                    "observed": "checked",
                    "status": "PASS",
                }
            )
        write_csv(self.rubric, RUBRIC_COLUMNS, rows)
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING_RUBRIC_DIMENSION", {item["code"] for item in report["errors"]})

    def test_below_target_cannot_pass(self) -> None:
        lowered = list(RUBRIC)
        lowered[2] = ("模型建立", 18, 25, 16)
        write_csv(
            self.rubric,
            RUBRIC_COLUMNS,
            [
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": "anchor",
                    "observed": "checked",
                    "status": "PASS",
                }
                for name, score, maximum, passing in lowered
            ],
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_EXPANSION")
        self.assertIn("RUBRIC_BELOW_TARGET", {item["code"] for item in report["expansion_items"]})

    def test_missing_submission_fails_contract(self) -> None:
        self.submission.unlink()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING_OR_UNREADABLE_SUBMISSION", {item["code"] for item in report["errors"]})

    def test_file_list_without_source_content_fails(self) -> None:
        body = self.reader.read_text(encoding="utf-8")
        self.submission.write_text(
            body + "附录 A 支撑材料文件列表\nsolve.py\n附录 B 完整源程序\nsolve.py\n",
            encoding="utf-8",
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SOURCE_CONTENT_NOT_EMBEDDED", {item["code"] for item in report["errors"]})

    def test_appendix_code_stale_when_source_edited_after_compile(self) -> None:
        """改了源码却没重编论文：附录印的是旧代码，必须与「压根没嵌入」区分开报。

        2025C 实测漏网场景——旧的 source_signature() 只抽最长一行做签名，那一行没动
        就整份放行；实际交付的论文附录里是修复前跑不通的 nipt_core.py。
        """
        source = self.source / "solve.py"
        original = source.read_text(encoding="utf-8")
        source.write_text(
            original + '\nDATA_ROOT = resolve_workspace_root(__file__, fallback="here")\n',
            encoding="utf-8",
        )
        result, report = self.run_contract()
        codes = {item["code"] for item in report["errors"]}
        self.assertEqual(result.returncode, 1)
        self.assertIn("APPENDIX_CODE_STALE", codes)
        self.assertNotIn("SOURCE_CONTENT_NOT_EMBEDDED", codes)
        message = next(i["message"] for i in report["errors"]
                       if i["code"] == "APPENDIX_CODE_STALE")
        self.assertIn("resolve_workspace_root", message.replace(" ", ""))

    def test_source_absent_from_appendix_is_not_reported_as_stale(self) -> None:
        """一行都回读不到 = 根本没收录，与「收录了但过期」是两种毛病、两种修法。"""
        body = self.reader.read_text(encoding="utf-8")
        self.submission.write_text(
            body + "附录 A 支撑材料文件列表\nsolve.py\n附录 B 完整源程序\nsolve.py\n",
            encoding="utf-8",
        )
        result, report = self.run_contract()
        codes = {item["code"] for item in report["errors"]}
        self.assertEqual(result.returncode, 1)
        self.assertIn("SOURCE_CONTENT_NOT_EMBEDDED", codes)
        self.assertNotIn("APPENDIX_CODE_STALE", codes)

    def test_non_ascii_only_source_is_reported_unchecked_not_passed(self) -> None:
        """没有可回读锚点时如实记「未核」，不得静默计为通过。"""
        (self.source / "notes.py").write_text(
            "# 全中文注释文件，没有可回读的 ASCII 行内锚点\n", encoding="utf-8")
        self.submission.write_text(
            self.submission.read_text(encoding="utf-8") + "notes.py\n", encoding="utf-8")
        _, report = self.run_contract()
        warning_codes = {item["code"] for item in report["warnings"]}
        self.assertIn("SOURCE_CONTENT_NOT_CHECKABLE", warning_codes)

    def test_reader_submission_body_drift_fails(self) -> None:
        text = self.submission.read_text(encoding="utf-8")
        self.submission.write_text("提交版擅自改写正文\n" + text, encoding="utf-8")
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SCIENTIFIC_BODY_DRIFT", {item["code"] for item in report["errors"]})

    def test_no_appendix_mode_still_compares_bodies(self) -> None:
        self.submission.write_text(
            self.reader.read_text(encoding="utf-8") + "科学正文漂移\n",
            encoding="utf-8",
        )
        result, report = self.run_contract("--no-appendix-required")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SCIENTIFIC_BODY_DRIFT", {item["code"] for item in report["errors"]})

    def test_directory_declaration_covers_files_beneath_it(self) -> None:
        """附录写一行 `figures/` 即覆盖其下文件，不必逐个列出。

        逐文件比对会逼人把几十个文件名（含每张图的同名 .csv）塞进正文，
        既不合国赛论文惯例又挤占篇幅；实测 2025A 演练因此一次报出 25 条
        SUPPORT_FILE_NOT_LISTED，其中 24 条是这个口径问题，1 条才是真缺陷。
        """
        nested = self.source / "figures"
        nested.mkdir(exist_ok=True)
        (nested / "F-001-panel.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        (nested / "F-001-panel.pdf").write_text("%PDF-1.4\n", encoding="utf-8")
        body = self.reader.read_text(encoding="utf-8")
        self.submission.write_text(
            body + APPENDIX + "\nfigures/    正文图及其图源表\n", encoding="utf-8"
        )
        _, report = self.run_contract()
        unlisted = [
            item["message"] for item in report["errors"]
            if item["code"] == "SUPPORT_FILE_NOT_LISTED"
        ]
        self.assertEqual(unlisted, [], f"目录级声明应覆盖其下文件，实际报出：{unlisted}")

    def test_top_level_file_still_needs_naming(self) -> None:
        """顶层散落文件没有可声明的父目录，仍须具名——否则目录级放宽会变成全放行。"""
        (self.source / "orphan_helper.py").write_text("print(1)\n", encoding="utf-8")
        _, report = self.run_contract()
        messages = " ".join(
            item["message"] for item in report["errors"]
            if item["code"] == "SUPPORT_FILE_NOT_LISTED"
        )
        self.assertIn("orphan_helper.py", messages)

    def test_ledger_value_absent_from_paper_is_flagged(self) -> None:
        """终检清单要求「正文数字 = RESULTS.md」，此前全靠人工比对。

        台账登记了结果、论文里却一个对应数值都找不到，说明两者已脱节。
        只取 >=4 位小数的高精度数值作判据：整数和一两位小数在任何论文里都
        可能偶然出现，拿它们比对会产出大量假通过，比不查更糟。
        """
        ledger = self.root / "RESULTS.md"
        ledger.write_text(
            "# RESULTS\n\n"
            "| ID | 内容 | 值/单位 | 输入 | 命令 | 种子 | 计算 | 核验 | 图 | verify | 状态 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| R-901 | 论文里有的量 | 1.391646 s | | | | | | | | CONFIRMED |\n"
            "| R-902 | 论文里没有的量 | 98765.432109 s | | | | | | | | CONFIRMED |\n"
            "| R-903 | 已作废 | 55555.111111 s | | | | | | | | STALE |\n",
            encoding="utf-8",
        )
        body = self.reader.read_text(encoding="utf-8")
        self.reader.write_text(body + "\n实测值 1.391646 s。\n", encoding="utf-8")
        self.submission.write_text(
            self.reader.read_text(encoding="utf-8") + APPENDIX, encoding="utf-8"
        )
        _, report = self.run_contract("--results-ledger", str(ledger))
        absent = {item["id"] for item in report["results_check"]["absent"]}
        self.assertEqual(absent, {"R-902"}, "只有论文里查无此数的活动记录该被报出")
        self.assertIn("RESULTS_NOT_IN_PAPER", {item["code"] for item in report["errors"]})

    def test_fabricated_references_are_rejected_without_any_flag(self) -> None:
        """反编造校验必须**默认**生效。

        回归的是一处真实失效：`--literature-library` 曾是可选参数，不传就静默 SKIPPED，
        而四处文档化的调用命令全都不传——照文档执行终检等于不校验参考文献。
        """
        body = self.reader.read_text(encoding="utf-8")
        fabricated = body[: body.index("五、参考文献")] + (
            "五、参考文献\n"
            "[1] 张三, 李四. 数学建模方法导论. 高等教育出版社, 2020.\n"
            "[2] 王五. 灵敏度分析与稳健性检验综述. 应用数学学报, 2021.\n"
            "[3] 赵六. 优化模型数值求解方法. 计算数学, 2022.\n"
        )
        self.reader.write_text(fabricated, encoding="utf-8")
        self.submission.write_text(fabricated + APPENDIX, encoding="utf-8")
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFERENCE_UNSOURCED", {item["code"] for item in report["errors"]})
        self.assertEqual(report["reference_check"]["unsourced"], 3)

    def test_missing_library_blocks_and_reports_null_counts(self) -> None:
        """「没查」与「查了没问题」必须在报告里可区分。

        跳过时把计数写 0 会与「真查了、零条未溯源」字面完全一样，是最容易骗过人眼的一处；
        且显式传入的库路径读不到属内容问题，必须阻断而不是留个 warning 放行。
        """
        result, report = self.run_contract("--literature-library", str(self.root / "no-such-lib.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFERENCE_LIBRARY_UNREADABLE", {item["code"] for item in report["errors"]})
        self.assertEqual(report["reference_check"]["status"], "SKIPPED")
        self.assertIsNone(report["reference_check"]["unsourced"])
        self.assertIsNone(report["reference_check"]["library_hits"])

    def test_appendix_offset_tolerance_does_not_swallow_real_drift(self) -> None:
        """APPENDIX_MARKER_OFFSET 只容忍附录标题字符，不容忍多出的正文。

        回归的是一处门禁降级：该分支原本只判「前缀匹配 + 相似度 ≥0.995」，
        于是任何追加到提交版末尾的正文都被当成截断偏移放行。
        """
        body = self.reader.read_text(encoding="utf-8")
        self.submission.write_text(
            body + "本文结论表明该策略在给定条件下最优且稳健可靠。" + APPENDIX,
            encoding="utf-8",
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SCIENTIFIC_BODY_DRIFT", {item["code"] for item in report["errors"]})

    def test_pdf_formula_extraction_reordering_only_warns(self) -> None:
        body = self.reader.read_text(encoding="utf-8") + "公式ABC≥DEF\n"
        self.reader.write_text(body, encoding="utf-8")
        submission_body = body.replace("公式ABC≥DEF", "公式ABCDE≥F")
        self.submission.write_text(submission_body + APPENDIX, encoding="utf-8")
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertIn("PDF_TEXT_ORDER_VARIANCE", {item["code"] for item in report["warnings"]})

    def test_pending_human_review_cannot_pass(self) -> None:
        for row in self.coverage_rows:
            row["human_status"] = "PENDING"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_HUMAN")

    def test_compound_historical_ids_are_accepted(self) -> None:
        for row in self.coverage_rows:
            row["claim_or_risk_ids"] = "K-D201" if row["component"] == "validation" else "C-D101"
            if row["component"] in {"result", "validation"}:
                row["evidence_ids"] = "R-D301"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")

    def test_reader_page_limit_is_hard_failure(self) -> None:
        result, report = self.run_contract("--reader-pages", "31")
        self.assertEqual(result.returncode, 1)
        self.assertIn("READER_PAGE_LIMIT_EXCEEDED", {item["code"] for item in report["errors"]})

    def test_proxy_rehearsal_never_becomes_formal_pass(self) -> None:
        for row in self.coverage_rows:
            row["human_status"] = "PROXY_REHEARSAL"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PROXY_REHEARSAL")

    def test_thin_incomplete_paper_needs_expansion(self) -> None:
        # 形态缺项的薄文必须 NEEDS_EXPANSION：页数/字数只是触发线，形态缺项才是阻断项。
        thin_body = "\n".join(ANCHORS.values()) + "\n"
        self.reader.write_text(thin_body, encoding="utf-8")
        self.submission.write_text(thin_body + APPENDIX, encoding="utf-8")
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_EXPANSION")
        codes = {item["code"] for item in report["expansion_items"]}
        self.assertIn("QUESTION_PROSE_FLOOR", codes)
        self.assertIn("QUESTION_EQUATION_FLOOR", codes)
        self.assertIn("RESULT_TABLE_FLOOR", codes)
        self.assertIn("REFERENCE_FLOOR", codes)


if __name__ == "__main__":
    unittest.main()


class PaginationTests(unittest.TestCase):
    """页码自摘要页起连续——规则第 42/44 条，此前全靠人眼翻页。

    实测踩过的坑：模板在摘要后写 \\setcounter{page}{1}，摘要标 1–2、正文又从 1
    重新计，全文两套页码，而所有 Gate 都判全绿。
    """

    @staticmethod
    def _load():
        import importlib.util

        spec = importlib.util.spec_from_file_location("vpc", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _check(self, footers):
        module = self._load()
        text = "\f".join(f"正文内容第 {i} 页\n{f}" for i, f in enumerate(footers, 1))
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "paper.pdf"
            fake.write_bytes(b"%PDF-1.4\n")
            errors, warnings = [], []
            return module.validate_pagination(fake, text, errors, warnings), errors, warnings

    def test_continuous_pagination_passes(self) -> None:
        report, errors, _ = self._check([1, 2, 3, 4, 5])
        self.assertEqual(report["mismatched"], [])
        self.assertEqual(errors, [])

    def test_counter_reset_after_abstract_is_caught(self) -> None:
        """摘要 1–2 后正文从 1 重新计，正是实测踩到的形态。"""
        report, errors, _ = self._check([1, 2, 1, 2, 3])
        self.assertIn("PAGINATION_DISCONTINUOUS", {item["code"] for item in errors})
        self.assertEqual(
            [entry["pdf_page"] for entry in report["mismatched"]], [3, 4, 5]
        )

    def test_section_numbers_are_not_mistaken_for_footers(self) -> None:
        """判据只认「整页最后一行且整行纯数字」；正文里的孤立数字不得被当页码。"""
        module = self._load()
        text = "1 问题重述\n正文若干\n表 3 结果对照\f2 模型建立\n正文若干\n"
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "paper.pdf"
            fake.write_bytes(b"%PDF-1.4\n")
            errors, warnings = [], []
            report = module.validate_pagination(fake, text, errors, warnings)
        self.assertEqual(report["status"], "SKIPPED")
        self.assertIn("PAGINATION_NOT_DETECTED", {item["code"] for item in warnings})
        self.assertEqual(errors, [])

