#!/usr/bin/env bash
# 环境探针：T0 与每次换机器/换会话时先跑，读实际输出再决定 CONFIG。
# 目的是把「静默失败」提前到开赛前暴露——尤其是中文字体与联网检索这两项，
# 它们不会报错，只会在出图/写参考文献时才发现，那时已来不及。
set -u

echo "=== 1. Python 与关键包 ==="
python3 -V 2>&1
for p in numpy scipy pandas matplotlib sklearn statsmodels sympy networkx pulp cvxpy openpyxl SALib; do
  python3 - "$p" <<'PY' 2>/dev/null || echo "  $p  MISSING"
import importlib, sys
m = importlib.import_module(sys.argv[1])
print(f"  {sys.argv[1]:<12} {getattr(m,'__version__','ok')}")
PY
done

echo
echo "=== 2. 求解器（实跑，不只是 import）==="
# 必须真解一次：某些求解器 import 正常、solve 时直接段错误（进程崩，非 Python 异常，
# 赛场上表现为「脚本没输出就没了」，极难排查）。这里用独立子进程隔离，崩了也不影响探针。
python3 -c "
import pulp
p=pulp.LpProblem('t',pulp.LpMaximize); x=pulp.LpVariable('x',0,10)
p+=x; p+=x<=4; p.solve(pulp.PULP_CBC_CMD(msg=0))
print('  pulp/CBC   实解 OK  obj=%.1f'%pulp.value(p.objective))
" 2>/dev/null || echo "  pulp/CBC   实解失败（exit=$?；139=段错误）"
python3 -c "
import cvxpy as cp, numpy as np
v=cp.Variable(2); pr=cp.Problem(cp.Minimize(cp.sum_squares(v-np.array([1.,2.]))),[cp.sum(v)<=2])
pr.solve()
print('  cvxpy      实解 OK  solver=%s obj=%.4f'%(pr.solver_stats.solver_name, pr.value))
print('  可用求解器:', cp.installed_solvers())
" 2>/dev/null || {
  echo "  cvxpy      默认求解失败（exit=$?；139=段错误，常见于 aarch64 上的 osqp 1.x）"
  echo "             → 逐个试 solver=CLARABEL/SCS/HIGHS，找到能用的就在代码里显式指定；"
  echo "               或 pip3 uninstall -y osqp 让 cvxpy 回退到 CLARABEL"
}
command -v glpsol >/dev/null && echo "  glpk: $(command -v glpsol)" || echo "  glpk: 无（可选）"

echo
echo "=== 3. LaTeX 链路 ==="
for c in xelatex pdflatex latexmk bibtex pandoc; do
  p=$(command -v $c 2>/dev/null) && echo "  $c -> $p" || echo "  $c  缺失"
done
for s in ctexart.cls xeCJK.sty booktabs.sty algorithm2e.sty algpseudocode.sty natbib.sty; do
  kpsewhich "$s" >/dev/null 2>&1 && echo "  $s  OK" || echo "  $s  缺失"
done
latex_probe_dir=$(mktemp -d)
trap 'rm -rf "$latex_probe_dir"' EXIT
printf '%s\n' '\documentclass[fontset=fandol]{ctexart}' '\begin{document}中文 PDF probe\end{document}' > "$latex_probe_dir/ctex_probe.tex"
if command -v xelatex >/dev/null 2>&1 && (cd "$latex_probe_dir" && xelatex -interaction=nonstopmode -halt-on-error ctex_probe.tex >/dev/null 2>&1); then
  echo "  ctexart 中文最小编译  OK"
else
  echo "  ctexart 中文最小编译  失败（单个 .cls/.sty 存在不代表依赖闭包完整）"
  printf '%s\n' '\documentclass{article}' '\usepackage{fontspec}' '\usepackage{xeCJK}' '\setCJKmainfont{FandolSong-Regular}' '\begin{document}中文 PDF probe\end{document}' > "$latex_probe_dir/xecjk_probe.tex"
  if command -v xelatex >/dev/null 2>&1 && (cd "$latex_probe_dir" && xelatex -interaction=nonstopmode -halt-on-error xecjk_probe.tex >/dev/null 2>&1); then
    echo "  article + xeCJK 中文最小编译  OK（可作为降级链路）"
  else
    echo "  article + xeCJK 中文最小编译  失败（T7 前必须修复）"
  fi
fi
echo "  ↑ 无 latexmk → 用 'xelatex 连跑两遍' 出交叉引用"
echo "  ↑ 无 bibtex/natbib → 参考文献必须手写 \\begin{thebibliography}，禁用 \\bibliography{}"

echo
echo "=== 4. 中文字体（最易静默出豆腐块）==="
fc-list :lang=zh family 2>/dev/null | tr ',' '\n' | sort -u | head -20
python3 - <<'PY' 2>/dev/null
import matplotlib.font_manager as fm
names = {f.name for f in fm.fontManager.ttflist}
want = ["SimHei","SimSun","Microsoft YaHei","Noto Sans CJK SC","WenQuanYi Micro Hei","FandolHei","FandolSong","PingFang SC","Heiti SC"]
hit = [w for w in want if w in names]
print("  matplotlib 可用中文字体:", hit or "【无】——出图必为豆腐块，须先装字体或改用可用字体名")
if hit:
    print(f"  建议写法: plt.rcParams['font.sans-serif']=['{hit[0]}']; plt.rcParams['axes.unicode_minus']=False")
PY

echo
echo "=== 5. 联网检索能力（决定 research.online 取值）==="
for u in https://www.mcm.edu.cn/ https://pypi.tuna.tsinghua.edu.cn/simple/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 8 "$u" 2>/dev/null)
  echo "  $u -> ${code:-失败}"
done
echo "  ↑ 若 agent 自身无 web_search/fetch 工具，MUST 置 research.online=false，"
echo "    在论文中如实说明数据来源，并**禁止编造 SOURCES 条目去过 T2 Gate**。"

echo
echo "=== 6. 硬件与磁盘 ==="
echo "  CPU: $(nproc 2>/dev/null || sysctl -n hw.ncpu) 核"
free -h 2>/dev/null | awk '/Mem/{print "  内存: "$2" 可用 "$7}' || echo "  内存: $(sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1073741824" GB"}')"
df -h . | tail -1 | awk '{print "  当前盘: "$4" 可用 ("$5" 已用)"}'

echo
echo "缺包补齐（按需）: pip3 install --user pandas statsmodels sympy networkx pulp cvxpy openpyxl SALib -i https://pypi.tuna.tsinghua.edu.cn/simple"
