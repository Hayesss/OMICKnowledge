"""
title: 多组学知识图谱检索
description: 从多组学知识图谱中检索实验方法、分析工具、关键概念等相关知识。支持语义搜索，基于向量相似度返回最相关的知识条目。可通过界面配置 API 地址。
author: Knowledge Graph Team
version: 1.1.0
license: MIT
requirements: requests
"""

import requests
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Tools:
    """
    知识图谱记忆库检索工具（支持界面配置）
    """
    
    # Valves 配置类 - Open WebUI 会自动在界面中显示这些配置项
    class Valves(BaseModel):
        api_base_url: str = Field(
            default="http://host.docker.internal:8000",
            description="知识图谱 API 地址。如果在 Docker 中运行 Open WebUI，使用 host.docker.internal:8000；如果是独立运行，使用 localhost:8000"
        )
        request_timeout: int = Field(
            default=10,
            description="API 请求超时时间（秒）"
        )
        default_top_k: int = Field(
            default=5,
            description="默认返回的结果数量"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def _get_api_base(self) -> str:
        """获取 API 基础地址。"""
        return self.valves.api_base_url.rstrip('/')
    
    def query_knowledge(
        self,
        query: str,
        entity_type: Optional[Literal[
            "assay", "tool", "step", "concept", "issue", "stage", "resource"
        ]] = None,
        top_k: Optional[int] = None
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
        :param top_k: 可选，返回的最大结果数量（默认使用配置值）
        :return: 格式化的知识检索结果
        """
        try:
            api_base = self._get_api_base()
            timeout = self.valves.request_timeout
            k = top_k or self.valves.default_top_k
            
            # 构建请求参数
            params = {"q": query, "k": str(k)}
            if entity_type:
                params["type"] = entity_type
            
            # 调用记忆库 API
            response = requests.get(
                f"{api_base}/search",
                params=params,
                timeout=timeout
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
                item_type = item.get("entity_type", "未知类型")
                score = item.get("score", 0)
                text = item.get("text", "")
                tags = item.get("tags", [])
                difficulty = item.get("difficulty", "")
                
                # 构建类型显示
                type_emoji = {
                    "assay": "🧪",
                    "tool": "🔧",
                    "step": "📋",
                    "concept": "💡",
                    "issue": "⚠️",
                    "stage": "📊",
                    "resource": "📚"
                }.get(item_type, "📄")
                
                formatted_results.append(f"{i}. {type_emoji} {name} (相关度: {score:.1%})")
                formatted_results.append(f"   类型: {item_type}")
                
                if difficulty:
                    level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
                    formatted_results.append(f"   难度: {level_emoji.get(difficulty, '⚪')} {difficulty}")
                
                if tags:
                    formatted_results.append(f"   标签: {', '.join(tags)}")
                
                # 提取描述
                description = ""
                for line in text.split('\n'):
                    if line.startswith("Description:"):
                        description = line.replace("Description:", "").strip()
                        break
                    elif line.startswith("Name:"):
                        continue
                    elif line and not description:
                        description = line[:250]
                        break
                
                if description:
                    formatted_results.append(f"   描述: {description}")
                
                formatted_results.append("")
            
            formatted_results.append("💡 提示: 您可以询问更具体的问题来获取更精确的答案。")
            
            return "\n".join(formatted_results)
            
        except requests.exceptions.ConnectionError:
            return (
                f"❌ 无法连接到知识图谱服务 ({self._get_api_base()})。\n\n"
                "请检查:\n"
                "1. 知识图谱 API 是否已启动 (pixi run serve-memory)\n"
                "2. API 地址配置是否正确（在工具设置中修改）\n"
                "3. 网络连接是否正常"
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
            api_base = self._get_api_base()
            timeout = self.valves.request_timeout
            
            response = requests.get(
                f"{api_base}/entity",
                params={"id": entity_id},
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            name = data.get("name", "未知")
            entity_type = data.get("entity_type", "未知类型")
            text = data.get("text", "")
            tags = data.get("tags", [])
            difficulty = data.get("difficulty", "")
            
            type_emoji = {
                "assay": "🧪",
                "tool": "🔧",
                "step": "📋",
                "concept": "💡",
                "issue": "⚠️",
                "stage": "📊",
                "resource": "📚"
            }.get(entity_type, "📄")
            
            formatted = []
            formatted.append(f"{'='*50}")
            formatted.append(f"📖 {type_emoji} {name}")
            formatted.append(f"{'='*50}")
            formatted.append(f"类型: {entity_type}")
            
            if difficulty:
                formatted.append(f"难度: {difficulty}")
            
            if tags:
                formatted.append(f"标签: {', '.join(tags)}")
            
            formatted.append(f"\n{text}")
            formatted.append(f"{'='*50}")
            
            return "\n".join(formatted)
            
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接到知识图谱服务。请确保服务已启动。"
        except Exception as e:
            return f"❌ 获取详情出错: {str(e)}"
    
    def find_related(self, entity_id: str, top_k: Optional[int] = None) -> str:
        """
        查找与指定实体相关的其他知识。
        
        当用户想了解与某个概念相关的其他知识时使用。
        
        :param entity_id: 实体的唯一标识符（如 bowtie2）
        :param top_k: 返回的相关实体数量（默认使用配置值）
        :return: 相关实体列表
        """
        try:
            api_base = self._get_api_base()
            timeout = self.valves.request_timeout
            k = top_k or self.valves.default_top_k
            
            response = requests.get(
                f"{api_base}/related",
                params={"id": entity_id, "k": k},
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            related = data.get("related", [])
            
            if not related:
                return f"未找到与 「{entity_id}」 相关的其他知识。"
            
            formatted = []
            formatted.append(f"🔗 与 「{entity_id}」 相关的内容:\n")
            
            type_emoji = {
                "assay": "🧪",
                "tool": "🔧",
                "step": "📋",
                "concept": "💡",
                "issue": "⚠️",
                "stage": "📊",
                "resource": "📚"
            }
            
            for item in related:
                name = item.get("name", "未知")
                entity_type = item.get("entity_type", "")
                score = item.get("score", 0)
                
                emoji = type_emoji.get(entity_type, "📄")
                formatted.append(f"• {emoji} {name} ({entity_type}) - 相似度: {score:.1%}")
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"❌ 查找相关内容出错: {str(e)}"
