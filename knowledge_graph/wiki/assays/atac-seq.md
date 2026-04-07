# ATAC-seq

## 基本信息

- **ID**: `atac-seq`
- **类型**: assays
- **难度**: intermediate
- **标签**: `atac-seq`, `epigenomics`, `chromatin-accessibility`

## 描述

利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。

## 详细说明

ATAC-seq (Assay for Transposase-Accessible Chromatin using sequencing) 是一种利用高活性 Tn5 转座酶切割并标记开放染色质区域的高通量测序技术。由于 Tn5 酶优先整合到核小体缺失的 DNA 区域，通过对这些片段进行测序，可以在全基因组范围内绘制染色质可及性图谱。ATAC-seq 具有细胞输入量低（500-50,000 个细胞）、实验周期短（数小时）、信噪比高的优势，广泛应用于鉴定启动子、增强子、绝缘子、转录因子结合位子等调控元件，以及研究细胞分化、疾病发生和药物响应中的表观遗传动态变化。

## 相关实体

### applies_to

- ← [MACS2](macs2.md) - 最常用的 ChIP-seq 和 ATAC-seq peak calling 工具，支持 narrow...

### has_stage

- → [数据预处理](preprocessing.md) - 对原始测序数据进行质量控制、比对和过滤，为后续分析准备干净的 BAM 文件。...
- → [Peak Calling](peak-calling.md) - 从比对结果中识别染色质开放区域（peaks），是 ATAC-seq 分析的核心步骤。...
- → [注释与解读](annotation.md) - 对鉴定出的 peaks 进行基因组注释，关联到附近的基因和调控元件。...

## 元信息

- **来源文件**: `content/assays/atac_seq.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
