# MACS2

## 基本信息

- **ID**: `macs2`
- **类型**: tools
- **难度**: beginner
- **标签**: `atac-seq`, `cut-tag`, `peak-calling`

## 描述

最常用的 ChIP-seq 和 ATAC-seq peak calling 工具，支持 narrow、broad 和 gapped peak 模型。

## 详细说明

MACS2 (Model-based Analysis of ChIP-seq 2) 是由 Xiaole Shirley Liu 实验室开发的一款基于泊松分布模型的 peak calling 工具，广泛应用于 ChIP-seq、ATAC-seq、DNase-seq 和 CUT&Tag 数据的开放区域或蛋白结合位点检测。MACS2 的核心算法通过比较每个基因组窗口的 reads 密度与局部背景噪音（local lambda），动态评估信号显著性。针对 ATAC-seq 数据，MACS2 提供了专门的参数组合：--nomodel（跳过双峰模型构建，因为 ATAC-seq 的 fragment size 分布与 ChIP-seq 不同）、--shift -75 和 --extsize 150（模拟 150 bp 的核小体-Free 片段中心位置，修正 Tn5 插入偏移）。MACS2 的输出包括标准的 NarrowPeak/BED 格式文件、bedGraph 信号文件（可用于 IGV/UCSC 基因组浏览器）和 summit 文件。其内置的 IDR（Irreproducible Discovery Rate）支持和差异 peak 分析模块（bdgdiff）进一步扩展了其在比较表观基因组学中的应用。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-q` | q-value 阈值 | 0.05 |
| `--nomodel` | 跳过模型构建，适用于 ATAC-seq | false |
| `--shift` | reads 偏移量 | -75 |
| `--extsize` | 扩展片段大小 | 150 |

## 相关实体

### applies_to

- → [ATAC-seq](atac-seq.md) - 利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。...

### has_resource

- → [MACS2 官方文档](macs2-doc.md) - MACS2 GitHub 仓库和用户使用手册...

### uses_tool

- ← [Peak 识别](peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。...

## 元信息

- **来源文件**: `content/tools/macs2.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
