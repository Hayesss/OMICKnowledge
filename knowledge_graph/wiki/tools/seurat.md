# Seurat

## 基本信息

- **ID**: `seurat`
- **类型**: tools
- **难度**: intermediate
- **标签**: `scRNA-seq`, `R`, `clustering`, `visualization`

## 描述

R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。

## 详细说明

Seurat 是由 Satija Lab 开发的 R 包，是目前单细胞领域引用率最高、生态最完善的数据分析工具。其核心工作流包括：CreateSeuratObject、QC 过滤、Normalization、FindVariableFeatures、ScaleData、RunPCA、RunUMAP、FindNeighbors、FindClusters 和 FindAllMarkers。
Seurat v5 引入了基于 sketch 的集成分析（sketch-based integration），可以在不损失精度的前提下分析百万级细胞的数据集。此外，Seurat 还提供了丰富的扩展功能，包括空间转录组分析（Seurat v5 + SCTransform）、多模态分析（CITE-seq, scATAC+RNA）和转录调控网络推断（SCENIC）。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `dims` | 用于聚类和 UMAP 的主成分维度 | 1:30 |
| `resolution` | 聚类分辨率 | 0.8 |

## 相关实体

### applies_to

- → [scRNA-seq](scRNA-seq.md) - 单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。...

### uses_tool

- ← [归一化与特征选择](scrna-normalization.md) - 消除测序深度差异，选择高变基因，为降维和聚类做准备。...
- ← [非线性降维与聚类](scrna-clustering-step.md) - 基于共享最近邻图进行细胞聚类，并使用 UMAP 可视化高维单细胞数据。...
- ← [差异基因分析](scrna-de-step.md) - 比较不同细胞簇间的基因表达差异，识别细胞类型特异性标记基因。...

## 元信息

- **来源文件**: `content/tools/seurat.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
