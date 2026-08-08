# MCM-Result 输出目录契约

所有新建、生成、下载、转换或审查得到的工作文件，统一写入当前工作目录下的 `MCM-Result/`。目录不存在时先创建；已存在时补齐缺失子目录，不删除、不清空、不覆盖冻结文件。不得在当前工作目录另建 `workspace/`、`paper/`、`data/`、`src/`、`figures/`、`deliverables/`、`logs/` 等平行输出目录。

固定目录如下，名称和大小写不得自行改写：

```text
MCM-Result/
├── Reference-Papers/       # 参考论文、参考文献、引用记录、检索日志
├── Data-Scripts/           # 数据处理、建模、验证、绘图与复现脚本及配置
├── Competition-Materials/  # 官方赛题、官方数据、附件、模板、规则与只读原件
├── Paper-Outputs/          # 论文源文件、阅读版、提交版、支撑包与最终交付物
├── Data-Figures/           # 数据图、正文图、图源表与最终尺寸预览
├── Intermediate-Outputs/   # 状态台账、处理数据、运行日志和其他中间输出
└── Review-Results/         # AI review 的阶段矩阵、结构化报告、契约与 QA 结果
```

## 路径规则

- 启动时把 `MCM-Result` 解析为绝对路径并记为 `result_root`；所有相对路径均以它为根。
- 官方输入保留原件，并复制或冻结到 `Competition-Materials/`；不得原地修改用户提供的文件。
- 程序、配置、依赖和复现入口放入 `Data-Scripts/`。程序产生的数据、缓存和日志放入 `Intermediate-Outputs/`，图及图源表放入 `Data-Figures/`。
- `SOURCES.md`、参考文献库、下载的论文和引用核验记录放入 `Reference-Papers/`。
- 论文源码、PDF/DOCX、AI 使用详情、提交白名单、支撑包和回执放入 `Paper-Outputs/`。
- AI review 形成的 CSV/JSON/YAML/Markdown 结构化检查结果放入 `Review-Results/`；对应原始命令输出仍放 `Intermediate-Outputs/logs/`，并由 review 文件引用。
- 允许在七个固定目录内建立语义明确的子目录，例如 `Data-Scripts/src/`、`Paper-Outputs/paper/`、`Paper-Outputs/deliverables/`。不得增加第八个一级目录。
- 临时目录也必须位于 `Intermediate-Outputs/tmp/`。需要干净环境复现时，在其中创建唯一目录，完成后保留日志和清单。
- 旧任务若已有其他布局，不静默搬动或覆盖；先登记路径映射和迁移风险，再把后续新增产物写入本契约目录。

## 缓存与构建产物的落点（曾长期未被执行）

上面「程序产生的数据、缓存和日志放入 `Intermediate-Outputs/`」一条此前没有任何机检，于是从未被执行。2025C 实测：`Data-Scripts/` 变成 408 MB / 14652 个文件，其中 407 MB 是 `.venv`，真实源码只有 16 个——人类打开源码目录第一眼看到的是虚拟环境。同期 `Paper-Outputs/paper/` 里 `.aux`/`.log` 与 `.tex` 混放。逐条落实：

- **虚拟环境**放 `Intermediate-Outputs/venv/`，不放 `Data-Scripts/.venv`。`__pycache__`、`*.pyc`、`node_modules` 同理，一律不得出现在 `Data-Scripts/`、`Paper-Outputs/`、`Data-Figures/` 下。
  Python 每跑一次就会在源码旁写 `__pycache__/`，靠事后清理必然反复失守；在跑之前设一次
  `export PYTHONPYCACHEPREFIX="$PWD/Intermediate-Outputs/pycache"`（或 `PYTHONDONTWRITEBYTECODE=1`）即可从源头改道。
- **LaTeX 中间产物**（`.aux .log .out .toc .fls .fdb_latexmk .synctex.gz .bbl .blg`）写到 `Intermediate-Outputs/`，不留在 `Paper-Outputs/`。留在那里会被误当成正式产物，也可能被打进支撑包。
- **结果台账** `RESULTS.md` / `RESULTS.jsonl` MUST 落在 `Intermediate-Outputs/`。`run_all.py` 的 `STATE_DIR` 默认是相对 cwd 的 `workspace/`，从别的目录调用会把台账写到工作区之外；跑的时候显式传 `--state-dir` 或设 `MCM_STATE_DIR`。2025C 实测踩中：论文与终检契约都在，台账却被写进会话临时目录、跑完即消失，契约当时读到的 12 行事后无处可查——**结论仍然成立，但支撑它的证据链断了**。

## 人类 review 入口

工作区根的 `README.md` 由 `templates/verify_output_layout.py --write-index` 扫描实际文件生成，是人类 review 的唯一入口：成品（论文 / 图 / 支撑包）、怎么核（台账、契约状态、复现命令）、过程（STATE、DECISIONS、日志）各一节。

它**只做导航，不复制被指向文件的内容**——复制会产生两处不一致，而不一致的索引比没有索引更容易误导 review。因此它也不写生成时间和文件大小：那会让每次重编译 PDF 都触发「过期」，把警告变成噪音。手改索引或产物增删后未刷新，校验时报 `REVIEW_INDEX_STALE`。

## 校验

```bash
python3 templates/init_result_workspace.py --workdir .          # 幂等创建七个目录
python3 templates/verify_output_layout.py --workspace MCM-Result --write-index   # 刷新索引
python3 templates/verify_output_layout.py --workspace MCM-Result                 # 只校验
```
