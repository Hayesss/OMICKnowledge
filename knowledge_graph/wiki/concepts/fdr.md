# False Discovery Rate (FDR)

## 基本信息

- **ID**: `fdr`
- **类型**: concepts
- **难度**: intermediate
- **标签**: `statistics`, `peak-calling`, `differential-analysis`

## 描述

错误发现率，即在所有被判定为显著的检验中，错误拒绝原假设的预期比例。

## 详细说明

FDR = E[V/R | R > 0] * P(R > 0)，其中 V 是假阳性数，R 是总拒绝数。
在 peak calling 中，常用 q-value 控制 FDR。与 p-value 相比，FDR 更适合大规模多重检验场景。


## 相关实体

### requires_concept

- ← [Peak 识别](peak-calling-step.md) - 使用 peak caller 从 BAM 文件中识别染色质开放区域。...

## 元信息

- **来源文件**: `content/concepts/fdr.yaml`
- **最后更新**: 2026-04-07 19:43

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
