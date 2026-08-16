# 论文与交付物模板

---

## 一、摘要专用页（LaTeX 片段）

```latex
\begin{center}\Large\textbf{<论文题目>}\end{center}
\begin{center}\textbf{摘\quad 要}\end{center}\quad <每问：难点→模型/算法→数值+单位→R-id验证；写清递进关系>
\textbf{创新点：}<没有它会怎样+对照证据>\quad \textbf{检验：}<范围+结论+R-id>\quad \textbf{关键词：}<4--5个，与 rubric-and-writing.md 的 target 及 verify_paper_contract 的 TARGET_KEYWORDS 同口径>
```

**排版要点**：三线表用 `booktabs`（`\toprule/\midrule/\bottomrule`）；中文用 `ctex`；图表编号与正文引用一致；页码 `\pagestyle{plain}` 页脚居中。

### 编译链路（**先跑 `templates/env_check.sh` 确认，别到 T7 才发现**）

| 环境情况 | 做法 |
|---|---|
| 有 latexmk | `latexmk -xelatex paper.tex` |
| **无 latexmk**（常见于精简 TeX Live） | `xelatex paper.tex` **连跑两遍**，第二遍才有正确的交叉引用与页码 |
| **无 bibtex / natbib / cite 宏包** | 参考文献**手写** `\begin{thebibliography}{99} \bibitem{x} ... \end{thebibliography}`，**禁用** `\bibliography{}` 与 `\citep` |
| 无 algpseudocode | 有 `algorithm2e` 则使用；两者都无时用带行号的 `tabular`/枚举步骤 |
| ctex 选不到字体 | 文档类写 `\documentclass[fontset=fandol]{ctexart}`（Linux 常见），其他系统按实测字体集调整 |

### matplotlib 中文（**最易静默出错**：字体名不存在不报错，直接渲染成豆腐块）

```python
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
# 按当前机器实际可用字体挑一个，别照抄 SimHei
_avail = {f.name for f in fm.fontManager.ttflist}
for _cand in ["SimHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "FandolHei", "PingFang SC", "Heiti SC"]:
    if _cand in _avail:
        plt.rcParams["font.sans-serif"] = [_cand]
        break
else:
    raise RuntimeError("无可用中文字体：先装字体，否则所有中文标签都是方框")
plt.rcParams["axes.unicode_minus"] = False   # 负号也会变方框
```
出第一张带中文的图后**立刻打开看一眼**，不要等到 T7 汇总时才发现全是方框。

---

## 二、AI 工具使用声明（置于参考文献之前）

无论是否使用 AI，论文都必须在**参考文献之前**设置“AI 工具使用声明”，按实际情况二选一，不得改写原文：

```text
本参赛队在竞赛过程中未使用任何 AI 工具。
```

```text
本参赛队在竞赛过程中使用了 AI 工具，主要用于【简要用途，如语言润色、代码调试等】，详细使用情况见支撑材料。
```

使用 AI 时，把方括号内容替换为真实、简要的用途，并在支撑材料中放入文件名完全一致的 `AI 工具使用详情.pdf`。该 PDF 从 `AI_USAGE.md` 生成，至少回读工具名称/版本或型号、用途与环节、主要提示方式与使用过程、采纳/人工修改/核验情况；核心建模与分析还须关联参赛队主导证据。2026 版不要求把 AI 工具列入参考文献，也不再把 2025 版正文逐处标注作为强制项。

---

## 三、支撑材料 README

```markdown
# 支撑材料说明
环境=<Python/OS/依赖/求解器及安装命令>｜预计耗时=<实测>
复现=解压后 **先进入本目录再执行**：
    cd <解压目录>
    python3 run_all.py --all --seed <seed> --state-dir <dir>
目录=`src/`源程序（`src/MAPPING.md`列公式→文件→函数）、`data/`自主查阅数据、`figures/`图及脚本、`intermediate/`大篇幅中间结果
```

**复现命令必须带 `cd`**：入口按相对路径查找 `src/`，评委在解压目录之外执行会直接报"未发现 src/p1.py"，看起来像"代码没交全"——而格式规范第五条把"程序不能运行"列为可能取消评奖资格的情形。README 写法与 T8 清环境复现脚本必须一致。

