# Peak 注释

## 基本信息

- **ID**: `peak-annotation`
- **类型**: steps
- **难度**: intermediate
- **标签**: `atac-seq`, `annotation`

## 描述

将 peaks 注释到最近的基因和调控元件，分析其功能富集。

## 详细说明

Peak 注释步骤将 peak calling 得到的基因组坐标转化为可理解的生物学功能和调控关联。首先，使用注释工具（如 ChIPseeker、HOMER annotatePeaks、GREAT）将每个 peak 分配到最近的基因（通常按 TSS 距离排序）和基因组功能区（启动子、5'UTR、外显子、内含子、基因间区）。启动子区（通常定义为 TSS ± 3 kb）的 peaks 通常与基因转录激活直接相关；基因间区的 peaks 则可能是远程增强子或沉默子。其次，进行 motif 富集分析（HOMER、MEME-ChIP），识别在这些开放区域中富集的转录因子结合 motif，从而推断调控网络。最后，对 peak 关联基因进行功能富集分析（clusterProfiler、DAVID、Enrichr），揭示这些基因参与的 GO 生物学过程、KEGG 代谢通路和疾病关联。注释结果通常以表格和可视化图（如 peak 分布饼图、TSS 热图、通路气泡图）的形式呈现。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `tss_distance` | 距离 TSS 的最大范围 | 3000 |

## 输入输出

- **输入**: Peak 文件（BED）
- **输出**: 注释结果表

## 相关实体

### has_step

- ← [注释与解读](annotation.md) - 对鉴定出的 peaks 进行基因组注释，关联到附近的基因和调控元件。...

### prerequisite_for

- ← [Peak 识别](peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。...

## 元信息

- **来源文件**: `content/steps/peak_annotation.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
