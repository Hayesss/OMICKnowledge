# Bowtie2

## 基本信息

- **ID**: `bowtie2`
- **类型**: tools
- **难度**: beginner
- **标签**: `atac-seq`, `alignment`, `cut-tag`

## 描述

快速且内存高效的短序列比对工具，广泛用于 ATAC-seq 和 ChIP-seq 数据的比对。

## 详细说明

Bowtie2 是一款基于 Burrows-Wheeler 变换（BWT）和 FM 索引的全基因组短序列比对工具，由 Johns Hopkins University 的 Langmead 实验室开发。相比其前代 Bowtie1，Bowtie2 引入了完全基于_seed_的启发式搜索和动态规划扩展算法，支持局部比对（local alignment）、gapped alignment 和 discordant paired-end 比对，能够更好地处理 reads 末端的错配和插入缺失（INDEL）。在 ATAC-seq 中，由于 Tn5 转座酶切割产生的片段可能跨越核小体边界或含有基因组变异导致的序列差异，Bowtie2 的局部比对模式（--local）和敏感模式（--very-sensitive）被广泛推荐。其索引构建速度快、内存占用低（人类基因组索引约 3-4 GB）、比对速度快的特点，使其成为 ATAC-seq、ChIP-seq 和 CUT&Tag 数据的标准比对工具之一。此外，Bowtie2 支持 SAM 格式输出、多线程（-p）和自定义比对质量阈值，易于与 Snakemake、Nextflow 等流程管理工具整合。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-X` | 最大插入片段大小 | 1000 |
| `--very-sensitive` | 使用高灵敏度预设参数 | false |

## 相关实体

### uses_tool

- ← [序列比对](alignment.md) - 将过滤后的 reads 比对到参考基因组，生成 BAM 文件。...

## 元信息

- **来源文件**: `content/tools/bowtie2.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
