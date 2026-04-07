# UMAP

## 基本信息

- **ID**: `umap`
- **类型**: concepts
- **难度**: intermediate
- **标签**: `scRNA-seq`, `dimensionality-reduction`, `visualization`

## 描述

一种非线性降维算法，广泛用于单细胞数据的可视化，能够在低维空间中保留细胞间的局部和全局拓扑结构。

## 详细说明

UMAP（Uniform Manifold Approximation and Projection）是一种基于流形学习和拓扑数据理论的降维算法。与 t-SNE 相比，UMAP 在保持局部结构的同时更好地保留了全局结构（如簇间的相对距离），且计算速度更快、可扩展到更大规模的数据集。
在 scRNA-seq 分析中，UMAP 通常作用于 PCA 降维后的结果（前 10-50 个主成分），通过构建高维空间的模糊拓扑表示，并在低维空间中找到最优映射。关键参数 n_neighbors 控制局部与全局结构的平衡：较小的值（5-15）强调局部细节，较大的值（30-50）保留更多全局拓扑。
需要特别注意的是，UMAP 是一种可视化工具，其嵌入空间中的距离不具有生物学上的严格定量意义，不能直接用于推断细胞间的真实转录组相似性。


## 相关实体

### requires_concept

- ← [线性降维 (PCA)](scrna-pca.md) - 使用主成分分析将高维基因表达数据投影到低维空间，保留主要变异来源。...

## 元信息

- **来源文件**: `content/concepts/umap.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