每个 `src/pN.py` 暴露 `main(seed, log_result)`，登记结果时传 `inputs=[...]`，由入口自动写输入哈希、R-id 与复现命令。

优化脚本还须把求解器原生日志放入 `intermediate/`，结果值中登记 `termination/primal/bound/gap/time_limit/elapsed/variables/constraints/residual`；到时限的可行解在 README 和论文中统一称“限时可行解”。

---

## 四、附录文件列表（写入论文附录，须与 support.zip 内容完全一致）

```markdown
## 附录 A 支撑材料文件列表
| 文件 | 说明 |
|---|---|
| <support.zip 内相对路径> | <用途；逐文件列出，含 `AI 工具使用详情.pdf`（若使用）> |
```

正式提交版随后列“附录 B 源程序”，粘贴全部完整、可运行代码；同时生成省略合规材料和程序附录的阅读审查版。`MCM-Result/Paper-Outputs/paper/main.pdf` 固定为纯论文默认入口，提交候选用 `*_submission.pdf` 显式命名；阅读版正文与科学附录保持正赛论文形态，不插入训练说明、内部编号、责任边界或“不可提交”横幅；不可提交状态仅在文件名、论文外 README 和打包白名单标识。默认预览、逐页截图和 H-004 审表达均看阅读版；文件列表须由打包目录实际遍历生成，禁止手写猜测。

两版必须从同一科学正文生成，禁止复制后分别修改：

```text
MCM-Result/Paper-Outputs/paper/body.tex                 # 摘要到参考文献，唯一科学正文源
MCM-Result/Paper-Outputs/paper/main.tex                 # 只 input body.tex，生成 main.pdf
MCM-Result/Paper-Outputs/paper/<problem>_submission.tex # input body.tex，再接实际文件列表和完整源程序
```

```latex
% main.tex
\input{body.tex}

% <problem>_submission.tex（body.tex 结束后）
\input{body.tex}
\section*{附录 A\quad 支撑材料文件列表}
% 表格必须由最终支撑目录遍历生成
\section*{附录 B\quad 完整源程序}
\lstinputlisting[title={src/p1.py}]{../support/src/p1.py}
```

最终 PDF 必须执行 `templates/verify_paper_contract.py`：它回读阅读版锚点、七维 rubric、两版共享正文、实际文件列表和代码内容。缺提交版、文件列表或完整代码为契约硬失败。

**页数偏短的现行处理已不止「人工复核」**：阅读版触线（<14 页或 <10000 字）会启动深度形态核查——每问建模求解字数与编号公式、全文三线表、参考文献、摘要与模型评价密度。形态项缺一即写入 `expansion_items` 并让契约返回 `NEEDS_EXPANSION` 阻断交付，必须逐条实质扩写后重跑；形态全过则只记 `DEPTH_FORM_CHECKS_PASSED` 豁免留痕（同时仍出 `DEPTH_REVIEW_REQUIRED` warning，H-004 照旧要人工读 `main.pdf`）。**页数本身从不单独判失败**，所以触线的正确响应是补实质内容，不是填充文字或粘代码凑页数。

无程序时写明「本论文没有用到程序」；无支撑材料时写明「本论文没有支撑材料」。

---

## 五、题目拆解表（T1 用）

```markdown
| 小问 | 题面原话 | 要求交付什么 | 输入数据 | 判定"答对"的标准 | 疑难点 |
|---|---|---|---|---|---|
| 1 | "……" | 一组参数 + 依据 | 附件1 | 数值落在物理可行域且能验证 | 缺少 X 的取值 |
```

## 六、选题评分矩阵（T1 用，1–5 分加权）

```markdown
| 维度 | 权重 | A题 | B题 | C题 |
|---|---|---|---|---|
| 数据可得性与质量 | 0.15 | | | |
| 领域机理熟悉度 | 0.15 | | | |
| 方法储备匹配度 | 0.15 | | | |
| 计算量可控性 | 0.10 | | | |
| **结果可验证性** | 0.20 | | | |
| 创新空间 | 0.15 | | | |
| 写作难度（反向） | 0.10 | | | |
| **加权总分** | | | | |
```
`risk_appetite: conservative` 时提高「结果可验证性/数据质量」权重；`aggressive` 时提高「创新空间」。
