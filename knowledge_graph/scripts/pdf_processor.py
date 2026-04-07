#!/usr/bin/env python3
"""
PDF Processor - 将论文转换为知识图谱实体
基于 PyMuPDF + OpenAI API
"""

import os
import sys
import json
import re
import base64
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import fitz  # PyMuPDF
import requests


@dataclass
class PDFEntity:
    """从 PDF 提取的知识实体"""
    id: str
    name: str
    type: str  # tools, steps, concepts, resources
    description: str
    detailed_explanation: str
    tags: List[str]
    source_pdf: str
    page_range: str
    created_at: str


class PDFProcessor:
    """PDF 处理器 - 提取内容并生成知识实体"""
    
    def __init__(self, api_base: str = "https://api.openai-proxy.org", 
                 api_key: str = None,
                 model: str = "gpt-4.1-mini"):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量或在初始化时提供 api_key")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, str]:
        """从 PDF 提取每页文本"""
        doc = fitz.open(pdf_path)
        pages = {}
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text().strip()
            if text:
                pages[page_num + 1] = text
        
        doc.close()
        return pages
    
    def render_page_to_image(self, pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
        """将 PDF 页面渲染为图片"""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num - 1)  # 0-based
        
        # 使用矩阵提高分辨率
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    
    def _call_openai(self, messages: List[Dict], temperature: float = 0.3) -> str:
        """调用 OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        response = requests.post(
            f"{self.api_base}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def analyze_paper_structure(self, text: str) -> Dict[str, Any]:
        """分析论文结构，提取关键信息"""
        system_prompt = """你是一个专业的学术论文分析助手。请分析输入的论文内容，提取以下结构化信息：

请返回 JSON 格式：
{
    "title": "论文标题",
    "abstract": "摘要",
    "keywords": ["关键词1", "关键词2"],
    "sections": [
        {
            "heading": "章节标题",
            "content": "章节内容摘要",
            "type": "introduction|methods|results|discussion|conclusion|other"
        }
    ],
    "tools": ["使用的工具/软件1", "工具2"],
    "methods": ["研究方法1", "方法2"],
    "datasets": ["数据集1", "数据集2"]
}

