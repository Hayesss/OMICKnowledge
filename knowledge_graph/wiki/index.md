# 多组学知识图谱索引

*最后更新: 2026-04-07 19:43*

本索引遵循 [llm-wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 构建，用于 LLM 快速定位和交叉引用知识实体。

## 概览

本项目涵盖四种组学技术（CUT&Tag、ATAC-seq、scRNA-seq、Hi-C）的分析流程、工具、概念和最佳实践。

## 实体列表

### 实验类型 (Assays)

*2 个实体*

- [ATAC-seq](assays/atac-seq.md) - 利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。
- [scRNA-seq](assays/scRNA-seq.md) - 单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。

### 分析工具 (Tools)

*4 个实体*

- [Bowtie2](tools/bowtie2.md) - 快速且内存高效的短序列比对工具，广泛用于 ATAC-seq 和 ChIP-seq 数据的比对。
- [Cell Ranger](tools/cellranger.md) - 10x Genomics 官方提供的 scRNA-seq 数据处理流程，用于从原始测序数据生成基因表达矩阵。
- [MACS2](tools/macs2.md) - 最常用的 ChIP-seq 和 ATAC-seq peak calling 工具，支持 narrow、broad 和 g...
- [Seurat](tools/seurat.md) - R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。

### 分析步骤 (Steps)

*9 个实体*

- [Peak 注释](steps/peak-annotation.md) - 将 peaks 注释到最近的基因和调控元件，分析其功能富集。
- [Peak 识别](steps/peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。
- [差异基因分析](steps/scrna-de-step.md) - 比较不同细胞簇间的基因表达差异，识别细胞类型特异性标记基因。
- [序列比对](steps/alignment.md) - 将过滤后的 reads 比对到参考基因组，生成 BAM 文件。
- [归一化与特征选择](steps/scrna-normalization.md) - 消除测序深度差异，选择高变基因，为降维和聚类做准备。
- [线性降维 (PCA)](steps/scrna-pca.md) - 使用主成分分析将高维基因表达数据投影到低维空间，保留主要变异来源。
- [质控与过滤](steps/scrna-qc.md) - 基于基因数、UMI 数和线粒体比例过滤低质量细胞和双细胞。
- [质量控制](steps/quality-control.md) - 评估原始测序数据质量，检查接头污染、测序深度、重复率等指标。
- [非线性降维与聚类](steps/scrna-clustering-step.md) - 基于共享最近邻图进行细胞聚类，并使用 UMAP 可视化高维单细胞数据。

### 关键概念 (Concepts)

*3 个实体*

- [False Discovery Rate (FDR)](concepts/fdr.md) - 错误发现率，即在所有被判定为显著的检验中，错误拒绝原假设的预期比例。
- [Fragment Size](concepts/fragment-size.md) - ATAC-seq 中 DNA 片段的大小分布，反映了核小体占位和开放染色质特征。
- [UMAP](concepts/umap.md) - 一种非线性降维算法，广泛用于单细胞数据的可视化，能够在低维空间中保留细胞间的局部和全局拓扑结构。

### 分析阶段 (Stages)

*6 个实体*

- [Peak Calling](stages/peak-calling.md) - 从比对结果中识别染色质开放区域（peaks），是 ATAC-seq 分析的核心步骤。
- [差异表达分析](stages/scrna-de.md) - 比较不同细胞群体间的基因表达差异，识别细胞类型特异性标记和差异调控基因。
- [数据预处理](stages/preprocessing.md) - 对原始测序数据进行质量控制、比对和过滤，为后续分析准备干净的 BAM 文件。
- [数据预处理](stages/scrna-preprocessing.md) - 对 scRNA-seq 原始数据进行比对、定量、质控和过滤，获得高质量表达矩阵。
- [注释与解读](stages/annotation.md) - 对鉴定出的 peaks 进行基因组注释，关联到附近的基因和调控元件。
- [聚类与注释](stages/scrna-clustering.md) - 对 scRNA-seq 表达矩阵进行降维、聚类和细胞类型注释，揭示细胞异质性。

### 常见问题 (Issues)

*2 个实体*

- [双细胞（Doublets）](issues/doublets.md) - 两个或多个细胞在液滴或微孔中被同时捕获并测序，导致其表达谱被错误地视为一个细胞。
- [批次效应](issues/batch-effect.md) - 由于实验时间、操作人员、试剂批次等非生物学因素导致的数据系统性差异。

### 外部资源 (Resources)

*1 个实体*

- [MACS2 官方文档](resources/macs2-doc.md) - MACS2 GitHub 仓库和用户使用手册

## 统计

- 总实体数: 27
- 关系数: 37
- 最后导出: 2026-04-07 19:43

## 导航

- [综合总结](synthesis.md) - 跨实体知识综合
- [变更日志](log.md) - 知识库演进历史
- [项目 README](../README.md) - 项目概述

## 如何使用

作为 LLM，你可以：

1. **查询**: 先阅读此索引找到相关实体，再深入阅读实体页面
2. **关联**: 通过页面内的交叉引用发现相关知识
3. **综合**: 基于多个实体信息生成综合回答
4. **维护**: 协助更新 wiki 页面，保持与 YAML 源文件同步

---

*本索引由 llm-wiki 系统自动生成*
