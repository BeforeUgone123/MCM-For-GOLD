# 可引用文献库（经典方法出处 + 本地全文）

> **这是书目库，不是阅读清单。** 74 小时内没人读得完这些论文；它存在的唯一目的，
> 是让论文引用经典方法时**不必现查、更不必编**。

## 定位与分工

| 文件 | 职责 |
|---|---|
| `methods-atlas.md` | 方法怎么选（题型 → 方法族 → 具体算法） |
| `frontier-cards.md` | 2023–2026 前沿方法的用法、翻车条件**及其出处** |
| **本文件** | **经典方法的可引用出处**，前沿卡不覆盖的部分；以及本地全文清单 |

## 引用纪律（呼应 `adversarial-gates.md` 反幻觉铁律第 3 条）

1. 本表只保证**书目字段本身**经过核验（Crossref 逐条核对，随机抽验可解析）。
   它**不代表你读过这篇文献**——未读过的只能引方法出处，不得转述其结论。
2. 引用前 MUST 确认该方法确实用在了你的模型里。为凑数量而引 = 学术不端风险。
3. 本表未收录的，宁可少引不可编引；DOI 拿不准就用 `https://doi.org/<DOI>` 实访一次。
4. 中文教材（Z 族）适合作方法出处，但**不宜作为核心结论的唯一支撑**。
5. `✔` = 本地有全文可核对细节；空白 = 仅有书目，只能引出处。

## A · 优化与规划

| 方法/主题 | 作者 | 年份 | 出处 | DOI | 全文 |
|---|---|---:|---|---|:-:|
| 非线性规划，KKT 条件的原始论文 | Harold W. Kuhn, Albert … | 1951 | Proceedings of the Second Berkeley Sympos… | `—` |  |
| 内点法开山之作 | Narendra Karmarkar | 1984 | Combinatorica, 4(4): 373–395 | `10.1007/BF02579150` |  |
| 模拟退火原始论文 | S. Kirkpatrick, C. D. G… | 1983 | Science, 220(4598): 671–680 | `10.1126/science.220.4598.671` |  |
| 遗传算法教程 | Darrell Whitley | 1994 | Statistics and Computing, 4(2): 65–85 | `10.1007/BF00175354` |  |
| 粒子群算法原始论文 | James Kennedy, Russell … | 1995 | Proceedings of ICNN'95 - International Co… | `10.1109/ICNN.1995.488968` |  |
| 蚁群算法综述，IEEE CIM 版 | Marco Dorigo, Mauro Bir… | 2006 | IEEE Computational Intelligence Magazine,… | `10.1109/MCI.2006.329691` |  |
| DEA-CCR 模型原始论文 | A. Charnes, W. W. Coope… | 1978 | European Journal of Operational Research,… | `10.1016/0377-2217(78)90138-8` |  |
| 多目标优化 NSGA-II 原始论文 | K. Deb, A. Pratap, S. A… | 2002 | IEEE Transactions on Evolutionary Computa… | `10.1109/4235.996017` |  |
| 鲁棒优化经典 | Dimitris Bertsimas, Mel… | 2004 | Operations Research, 52(1): 35–53 | `10.1287/opre.1030.0065 （原线索误作 1…` |  |
| Dantzig-Wolfe 分解原理 | George B. Dantzig, Phil… | 1960 | Operations Research, 8(1): 101–111 | `10.1287/opre.8.1.101` |  |

## B · 评价与决策

