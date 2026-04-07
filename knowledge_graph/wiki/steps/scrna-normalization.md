# 归一化与特征选择

## 基本信息

- **ID**: `scrna-normalization`
- **类型**: steps
- **难度**: intermediate
- **标签**: `scRNA-seq`, `normalization`, `feature-selection`

## 描述

消除测序深度差异，选择高变基因，为降维和聚类做准备。

## 详细说明

由于不同细胞的测序深度和捕获效率存在差异，原始 UMI 计数不能直接比较。归一化的目标是消除这些技术性差异，同时保留生物学变异。
常用方法包括：1) 文库大小归一化（CPM、 scran pool-based normalization）；2) Log 变换（log1p）；3) 高变基因选择（vst、mean.var.plot），通常选取 2000 个高变基因用于下游 PCA 和聚类。
近年来，基于深度学习的归一化方法（如 scVI、DCA）也逐渐流行，它们能同时处理批次效应、dropout 和过离散问题。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `n_features` | 选择的高变基因数量 | 2000 |
| `normalization_method` | 归一化方法 | LogNormalize |

## 输入输出

- **输入**: 过滤后的表达矩阵
- **输出**: 归一化后的高变基因矩阵

## 相关实体

### has_step

- ← [数据预处理](scrna-preprocessing.md) - 对 scRNA-seq 原始数据进行比对、定量、质控和过滤，获得高质量表达矩阵。...

### prerequisite_for

- ← [质控与过滤](scrna-qc.md) - 基于基因数、UMI 数和线粒体比例过滤低质量细胞和双细胞。...
- → [线性降维 (PCA)](scrna-pca.md) - 使用主成分分析将高维基因表达数据投影到低维空间，保留主要变异来源。...

### uses_tool

- → [Seurat](seurat.md) - R 语言中最流行的单细胞转录组数据分析工具包，提供完整的质控、归一化、降维、聚类和可视化流程。...

## 元信息

- **来源文件**: `content/steps/scrna_normalization.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
