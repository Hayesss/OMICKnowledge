# 数据预处理

## 基本信息

- **ID**: `scrna-preprocessing`
- **类型**: stages
- **难度**: intermediate
- **标签**: `scRNA-seq`, `preprocessing`, `qc`

## 描述

对 scRNA-seq 原始数据进行比对、定量、质控和过滤，获得高质量表达矩阵。

## 详细说明

scRNA-seq 数据预处理是决定下游分析可靠性的关键步骤。对于 10x Genomics 数据，通常使用 Cell Ranger 进行 demultiplexing、基因组比对（基于 STAR）、基因定量并生成基因-条形码表达矩阵（feature-barcode matrix）。
质控环节需要过滤低质量细胞：1) 检测到的基因数（nFeature）过少（可能为空液滴/死细胞）或过多（可能是双细胞）；2) 线粒体基因比例过高（通常 >5-10% 提示细胞膜破裂、细胞质 RNA 流失）；3) 总 UMI 数（nCount）异常。常用阈值因组织类型和实验平台而异。
此外，需要根据空液滴和双细胞检测算法（如 EmptyDrops、DoubletFinder/Scrublet）进一步过滤。最终获得一个相对干净的高维稀疏表达矩阵，供下游归一化和聚类分析使用。


## 相关实体

### has_stage

- ← [scRNA-seq](scRNA-seq.md) - 单细胞转录组测序技术，用于在单个细胞分辨率下解析基因表达谱，揭示细胞异质性、发育轨迹和疾病机制。...

### has_step

- → [质控与过滤](scrna-qc.md) - 基于基因数、UMI 数和线粒体比例过滤低质量细胞和双细胞。...
- → [归一化与特征选择](scrna-normalization.md) - 消除测序深度差异，选择高变基因，为降维和聚类做准备。...

## 元信息

- **来源文件**: `content/stages/scrna_preprocessing.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
