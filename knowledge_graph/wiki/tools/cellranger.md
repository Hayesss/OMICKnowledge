# Cell Ranger

## 基本信息

- **ID**: `cellranger`
- **类型**: tools
- **难度**: beginner
- **标签**: `scRNA-seq`, `10x-genomics`, `preprocessing`

## 描述

10x Genomics 官方提供的 scRNA-seq 数据处理流程，用于从原始测序数据生成基因表达矩阵。

## 详细说明

Cell Ranger 是 10x Genomics 官方推出的单细胞数据分析软件套件，核心模块包括：cellranger mkfastq（将 BCL 文件转换为 FASTQ）、cellranger count（比对、定量和生成 feature-barcode 矩阵）和 cellranger aggr（合并多个样本的计数结果）。
其比对步骤基于 STAR 算法，定量基于 GTF 注释文件。输出结果包括过滤后的表达矩阵（filtered_feature_bc_matrix）、质控报告（web_summary.html）和细胞聚类预览（基于 Louvain 聚类的 t-SNE 图）。
对于非 10x 平台的数据（如 Smart-seq2、Drop-seq），需要使用其他工具如 STARsolo、alevin 或 zUMIs。


## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--transcriptome` | 参考转录组索引路径 | required |
| `--fastqs` | 原始 FASTQ 文件目录 | required |

## 相关实体

### applies_to

- → [scRNA-seq](scRNA-seq.md) - 单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。...

### uses_tool

- ← [质控与过滤](scrna-qc.md) - 基于基因数、UMI 数和线粒体比例过滤低质量细胞和双细胞。...

## 元信息

- **来源文件**: `content/tools/cellranger.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