| 方法/主题 | 作者 | 年份 | 出处 | DOI | 全文 |
|---|---|---:|---|---|:-:|
| AHP 层次分析法原始论文 | Thomas L. Saaty | 1977 | Journal of Mathematical Psychology, 15(3)… | `10.1016/0022-2496(77)90033-5` |  |
| TOPSIS 方法原始专著 | Ching-Lai Hwang, Kwangs… | 1981 | Springer, Lecture Notes in Economics and … | `10.1007/978-3-642-48318-9` |  |
| 模糊集合论原始论文 | Lotfi A. Zadeh | 1965 | Information and Control, 8(3): 338–353 | `10.1016/S0019-9958(65)90241-X` |  |
| 信息论奠基之作，熵权法源头 | Claude E. Shannon | 1948 | Bell System Technical Journal, 27(3): 379… | `10.1002/j.1538-7305.1948.tb0133…` | ✔ |
| PROMETHEE 方法原始论文 | J. P. Brans, Ph. Vincke | 1985 | Management Science, 31(6): 647–656 | `10.1287/mnsc.31.6.647` |  |
| ELECTRE 方法奠基综述 | Bernard Roy | 1991 | Theory and Decision, 31(1): 49–73 | `10.1007/BF00134132` |  |
| 纳什均衡原始论文 | John F. Nash, Jr. | 1950 | Proceedings of the National Academy of Sc… | `10.1073/pnas.36.1.48` | ✔ |
| CRITIC 客观赋权法原始论文 | D. Diakoulaki, G. Mavro… | 1995 | Computers & Operations Research, 22(7): 7… | `10.1016/0305-0548(94)00059-H （原…` |  |
| AHP 通俗权威综述 | Thomas L. Saaty | 2008 | International Journal of Services Science… | `10.1504/IJSSCI.2008.017590` |  |
| VIKOR 方法对比经典 | Serafim Opricovic, Gwo-… | 2004 | European Journal of Operational Research,… | `10.1016/S0377-2217(03)00020-1` |  |

## C · 预测与时间序列

