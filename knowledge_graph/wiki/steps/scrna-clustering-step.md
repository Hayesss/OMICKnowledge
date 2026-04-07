# 非线性降维与聚类

## 基本信息

- **ID**: `scrna-clustering-step`
- **类型**: steps
- **难度**: advanced
- **标签**: `scRNA-seq`, `clustering`, `umap`, `visualization`

## 描述

基于共享最近邻图进行细胞聚类，并使用 UMAP 可视化高维单细胞数据。

## 详细说明

在 PCA 降维后，scRNA-seq 聚类通常采用图-based 方法：首先基于欧氏距离或关联距离构建细胞的 k-NN 图，然后转换为共享最近邻（SNN）图，最后使用 Louvain 或 Leiden 算法识别社区结构（即细胞簇）。
resolution 参数直接控制簇的粒度：低分辨率（0.4-0.8）得到大类（如 T/B cell），高分辨率（1.2-2.0）得到更细的亚型（如 CD4+ Treg vs Th17）。
UMAP（Uniform Manifold Approximation and Projection）是目前最流行的单细胞可视化方法，它能在保留局部细胞邻域关系的同时，将不同群体在二维空间中拉开距离。但需要注意，UMAP 距离不反映真实的转录组距离，不能用于定量比较。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `resolution` | 聚类分辨率，越高则簇越细 | 0.8 |
| `n_neighbors` | UMAP 的最近邻数量 | 30 |

## 输入输出

- **输入**: 主成分坐标（PC scores）
- **输出**: 细胞聚类标签和 UMAP 坐标

## 相关实体

### has_step

- ← [聚类与注释](scrna-clustering.md) - 对 scRNA-seq 表达矩阵进行降维、聚类和细胞类型注释，揭示细胞异质性。...

### prerequisite_for

- ← [线性降维 (PCA)](scrna-pca.md) - 使用主成分分析将高维基因表达数据投影到低维空间，保留主要变异来源。...
- → [差异基因分析](scrna-de-step.md) - 比较不同细胞簇间的基因表达差异，识别细胞类型特异性标记基因。...

### uses_tool

- → [Seurat](seurat.md) - R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。...

## 元信息

- **来源文件**: `content/steps/scrna_clustering_step.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