注意：
1. 只返回 JSON，不要有任何其他文字
2. 如果某部分信息缺失，使用空字符串或空数组
3. content 字段应简明扼要，不超过 200 字"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下论文内容：\n\n{text[:15000]}"}  # 限制长度
        ]
        
        response = self._call_openai(messages)
        
        # 提取 JSON
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试从代码块中提取
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # 尝试从文本中提取 JSON 部分
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"无法解析 API 响应: {response[:500]}")
    
    def extract_knowledge_entities(self, structure: Dict[str, Any], 
                                    pdf_filename: str) -> List[PDFEntity]:
        """从论文结构提取知识实体"""
        entities = []
        timestamp = datetime.now().isoformat()
        base_id = Path(pdf_filename).stem.lower().replace(' ', '-')
        
        # 1. 创建论文资源实体
        entities.append(PDFEntity(
            id=f"{base_id}-paper",
            name=structure.get("title", "Unknown Paper"),
            type="resources",
            description=structure.get("abstract", "")[:200],
            detailed_explanation=f"# {structure.get('title', 'Unknown')}\n\n## 摘要\n{structure.get('abstract', 'N/A')}\n\n## 关键词\n{', '.join(structure.get('keywords', []))}",
            tags=structure.get("keywords", []) + ["论文", "文献"],
            source_pdf=pdf_filename,
            page_range="all",
            created_at=timestamp
        ))
        
        # 2. 创建方法实体
        for i, method in enumerate(structure.get("methods", [])):
            if len(method) > 5:  # 过滤太短的
                entities.append(PDFEntity(
                    id=f"{base_id}-method-{i}",
                    name=method[:50],
                    type="steps",
                    description=f"论文中使用的方法: {method}",
                    detailed_explanation=f"## 方法\n{method}\n\n来源: {structure.get('title', 'Unknown Paper')}",
                    tags=["方法", "protocol"] + structure.get("keywords", [])[:3],
                    source_pdf=pdf_filename,
                    page_range="methods",
                    created_at=timestamp
                ))
        
        # 3. 创建工具实体
        for i, tool in enumerate(structure.get("tools", [])):
            if len(tool) > 2:
                entities.append(PDFEntity(
                    id=f"{base_id}-tool-{i}",
                    name=tool[:50],
                    type="tools",
                    description=f"论文中使用的工具/软件",
                    detailed_explanation=f"## 工具: {tool}\n\n在论文 '{structure.get('title', 'Unknown')}' 中使用",
                    tags=["软件", "工具"] + structure.get("keywords", [])[:2],
                    source_pdf=pdf_filename,
                    page_range="methods",
                    created_at=timestamp
                ))
        
        # 4. 从章节创建概念实体
        for section in structure.get("sections", []):
            if section.get("type") in ["introduction", "discussion", "conclusion"]:
                content = section.get("content", "")
                if len(content) > 50:
                    entities.append(PDFEntity(
                        id=f"{base_id}-concept-{len(entities)}",
                        name=section.get("heading", "概念")[:50],
                        type="concepts",
                        description=content[:150],
                        detailed_explanation=f"## {section.get('heading', '概念')}\n\n{content}",
                        tags=["概念", "知识"] + structure.get("keywords", [])[:2],
                        source_pdf=pdf_filename,
                        page_range=section.get("heading", "unknown"),
                        created_at=timestamp
                    ))
        
        return entities
    
    def analyze_figure(self, image_data: bytes, caption: str = "") -> Dict[str, Any]:
        """使用 Vision API 分析图片"""
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        system_prompt = """你是一个科学图表分析专家。请分析这张论文图片，提取以下信息：

返回 JSON 格式：
{
    "figure_type": "图表类型 (flowchart/heatmap/scatter/bar/line/microscopy/gel/etc)",
    "description": "图片内容的详细描述",
    "key_points": ["关键点1", "关键点2"],
    "methods_shown": ["展示的方法1"],
    "data_summary": "数据摘要"
}

只返回 JSON，不要有其他文字。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"请分析这张图片{f'，图注: {caption}' if caption else ''}:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        response = self._call_openai(messages, temperature=0.2)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"description": response, "figure_type": "unknown"}
    
    def process_pdf(self, pdf_path: str, extract_figures: bool = False) -> Dict[str, Any]:
        """处理 PDF 文件，返回知识实体"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        print(f"📄 正在处理: {pdf_path.name}")
        
        # 1. 提取文本
        print("  → 提取文本...")
        pages = self.extract_text_from_pdf(str(pdf_path))
        full_text = "\n\n".join(pages.values())
        
        # 2. 分析结构
        print("  → AI 分析论文结构...")
        structure = self.analyze_paper_structure(full_text)
        structure["total_pages"] = len(pages)
        
        # 3. 提取实体
        print("  → 生成知识实体...")
        entities = self.extract_knowledge_entities(structure, pdf_path.name)
        
        # 4. 可选：分析图片
        figures = []
        if extract_figures:
            print("  → 分析图表...")
            doc = fitz.open(str(pdf_path))
            for page_num in range(min(3, len(doc))):  # 只分析前3页
                img_data = self.render_page_to_image(str(pdf_path), page_num + 1)
                figure_info = self.analyze_figure(img_data)
                figures.append({
                    "page": page_num + 1,
                    **figure_info
                })
            doc.close()
        
        return {
            "filename": pdf_path.name,
            "structure": structure,
            "entities": [asdict(e) for e in entities],
            "figures": figures,
            "entity_count": len(entities)
        }
    
    def save_entities_to_yaml(self, result: Dict[str, Any], output_dir: str = "content"):
        """将实体保存为 YAML 文件"""
        import yaml
        
        output_dir = Path(output_dir)
        
        for entity in result["entities"]:
            type_dir = output_dir / entity["type"]
            type_dir.mkdir(parents=True, exist_ok=True)
            
            yaml_path = type_dir / f"{entity['id']}.yaml"
            
            yaml_data = {
                "id": entity["id"],
                "name": entity["name"],
                "type": entity["type"],
                "description": entity["description"],
                "detailed_explanation": entity["detailed_explanation"],
                "tags": entity["tags"],
                "metadata": {
                    "source_pdf": entity["source_pdf"],
                    "page_range": entity["page_range"],
                    "created_at": entity["created_at"],
                    "auto_extracted": True
                }
            }
            
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)
            
            print(f"  ✓ 已保存: {yaml_path}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF 论文处理器")
    parser.add_argument("pdf", help="PDF 文件路径")
    parser.add_argument("--api-base", default="https://api.openai-proxy.org", help="API 基础地址")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="API Key")
    parser.add_argument("--model", default="gpt-4.1-mini", help="模型名称")
    parser.add_argument("--output", default="content", help="输出目录")
    parser.add_argument("--figures", action="store_true", help="是否分析图片")
    
    args = parser.parse_args()
    
    processor = PDFProcessor(
        api_base=args.api_base,
        api_key=args.api_key,
        model=args.model
    )
    
    result = processor.process_pdf(args.pdf, extract_figures=args.figures)
    processor.save_entities_to_yaml(result, args.output)
    
    print(f"\n✅ 完成！共生成 {result['entity_count']} 个知识实体")


if __name__ == "__main__":
    main()
