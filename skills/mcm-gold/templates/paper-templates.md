# 论文与交付物模板

---

## 一、摘要专用页（LaTeX 片段）

```latex
\begin{center}\Large\textbf{<论文题目>}\end{center}
\begin{center}\textbf{摘\quad 要}\end{center}\quad <每问：难点→模型/算法→数值+单位→R-id验证；写清递进关系>
\textbf{创新点：}<没有它会怎样+对照证据>\quad \textbf{检验：}<范围+结论+R-id>\quad \textbf{关键词：}<4--6个>
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

## 二、支撑材料 README

```markdown
# 支撑材料说明
环境=<Python/OS/依赖/求解器及安装命令>｜复现=`python3 run_all.py --all --seed <seed> --state-dir <dir>`｜预计耗时=<实测>
目录=`src/`源程序（`src/MAPPING.md`列公式→文件→函数）、`data/`自主查阅数据、`figures/`图及脚本、`intermediate/`大篇幅中间结果
```

每个 `src/pN.py` 暴露 `main(seed, log_result)`，登记结果时传 `inputs=[...]`，由入口自动写输入哈希、R-id 与复现命令。

优化脚本还须把求解器原生日志放入 `intermediate/`，结果值中登记 `termination/primal/bound/gap/time_limit/elapsed/variables/constraints/residual`；到时限的可行解在 README 和论文中统一称“限时可行解”。

---

## 三、附录文件列表（写入论文附录，须与 support.zip 内容完全一致）

```markdown
## 附录 A 支撑材料文件列表
| 文件 | 说明 |
|---|---|
| <support.zip 内相对路径> | <用途；逐文件列出，含 AI工具使用详情.pdf（若使用）> |
```

正式提交版随后列“附录 B 源程序”，粘贴全部完整、可运行代码；同时生成省略合规材料和程序附录的阅读审查版。`paper/main.pdf`固定为纯论文默认入口，提交候选用`*_submission.pdf`显式命名；阅读版正文与科学附录保持正赛论文形态，不插入训练说明、内部编号、责任边界或“不可提交”横幅；不可提交状态仅在文件名、论文外 README 和打包白名单标识。默认预览、逐页截图和 H-004 审表达均看阅读版；文件列表须由打包目录实际遍历生成，禁止手写猜测。

无程序时写明「本论文没有用到程序」；无支撑材料时写明「本论文没有支撑材料」。

---

## 四、题目拆解表（T1 用）

```markdown
| 小问 | 题面原话 | 要求交付什么 | 输入数据 | 判定"答对"的标准 | 疑难点 |
|---|---|---|---|---|---|
| 1 | "……" | 一组参数 + 依据 | 附件1 | 数值落在物理可行域且能验证 | 缺少 X 的取值 |
```

## 五、选题评分矩阵（T1 用，1–5 分加权）

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
