# 聚类与注释

## 基本信息

- **ID**: `scrna-clustering`
- **类型**: stages
- **难度**: advanced
- **标签**: `scRNA-seq`, `clustering`, `visualization`

## 描述

对 scRNA-seq 表达矩阵进行降维、聚类和细胞类型注释，揭示细胞异质性。

## 详细说明

聚类与注释是 scRNA-seq 分析的核心环节，旨在将大量单细胞按转录组相似性分组，并赋予生物学身份（细胞类型或状态）。标准流程包括：
1) 高变基因选择：筛选在不同细胞间表达差异最大的基因，减少噪音干扰；
2) 线性降维（PCA）：将高维表达矩阵投影到低维空间，保留主要变异；
3) 非线性降维（UMAP/t-SNE）：将细胞在二维/三维空间中可视化，保持局部邻域结构的同时拉开不同群体的距离；
4) 图-based 聚类（如 Louvain/Leiden 算法）：基于细胞间的共享最近邻（SNN）图结构识别细胞亚群；
5) 细胞类型注释：通过已知标记基因（marker genes）的表达模式，将聚类结果映射到经典细胞类型（如 T cell, B cell, macrophage）。自动注释工具（如 SingleR、CellTypist）可以辅助这一过程，但手工校验仍不可或缺。


## 相关实体

### has_stage

- ← [scRNA-seq](scRNA-seq.md) - 单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。...

### has_step

- → [线性降维 (PCA)](scrna-pca.md) - 使用主成分分析将高维基因表达数据投影到低维空间，保留主要变异来源。...
- → [非线性降维与聚类](scrna-clustering-step.md) - 基于共享最近邻图进行细胞聚类，并使用 UMAP 可视化高维单细胞数据。...

## 元信息

- **来源文件**: `content/stages/scrna_clustering.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
