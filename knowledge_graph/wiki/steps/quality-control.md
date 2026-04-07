# 质量控制

## 基本信息

- **ID**: `quality-control`
- **类型**: steps
- **难度**: beginner
- **标签**: `atac-seq`, `qc`, `preprocessing`

## 描述

评估原始测序数据质量，检查接头污染、测序深度、重复率等指标。

## 详细说明

质量控制是确保 ATAC-seq 数据可靠性的第一道关口，必须在进入下游分析之前系统评估。关键质控指标包括：1) 碱基质量：Q30 比例应 > 85%，确保测序准确性；2) 接头污染：接头序列比例应 < 10%，过高会影响比对率；3) 重复率：PCR 重复比例理想情况下 < 20-30%，过高提示文库复杂度不足；4) 线粒体 reads 比例：ATAC-seq 中线粒体 DNA 通常占 10-50%，过高的比例（> 60%）可能提示细胞状态不佳或核膜破裂；5) 比对率：唯一比对率应 > 70%；6) Fragment size 分布：应呈现明显的核小体周期性峰（~50 bp NFR、~200 bp 单核小体、~400 bp 双核小体），这是 ATAC-seq 数据质量的"指纹"特征。综合这些指标，可以判断实验是否成功、是否需要重新建库或调整分析参数。常用质控工具包括 FastQC、MultiQC 和 ATACseqQC。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `adapter_sequence` | 接头序列，用于去除接头污染 | auto-detect |

## 输入输出

- **输入**: 原始 FASTQ 文件
- **输出**: 质控报告（HTML/TXT）

## 相关实体

### has_step

- ← [数据预处理](preprocessing.md) - 对原始测序数据进行质量控制、比对和过滤，为后续分析准备干净的 BAM 文件。...

### prerequisite_for

- → [序列比对](alignment.md) - 将过滤后的 reads 比对到参考基因组，生成 BAM 文件。...

### requires_concept

- → [Fragment Size](fragment-size.md) - ATAC-seq 中 DNA 片段的大小分布，反映了核小体占位和开放染色质特征。...

## 元信息

- **来源文件**: `content/steps/quality_control.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
