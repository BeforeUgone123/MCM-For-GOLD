# 内置 Nature 科学图表规范

## 目录

1. 后端 Gate
2. Figure contract
3. 证据与版式
4. 统计和源数据
5. 导出与视觉 QA
6. 验收

## 后端 Gate

首次制作正文图前，确认 Python 或 R。用户已明确选择或项目已有清晰单语言绘图链时直接记录；否则只问“Python 还是 R？”并等待。

选定后，绘图、预览、SVG/PDF/TIFF/PNG 导出和视觉 QA 全部使用同一后端。缺运行时或包时停止渲染，报告准确缺口；另一语言只能做不改变视觉的数据转换。

## Figure contract

写代码前为每张 F-id 建立：

```text
Core conclusion: <一句含动词、可证伪的结论>
Role: discovery | method | main_result | comparison | validation | robustness | limitation
Archetype: quantitative_grid | schematic_led | image_plus_quant | asymmetric_mixed
Backend: Python | R
Final size: <正文实际宽高>
Panel map: <a/b/c 各自唯一证据角色>
Evidence hierarchy: <hero/validation/control>
Statistics: <n/中心/区间/检验/校正>
Source data: <文件+哈希>
Image integrity: <裁剪/对比度/伪彩/拼接/复用>
Reviewer risk: <最可能被攻击的点>
Caption boundary: <能说明与不能说明什么>
```

盖住一个面板不削弱论证时，删除或合并该面板。主证据获得最大空间，控制和稳健性视觉降级，不平均分配面板。

## 证据与版式

- 一张图只服务一个中心结论；跨图保持方法、情景和数据集颜色稳定。
- 优先直接标注和共享图例，避免重复图例与眼动往返。
- 使用白底、克制配色、矢量线条；红绿不得成为唯一编码，灰度打印仍可区分。
- 方法/流程图按逻辑流组织，不以装饰卡片替代方程和接口。
- 代表性图片必须量化并追溯原文件；比例尺经过校准，不能只写放大倍数。
- 图题和图注先陈述图展示的事实，再解释边界，不在图注新增未经验证结论。

## 统计和源数据

每个定量面板至少记录：独立样本 `n` 的定义、重复/种子/折数、中心统计量、误差条或区间、检验、比较对象、多重校正、指标定义和 source-data 文件。

机器学习或优化图额外记录：训练/验证/测试划分、种子/折数、基线定义、预算、求解状态、gap/残差和变异定义。候选池内比较不得用全局最优视觉暗示。

## 导出与视觉 QA

- 正文优先 SVG/PDF，保持文本可编辑；PNG 用于预览或规则要求。
- 竞赛不默认生成 TIFF；只有明确要求时输出高分辨率 TIFF。
- 使用正文最终尺寸渲染，检查字体、标签、图例、公式、颜色、裁剪、遮挡和空白。
- 打开实际 SVG/PDF，确认文本可选择、数字与源表一致、字体嵌入或回退正常。
- 保存脚本、源表、SVG/PDF、预览和 QA 记录；禁止只交截图。

## 验收

- 每个面板映射唯一证据角色和 C/R-id。
- 视觉层级与证据层级一致，没有美化导致的强度升级。
- 最终尺寸可读，跨图语义稳定，无重叠和裁剪。
- 数字回读、统计说明、source data 和脚本齐全。
- 图像调整全局、可解释、可追溯；选择性处理被标风险。
