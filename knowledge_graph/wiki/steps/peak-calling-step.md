# Peak 识别

## 基本信息

- **ID**: `peak-calling-step`
- **类型**: steps
- **难度**: intermediate
- **标签**: `atac-seq`, `peak-calling`

## 描述

使用 peak caller 从 BAM 文件中识别染色质开放区域。

## 详细说明

Peak 识别步骤使用专门的统计算法从比对后的 BAM 文件中检测显著的 reads 富集区域，即染色质开放位点。针对 ATAC-seq 数据，最核心的工具是 MACS2，其 callpeak 命令通过比较每个基因组窗口的 reads 密度与局部背景（考虑测序深度和信号波动）来判断显著性。由于 ATAC-seq 没有 Input 对照，MACS2 会自动构建局部 lambda 背景模型。关键参数调优包括：--nomodel（跳过模型构建，直接指定 shift/extsize）、--shift -75（将 reads 向 3' 端偏移 75 bp）、--extsize 150（将片段扩展至 150 bp 以模拟核小体-Free 片段中心）、-q 0.05（q-value 阈值）。输出文件主要包括 NarrowPeak（包含 peak 坐标、信号强度、p-value、q-value 和 peak summit 位置）和 bedGraph/bigWig（用于基因组浏览器可视化）。评估 peak calling 质量的常用指标是 FRiP（Fraction of Reads in Peaks），优质 ATAC-seq 数据的 FRiP 通常在 0.2-0.5 之间。

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `qvalue` | q-value 阈值 | 0.05 |
| `nomodel` | 是否跳过模型构建 | false |

## 输入输出

- **输入**: 过滤后的 BAM 文件
- **输出**: Peak 文件（BED/NarrowPeak）

## 相关实体

### has_step

- ← [Peak Calling](peak-calling.md) - 从比对结果中识别染色质开放区域（peaks），是 ATAC-seq 分析的核心步骤。...

### prerequisite_for

- ← [序列比对](alignment.md) - 将过滤后的 reads 比对到参考基因组，生成 BAM 文件。...
- → [Peak 注释](peak-annotation.md) - 将 peaks 注释到最近的基因和调控元件，分析其功能富集。...

### requires_concept

- → [False Discovery Rate (FDR)](fdr.md) - 错误发现率，即在所有被判定为显著的检验中，错误拒绝原假设的预期比例。...

### uses_tool

- → [MACS2](macs2.md) - 最常用的 ChIP-seq 和 ATAC-seq peak calling 工具，支持 narrow...

## 元信息

- **来源文件**: `content/steps/peak_calling_step.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
