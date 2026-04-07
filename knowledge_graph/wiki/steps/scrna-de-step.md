# 差异基因分析

## 基本信息

- **ID**: `scrna-de-step`
- **类型**: steps
- **难度**: advanced
- **标签**: `scRNA-seq`, `differential-expression`, `markers`

## 描述

比较不同细胞簇间的基因表达差异，识别细胞类型特异性标记基因。

## 详细说明

差异基因分析（FindAllMarkers / FindMarkers）旨在识别在特定细胞簇中高表达而在其他簇中低表达的基因，这些基因通常可作为细胞类型的标记基因（marker genes）。
Seurat 默认使用 Wilcoxon rank-sum test，但也支持 MAST、DESeq2 等多种方法。常用过滤标准包括：平均 log2 fold change > 0.25；在目标群体中表达的细胞比例 > 10%；校正后 p-value < 0.05。
除了单细胞水平的差异分析，pseudobulk 方法（将同一群体的细胞 UMI 加总后使用 DESeq2/EdgeR）近年来被认为在控制假阳性方面表现更优，尤其适用于存在强批次效应的数据集。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `logfc_threshold` | 最小 log2  fold change 阈值 | 0.25 |
| `min_pct` | 基因在群体中表达的最小细胞比例 | 0.1 |

## 输入输出

- **输入**: 聚类标签和表达矩阵
- **输出**: 差异基因列表（logFC, p-value, adjusted p-value）

## 相关实体

### has_step

- ← [差异表达分析](scrna-de.md) - 比较不同细胞群体间的基因表达差异，识别细胞类型特异性标记和差异调控基因。...

### prerequisite_for

- ← [非线性降维与聚类](scrna-clustering-step.md) - 基于共享最近邻图进行细胞聚类，并使用 UMAP 可视化高维单细胞数据。...

### uses_tool

- → [Seurat](seurat.md) - R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。...

## 元信息

- **来源文件**: `content/steps/scrna_de_step.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
