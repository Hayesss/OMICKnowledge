# Peak Calling

## 基本信息

- **ID**: `peak-calling`
- **类型**: stages
- **难度**: intermediate
- **标签**: `atac-seq`, `peak-calling`, `regulatory-elements`

## 描述

从比对结果中识别染色质开放区域（peaks），是 ATAC-seq 分析的核心步骤。

## 详细说明

Peak calling 是 ATAC-seq 分析的核心环节，旨在从预处理后的 BAM 文件中识别统计显著的染色质开放区域（peaks）。ATAC-seq 利用 Tn5 转座酶优先切割核小体缺失区域（Nucleosome-Free Regions, NFR），这些区域会富集大量测序 reads，在基因组上形成信号峰。Peak caller（如 MACS2、HOMER、Genrich）通过建立局部背景模型（通常是泊松分布或负二项分布），比较每个基因组窗口内的 reads 密度与周围背景及对照样本的差异，从而确定显著开放的区域。针对 ATAC-seq 数据，需要特别注意参数调整：由于 Tn5 在 DNA 双链上切割后会产生 9 bp 的粘性末端，实际的开放中心位于 reads 起始位置的 +4.5 bp 处，因此通常设置 --shift -75 和 --extsize 150 来准确模拟片段中心。输出结果包括 peak 坐标（BED/NarrowPeak）、信号强度文件（bedGraph/bigWig）和质量评估指标（如 FRiP score：reads in peaks 比例）。

## 相关实体

### has_stage

- ← [ATAC-seq](atac-seq.md) - 利用转座酶可及性分析染色质开放区域的高通量测序技术，用于鉴定调控元件和潜在增强子。...

### has_step

- → [Peak 识别](peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。...

## 元信息

- **来源文件**: `content/stages/peak_calling.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
