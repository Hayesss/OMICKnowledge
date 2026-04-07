# scRNA-seq

## 基本信息

- **ID**: `scRNA-seq`
- **类型**: assays
- **难度**: advanced
- **标签**: `scRNA-seq`, `transcriptomics`, `single-cell`

## 描述

单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。

## 详细说明

单细胞 RNA 测序（single-cell RNA-seq, scRNA-seq）是一类能够在单个细胞水平定量检测转录本表达的高通量技术。与传统 bulk RNA-seq 相比，scRNA-seq 可以揭示组织内不同细胞类型的异质性、识别稀有细胞亚群、重建发育分化轨迹以及解析疾病状态下细胞类型特异性的基因调控变化。
主流技术平台包括基于微流控的 10x Genomics Chromium（通量高、成本低）、基于微孔板的 Smart-seq2（全长覆盖、适合低丰度转录本）、以及基于组合索引的 Split-seq 和 sci-RNA-seq（超高通量）。
scRNA-seq 的核心分析流程包括：数据预处理（比对、定量、质控）、归一化与降维（PCA、UMAP/t-SNE）、细胞聚类与注释、差异表达分析、拟时序分析（pseudotime）、细胞通讯分析和转录因子活性推断。由于其高维度、高噪音和高缺失率（dropout）的特点，scRNA-seq 分析对计算资源和统计方法提出了较高要求。


## 相关实体

### applies_to

- ← [Cell Ranger](cellranger.md) - 10x Genomics 官方提供的 scRNA-seq 数据处理流程，用于从原始测序数据生成基因表...
- ← [Seurat](seurat.md) - R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。...

### has_stage

- → [数据预处理](scrna-preprocessing.md) - 对 scRNA-seq 原始数据进行比对、定量、质控和过滤，获得高质量表达矩阵。...
- → [聚类与注释](scrna-clustering.md) - 对 scRNA-seq 表达矩阵进行降维、聚类和细胞类型注释，揭示细胞异质性。...
- → [差异表达分析](scrna-de.md) - 比较不同细胞群体间的基因表达差异，识别细胞类型特异性标记和差异调控基因。...

## 元信息

- **来源文件**: `content/assays/scrna_seq.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