| 方法/主题 | 作者 | 年份 | 出处 | DOI | 全文 |
|---|---|---:|---|---|:-:|
| 第 4 版，ARIMA 圣经 | George E. P. Box, Gwily… | 2008 | 2008（第 4 版），Wiley, Wiley Series in Probab… | `10.1002/9781118619193` |  |
| Winters 三参数指数平滑 | Peter R. Winters | 1960 | Management Science, 6(3): 324–342 | `10.1287/mnsc.6.3.324` |  |
| Holt 双参数指数平滑 1957 报告重印 | Charles C. Holt | 2004 | International Journal of Forecasting, 20(… | `10.1016/j.ijforecast.2003.09.015` |  |
| 卡尔曼滤波原始论文 | Rudolph E. Kalman | 1960 | Journal of Basic Engineering (Trans. ASME… | `10.1115/1.3662552` | ✔ |
| ARCH 模型原始论文 | Robert F. Engle | 1982 | Econometrica, 50(4): 987–1007 | `10.2307/1912773` |  |
| GARCH 模型原始论文 | Tim Bollerslev | 1986 | Journal of Econometrics, 31(3): 307–327 | `10.1016/0304-4076(86)90063-1` |  |
| LSTM 原始论文 | Sepp Hochreiter, Jürgen… | 1997 | Neural Computation, 9(8): 1735–1780 | `10.1162/neco.1997.9.8.1735` | ✔ |
| 随机森林原始论文 | Leo Breiman | 2001 | Machine Learning, 45(1): 5–32 | `10.1023/A:1010933404324` | ✔ |
| XGBoost 原始论文 | Tianqi Chen, Carlos Gue… | 2016 | Proceedings of the 22nd ACM SIGKDD Intern… | `10.1145/2939672.2939785` | ✔ |
| 灰色系统理论原始论文 | Deng Julong（邓聚龙） | 1982 | Systems & Control Letters, 1(5): 288–294 | `10.1016/S0167-6911(82)80025-X` |  |

## D · 分类、聚类与判别

| 方法/主题 | 作者 | 年份 | 出处 | DOI | 全文 |
|---|---|---:|---|---|:-:|
| k-means 原始论文 | James MacQueen | 1967 | Proceedings of the Fifth Berkeley Symposi… | `—` | ✔ |
| Lloyd 算法，k-means 等价形式 | Stuart P. Lloyd | 1982 | IEEE Transactions on Information Theory, … | `10.1109/TIT.1982.1056489` |  |
| DBSCAN 原始论文 | Martin Ester, Hans-Pete… | 1996 | Proceedings of the Second International C… | `—` | ✔ |
| 支持向量机原始论文 | Corinna Cortes, Vladimi… | 1995 | Machine Learning, 20(3): 273–297 | `10.1007/BF00994018` |  |
| Logistic 回归奠基论文 | David R. Cox | 1958 | Journal of the Royal Statistical Society:… | `10.1111/j.2517-6161.1958.tb0029…` |  |
| Lasso 原始论文 | Robert Tibshirani | 1996 | Journal of the Royal Statistical Society:… | `10.1111/j.2517-6161.1996.tb0208…` | ✔ |
| PCA 思想源头 | Karl Pearson | 1901 | The London, Edinburgh, and Dublin Philoso… | `10.1080/14786440109462720` |  |
| PCA 正式奠基论文 | Harold Hotelling | 1933 | Journal of Educational Psychology, 24(6):… | `10.1037/h0071325` |  |
| Fisher 判别分析与鸢尾花数据集原始论文 | Ronald A. Fisher | 1936 | Annals of Eugenics, 7(2): 179–188 | `10.1111/j.1469-1809.1936.tb0213…` | ✔ |
| CART 决策树原始专著 | Leo Breiman, Jerome H. … | 1984 | Chapman & Hall/CRC（原著 Wadsworth；所列 DOI 为 … | `10.1201/9781315139470` |  |

## E · 机理建模与仿真

| 方法/主题 | 作者 | 年份 | 出处 | DOI | 全文 |
|---|---|---:|---|---|:-:|
| SIR 传染病模型原始论文 | W. O. Kermack, A. G. Mc… | 1927 | Proceedings of the Royal Society of Londo… | `10.1098/rspa.1927.0118` | ✔ |
| Metropolis 采样 / MCMC 原始论文 | Nicholas Metropolis, Ar… | 1953 | The Journal of Chemical Physics, 21(6): 1… | `10.1063/1.1699114` |  |
| 排队论 Little 定律 | John D. C. Little | 1961 | Operations Research, 9(3): 383–387 | `10.1287/opre.9.3.383` |  |
| Dijkstra 最短路算法原始论文 | Edsger W. Dijkstra | 1959 | Numerische Mathematik, 1(1): 269–271 | `10.1007/BF01386390` |  |
| Floyd 全源最短路算法原始论文 | Robert W. Floyd | 1962 | Communications of the ACM, 5(6): 345 | `10.1145/367766.368168` |  |
| PageRank 原始技术报告 | Lawrence Page, Sergey B… | 1999 | Stanford InfoLab Technical Report 1999-66… | `—` |  |
| 元胞自动机经典 | Stephen Wolfram | 1983 | Reviews of Modern Physics, 55(3): 601–644 | `10.1103/RevModPhys.55.601` |  |
| Boids 群体行为仿真原始论文 | Craig W. Reynolds | 1987 | ACM SIGGRAPH Computer Graphics (SIGGRAPH'… | `10.1145/37402.37406` |  |
| Sobol' 全局敏感性分析 | I. M. Sobol' | 2001 | Mathematics and Computers in Simulation, … | `10.1016/S0378-4754(00)00270-6` |  |
| 克里金插值综述经典 | Noel Cressie | 1990 | Mathematical Geology, 22(3): 239–252 | `10.1007/BF00889887` |  |

## Z · 中文经典（教材/专著）

| 书名 | 作者 | 年份 | 出版社/出处 |
|---|---|---:|---|
| 《数学模型（第五版）》 | 姜启源、谢金星、叶俊 | 2018 | 高等教育出版社，ISBN 978-7-04-049222-4 |
| 《数学建模算法与应用（第 3 版）》 | 司守奎、孙玺菁 | 2021 | 国防工业出版社，ISBN 978-7-118-12278-7 |
| 《数学建模方法及其应用（第 3 版）》 | 韩中庚 | 2017 | 高等教育出版社，ISBN 978-7-04-045709-4（"十二五"普… |
| 《运筹学教程（第 5 版）》 | 胡运权 主编（郭耀煌 副主编） | 2018 | 清华大学出版社，ISBN 978-7-302-48125-6 |
| 《灰色系统理论及其应用（第 9 版）》 | 刘思峰 等 | 2021 | 科学出版社，ISBN 978-7-03-067948-2 |
| 《综合评价理论、方法及应用》 | 郭亚军 | 2007 | 科学出版社，ISBN 978-7-03-018796-3 |
| 《多指标综合评价方法综述》 | 虞晓芬、傅玳 | 2004 | 《统计与决策》，2004(11): 119–121 |
| 《综合评价的方法、问题及其研究趋势》 | 王宗军 | 1998 | 《管理科学学报》，1(1): 75–81（页码各库记载不一，按万方数据记 … |
| 《将数学建模思想融入数学类主干课程》 | 李大潜（中国科学院院士，全国大学生数学… | 2006 | 《中国大学教学》，2006(1): 9–11 |
| 《确定组合预测权系数最优近似解的方法研究》 | 王明涛 | 2000 | 《系统工程理论与实践》，20(3): 104–109 |

## 本地全文清单（30 篇）

默认路径 `research/papers/`，由 `MANIFEST.sha256` 锁定。**赛前由 T0 预置**：
竞赛期间 CSDN/GitHub 等属禁入域名（见 `rules-2026.md` 检索纪律），
arXiv、Crossref、出版社官网不受此限，但网络不可靠时本地全文是唯一保障。

| 文件 | 用途 |
|---|---|
| `1927-kermack-mckendrick-epidemics.pdf` | E 传染病 SIR 模型原始论文 |
| `1936-fisher-multiple-measurements.pdf` | D 线性判别分析(LDA)原始论文 |
| `1948-shannon-mathematical-theory-communication.pdf` | B 信息论奠基，熵权法源头 |
| `1950-nash-equilibrium-points.pdf` | B 纳什均衡原始论文 |
| `1960-kalman-linear-filtering-prediction.pdf` | C 卡尔曼滤波原始论文 |
| `1967-macqueen-kmeans-classification.pdf` | D K-means 原始论文 |
| `1979-mckay-beckman-conover-lhs.pdf` | E 拉丁超立方抽样原始论文 |
| `1996-ester-dbscan-density-clusters.pdf` | D DBSCAN 原始论文 |
| `1996-tibshirani-lasso.pdf` | C LASSO 原始论文 |
| `1997-hochreiter-schmidhuber-lstm.pdf` | C LSTM 原始论文 |
| `2000-rockafellar-uryasev-cvar.pdf` | A CVaR 优化原始论文 |
| `2001-breiman-random-forests.pdf` | D 随机森林原始论文 |
| `2003-dupacova-growe-kuska-romisch-scenario-reduction.pdf` | A 情景缩减 |
| `2015-bates-etal-parsimonious-mixed-models.pdf` | CC-026 混合效应模型的简约化，随机效应结构选择 |
| `2016-chen-guestrin-xgboost.pdf` | D XGBoost 原始论文 |
| `2017-amaran-etal-simulation-optimization-review.pdf` | 第3问 响应面/仿真优化算法综述 |
| `2018-esfahani-kuhn-wasserstein-dro.pdf` | A Wasserstein DRO（前沿卡 B5 出处） |
| `2021-lei-bickel-assumption-free-exact-test-exchangeable-errors.pdf` | CC-026 小样本无假设精确检验，n=21 推断困境的替代路径 |
| `2021-shwartz-ziv-armon-tabular-deep-learning-not-all-you-need.pdf` | methods-atlas 小样本慎用神经网络的实证支撑 |
| `2021-zimmerman-etal-pseudoreplication-bias-single-cell.pdf` | CC-026 伪重复偏差实证与解法(n=21 vs 114 的直接依据) |
| `2022-model-specification-in-mixed-effects-models.pdf` | CC-026 分层数据的模型设定 |
| `2022-randall-montgomery-lewis-robust-crop-planning.pdf` | A 鲁棒作物规划应用 |
| `2023-overstall-mcgree-gibbs-optimal-design.pdf` | CC-027 模型误设下的稳健最优设计 |
| `2024-bayesian-d-optimal-column-subset-selection.pdf` | CC-027 D-最优的列子集选择视角，解释纯D-最优为何堆角点 |
| `2024-rainforth-etal-modern-bayesian-experimental-design.pdf` | CC-027 实验设计准则：BED 权威综述(Statistical Science 2024) |
| `2024-watch-treatment-effect-heterogeneity-workflow.pdf` | CC-026 异质性评估工作流(方向不一致时的处理范式) |
| `2025-actionable-treatment-effect-heterogeneity.pdf` | CC-026 效应异质性的检验与可行动性判定 |
| `2025-kuhn-shafiee-wiesemann-dro-survey-v3.pdf` | A DRO 最新综述 |
| `2026-islip-et-al-contextual-scenario-generation-v2.pdf` | A 情境生成最新进展 |
| `2026-surrogates-parametric-systems-review.pdf` | 第3问 代理模型最新综述(2026) |

