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

使用 `templates/init_result_workspace.py` 幂等创建并回读这七个目录。
