# 质控与过滤

## 基本信息

- **ID**: `scrna-qc`
- **类型**: steps
- **难度**: beginner
- **标签**: `scRNA-seq`, `qc`, `preprocessing`

## 描述

基于基因数、UMI 数和线粒体比例过滤低质量细胞和双细胞。

## 详细说明

质控是 scRNA-seq 预处理的首要步骤。由于实验过程中会产生空液滴、死细胞和双细胞，这些低质量数据会严重干扰下游聚类和差异分析。
常用过滤标准包括：nFeature_RNA（每个细胞检测到的基因数）在 200-5000 之间；nCount_RNA（总 UMI 数）不过高；percent.mt（线粒体基因比例）< 5-10%。
对于双细胞（doublets），需要使用 Scrublet、DoubletFinder 或 Solo 等算法进行检测和去除。高质量质控能显著提高细胞聚类的清晰度和生物学可解释性。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `min_genes` | 每个细胞检测到的最小基因数 | 200 |
| `max_mt_percent` | 线粒体基因最大百分比 | 5 |

## 输入输出

- **输入**: 原始表达矩阵（h5 / mtx）
- **输出**: 过滤后的表达矩阵

## 相关实体

### has_issue

- → [双细胞（Doublets）](doublets.md) - 两个或多个细胞在液滴或微孔中被同时捕获并测序，导致其表达谱被错误地视为一个细胞。...

### has_step

- ← [数据预处理](scrna-preprocessing.md) - 对 scRNA-seq 原始数据进行比对、定量、质控和过滤，获得高质量表达矩阵。...

### prerequisite_for

- → [归一化与特征选择](scrna-normalization.md) - 消除测序深度差异，选择高变基因，为降维和聚类做准备。...

### uses_tool

- → [Cell Ranger](cellranger.md) - 10x Genomics 官方提供的 scRNA-seq 数据处理流程，用于从原始测序数据生成基因表...

## 元信息

- **来源文件**: `content/steps/scrna_qc.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
