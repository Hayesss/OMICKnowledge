# 数据预处理

## 基本信息

- **ID**: `preprocessing`
- **类型**: stages
- **难度**: beginner
- **标签**: `atac-seq`, `preprocessing`, `qc`

## 描述

对原始测序数据进行质量控制、比对和过滤，为后续分析准备干净的 BAM 文件。

## 详细说明

数据预处理是 ATAC-seq 分析流程的基石，直接决定后续 peak calling 和差异分析的可靠性。该阶段的核心任务包括：1) 原始数据质量评估（FastQC/MultiQC），检查碱基质量、GC 偏倚、接头污染和序列重复水平；2) 接头去除和低质量碱基修剪（cutadapt/Trimmomatic），确保输入比对的 reads 质量；3) 序列比对到参考基因组（Bowtie2/BWA-MEM），考虑 ATAC-seq 片段的短插入特性；4) 比对后过滤，包括去除 PCR 重复（Picard/sambamba）、过滤低质量比对（MAPQ < 30）、去除线粒体 DNA（chrM，通常占 ATAC-seq reads 的 10-50%）以及去除多比对 reads。严格的预处理能显著降低技术噪音，提高开放区域检测的灵敏度和特异性。

## 相关实体

### has_stage

- ← [ATAC-seq](atac-seq.md) - 利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。...

### has_step

- → [质量控制](quality-control.md) - 评估原始测序数据质量，检查接头污染、测序深度、重复率等指标。...
- → [序列比对](alignment.md) - 将过滤后的 reads 比对到参考基因组，生成 BAM 文件。...

## 元信息

- **来源文件**: `content/stages/preprocessing.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
