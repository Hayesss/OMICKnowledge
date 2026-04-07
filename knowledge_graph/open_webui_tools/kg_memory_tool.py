"""
title: 多组学知识图谱检索
description: 从多组学知识图谱中检索实验方法、分析工具、关键概念等相关知识。支持语义搜索，基于向量相似度返回最相关的知识条目。
author: Knowledge Graph Team
version: 1.0.0
license: MIT
requirements: requests
"""

import requests
import json
from typing import Optional


class Tools:
    """
    知识图谱记忆库检索工具
    
    使用此工具从多组学知识图谱中检索相关知识，包括：
    - 实验类型 (CUT&Tag, ATAC-seq, scRNA-seq, Hi-C 等)
    - 分析工具 (Bowtie2, MACS2, Seurat, Cell Ranger 等)
    - 分析步骤 (质控、比对、peak calling、聚类等)
    - 关键概念 (FDR, fragment size, UMAP 等)
    - 常见问题及解决方案
    """
    
    def __init__(self):
        """初始化工具，从环境变量或默认值获取配置。"""
        # Open WebUI 通过 valves 传递配置，但这里设置默认值
        self.api_base = "http://host.docker.internal:8000"
        self.timeout = 10
    
    def query_knowledge(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        从多组学知识图谱中检索相关知识。
        
        当用户询问以下类型的问题时，应调用此工具：
        - 实验方法（如"CUT&Tag 是什么"、"ATAC-seq 流程"）
        - 分析工具（如"Bowtie2 怎么用"、"用什么做 peak calling"）
        - 分析步骤（如"质控步骤有哪些"、"如何过滤低质量细胞"）
        - 概念解释（如"FDR 是什么意思"、"什么是 fragment size"）
        - 问题排查（如"比对率低怎么办"、"为什么聚类效果不好"）
        
        :param query: 用户的查询问题（自然语言）
        :param entity_type: 可选，限定返回的实体类型 
                           (assay, tool, step, concept, issue, stage, resource)
        :param top_k: 返回的最大结果数量（默认 5）
        :return: 格式化的知识检索结果
        """
        try:
            # 构建请求参数
            params = {
                "q": query,
                "k": str(top_k)
            }
            if entity_type:
                params["type"] = entity_type
            
            # 调用记忆库 API
            response = requests.get(
                f"{self.api_base}/search",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return f"未找到与「{query}」相关的知识。请尝试使用不同的关键词。"
            
            # 格式化返回结果
            formatted_results = []
            formatted_results.append(f"🔍 检索查询: 「{query}」")
            formatted_results.append(f"📊 找到 {len(results)} 条相关知识\n")
            
            for i, item in enumerate(results, 1):
                name = item.get("name", "未知")
                entity_type_display = item.get("entity_type", "未知类型")
                score = item.get("score", 0)
                text = item.get("text", "")
                tags = item.get("tags", [])
                
                # 构建类型显示
                type_emoji = {
                    "assay": "🧪",
                    "tool": "🔧",
                    "step": "📋",
                    "concept": "💡",
                    "issue": "⚠️",
                    "stage": "📊",
                    "resource": "📚"
                }.get(entity_type_display, "📄")
                
                formatted_results.append(f"{i}. {type_emoji} {name} (相关度: {score:.1%})")
                formatted_results.append(f"   类型: {entity_type_display}")
                
                if tags:
                    formatted_results.append(f"   标签: {', '.join(tags)}")
                
                # 提取关键信息（取前几行）
                text_lines = text.split('\n')
                description = ""
                for line in text_lines:
                    if line.startswith("Description:"):
                        description = line.replace("Description:", "").strip()
                        break
                
                if not description and text_lines:
                    description = text_lines[0][:200]
                
                if description:
                    formatted_results.append(f"   描述: {description}")
                
                formatted_results.append("")  # 空行分隔
            
            formatted_results.append("💡 提示: 您可以询问更具体的问题来获取更精确的答案。")
            
            return "\n".join(formatted_results)
            
        except requests.exceptions.ConnectionError:
            return (
                "❌ 无法连接到知识图谱服务。\n"
                "请确保:\n"
                "1. 知识图谱 API 服务已启动 (pixi run serve-memory)\n"
                "2. Docker 容器可以访问 host.docker.internal:8000\n"
                "3. 如果是 Linux，可能需要添加 --add-host=host.docker.internal:host-gateway"
            )
        except requests.exceptions.Timeout:
            return "⏱️ 请求超时，请稍后重试。"
        except Exception as e:
            return f"❌ 检索出错: {str(e)}"
    
    def get_entity_detail(self, entity_id: str) -> str:
        """
        获取特定实体的详细信息。
        
        当用户想了解某个特定工具、方法或概念的详细信息时使用。
        
        :param entity_id: 实体的唯一标识符（如 bowtie2, cut-tag, quality-control）
        :return: 实体的完整信息
        """
        try:
            response = requests.get(
                f"{self.api_base}/entity",
                params={"id": entity_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            name = data.get("name", "未知")
            entity_type = data.get("entity_type", "未知类型")
            text = data.get("text", "")
            tags = data.get("tags", [])
            difficulty = data.get("difficulty", "")
            
            formatted = []
            formatted.append(f"📖 {name}")
            formatted.append(f"类型: {entity_type}")
            
            if difficulty:
                formatted.append(f"难度: {difficulty}")
            
            if tags:
                formatted.append(f"标签: {', '.join(tags)}")
            
            formatted.append(f"\n{text}")
            
            return "\n".join(formatted)
            
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接到知识图谱服务。请确保服务已启动。"
        except Exception as e:
            return f"❌ 获取详情出错: {str(e)}"
    
    def find_related(self, entity_id: str, top_k: int = 5) -> str:
        """
        查找与指定实体相关的其他知识。
        
        :param entity_id: 实体的唯一标识符
        :param top_k: 返回的相关实体数量
        :return: 相关实体列表
        """
        try:
            response = requests.get(
                f"{self.api_base}/related",
                params={"id": entity_id, "k": top_k},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            related = data.get("related", [])
            
            if not related:
                return f"未找到与 「{entity_id}」 相关的其他知识。"
            
            formatted = []
            formatted.append(f"🔗 与 「{entity_id}」 相关的内容:\n")
            
            for item in related:
                name = item.get("name", "未知")
                entity_type = item.get("entity_type", "")
                score = item.get("score", 0)
                
                formatted.append(f"• {name} ({entity_type}) - 相似度: {score:.1%}")
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"❌ 查找相关内容出错: {str(e)}"


# 兼容性别名，用于旧版本 Open WebUI
ToolsClass = Tools
