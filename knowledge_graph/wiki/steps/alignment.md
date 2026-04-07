# 序列比对

## 基本信息

- **ID**: `alignment`
- **类型**: steps
- **难度**: beginner
- **标签**: `atac-seq`, `alignment`, `preprocessing`

## 描述

将过滤后的 reads 比对到参考基因组，生成 BAM 文件。

## 详细说明

序列比对是将经过质控的 clean reads 精确映射到参考基因组坐标的过程，是连接原始测序数据与生物学解释的桥梁。ATAC-seq 数据通常长度较短（<100 bp）且插入片段大小不一，因此需要选择支持局部比对（local alignment）和 gapped alignment 的工具。Bowtie2 是 ATAC-seq 最常用的比对器，其 --very-sensitive 参数可以在灵敏度、速度和准确性之间取得良好平衡。由于 ATAC-seq 的 Tn5 片段可能跨越核小体边界或含有 INDEL，-X 参数（最大插入片段大小，通常设为 1000-2000 bp）能帮助捕获较长的单核小体/双核小体片段。比对后需要进行严格过滤：去除未比对（unmapped）、多比对（multimapping, MAPQ < 30）和 PCR 重复 reads（duplicates），以保证进入 peak calling 的 reads 具有唯一的基因组来源和高置信度。最终输出为排序后的 BAM 文件及其索引（BAI）。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `max_insert_size` | 最大插入片段大小 | 1000 |

## 输入输出

- **输入**: 过滤后的 FASTQ 文件
- **输出**: BAM 文件

## 相关实体

### has_issue

- → [批次效应](batch-effect.md) - 由于实验时间、操作人员、试剂批次等非生物学因素导致的数据系统性差异。...

### has_step

- ← [数据预处理](preprocessing.md) - 对原始测序数据进行质量控制、比对和过滤，为后续分析准备干净的 BAM 文件。...

### prerequisite_for

- ← [质量控制](quality-control.md) - 评估原始测序数据质量，检查接头污染、测序深度、重复率等指标。...
- → [Peak 识别](peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。...

### uses_tool

- → [Bowtie2](bowtie2.md) - 快速且内存高效的短序列比对工具，广泛用于 ATAC-seq 和 ChIP-seq 数据的比对。...

## 元信息

- **来源文件**: `content/steps/alignment.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
