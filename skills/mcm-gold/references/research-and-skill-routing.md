# 分阶段调研与本机 Skill 路由

## 一、调研深度

调研必须服务一个未决 claim、参数、机理或路线选择，不能为了“看起来先进”堆方法名。

| depth | 典型时间盒 | 最低产物 | 适用 |
|---|---:|---|---|
| `off` | 0 | 题面/附件来源 | 禁止外部检索或无需外部事实 |
| `light` | 15-30 min | 3-5 个权威来源 + 缺口 | 普通背景、已知方法核验 |
| `standard` | 45-90 min | 方法候选矩阵 + 适用/失效条件 + 推荐 | 主路线选择、关键参数 |
| `deep` | 2-4 h | 系统检索、前向/反向追踪、PoC、负例和人裁决简报 | 高影响且仍有 >36h、路线不可逆或创新点需成立 |

正式赛时只有在人已确认“值得花这段时间”或配置中有预授权时进入 `deep`。演练可主动深调研，但必须记录真实耗时。

## 二、路线调研产物

每个候选方法一行：`method_id | mathematical_family | exact_problem_fit | required_data | baseline | expected_gain | failure_modes | validation_burden | implementation_time | compute_budget | primary_sources | source_status | PoC_status | human_decision | paper_claim_boundary`。

检索顺序：官方规则/数据文档 → 领域机理/标准 → 原始方法论文/官方文档 → 综述作导航。搜索结果摘要和 AI 总结都不能直接成为论文引用。

先完成候选矩阵再由人选主路线，禁止让算法名自动决定论文结构或写完后反向找文献装饰。数据不满足方法前提时，记录“否决”本身也是有效调研结果。

## 三、新兴方法纪律

- 新方法必须解决具体痛点并与同数据、同预算基线比较；无真实样本时，不得把数据驱动 DRO、情境生成、深度学习或因果方法包装成可靠估计，模拟数据只能回答所设情景。
- 报告负结果和失效模式；最后 8h 不引入新模型，任何时候都不让文献数量替代实际计算和人的题意判断。

## 四、内置 Nature 能力路由

Nature 能力已直接写入本 skill 群，不再调用外部 `nature-*` skill。按证据缺口读取最小参考文件，并在 `NATURE_QA.csv` 记录实际验收。总则见 `nature-integrated-playbook.md`。

| 缺口 | 内置参考 | 进入竞赛证据链的产物 | 硬边界 |
|---|---|---|---|
| claim、来源和数据证据 | `nature-evidence-data.md` | 句段--来源支撑等级、SOURCE_DATA_MAP、必要的引用导出 | 普通国赛不限CNS；metadata-only不得进论文，不虚构仓储/许可 |
| 主图论证与出版级导出 | `nature-figures.md` | figure contract、脚本、源表、SVG/PDF、预览和视觉QA | 后端确认后全链独占；美化不能替代模型检验，竞赛版不强制TIFF |
| 论证、摘要、翻译与润色 | `nature-writing-office.md` | SourceModel、结构审查、证据一致文本和修订说明 | 不从零代写核心论证，不新增事实、机制、数值或引用 |
| DOCX/PPTX | `nature-writing-office.md` + `officecli` | DocumentSpec/SlideSpec、实际可编辑文件与QA | LaTeX不绕到Office；产物须回读、渲染和结构核验 |
| 人工/评委反馈 | `nature-feedback.md` | 原评论、逐条动作、修改位置、证据与未决人输入 | 不伪造已修改、页码或实验；不能替代H-004/H-005 |

T7 先写唯一 `MCM_SOURCE_MODEL.yaml`；每张主图建立图合同并合入 `FIGURE_EVIDENCE.csv`。引用按句段评支撑强度，数据按 claim 映射实际文件/哈希，收到反馈则逐条闭环。内置 Nature 产物始终受 MCM Gate 和人类签署约束。

## 五、等待人裁决时

AI 可继续清点附件、核哈希、补来源元数据、做小规模 PoC、准备对照、建立测试与复现脚本，但不得把等待中的候选路线或内置 Nature 产物悄悄晋升为 paper-ready。
