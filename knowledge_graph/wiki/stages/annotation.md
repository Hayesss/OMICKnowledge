# 注释与解读

## 基本信息

- **ID**: `annotation`
- **类型**: stages
- **难度**: intermediate
- **标签**: `atac-seq`, `annotation`, `functional-analysis`

## 描述

对鉴定出的 peaks 进行基因组注释，关联到附近的基因和调控元件。

## 详细说明

注释与解读阶段将抽象的基因组坐标（peaks）转化为具体的生物学功能和调控机制。该阶段通常包括三个层次的分析：1) 基因组位置注释，利用 ChIPseeker、HOMER 或 GREAT 等工具，将 peaks 映射到最近的基因（通常以转录起始位点 TSS 为中心），并分类到启动子、5'UTR、外显子、内含子、基因间区等基因组特征；2) 调控元件注释，通过与已知的增强子、沉默子、绝缘子数据库（如 VISTA Enhancer Browser、FANTOM5、ENCODE cCRE）比对，识别潜在的功能性调控序列；3) 功能富集分析，对 peak 关联基因进行 GO（Gene Ontology）、KEGG 通路、GSEA 和 motif 富集分析（如使用 HOMER、MEME-ChIP），揭示转录因子结合模式、信号通路激活状态和疾病关联。高质量的注释结果可以帮助研究者从海量的表观基因组数据中提炼出有意义的生物学假设。

## 相关实体

### has_stage

- ← [ATAC-seq](atac-seq.md) - 利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。...

### has_step

- → [Peak 注释](peak-annotation.md) - 将 peaks 注释到最近的基因和调控元件，分析其功能富集。...

## 元信息

- **来源文件**: `content/stages/annotation.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
