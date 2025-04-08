#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Notion API 관련 라이브러리
from notion_client import Client
from notion2md.exporter.block import MarkdownExporter, StringExporter

# FastMCP 라이브러리
from mcp.server.fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_mcp.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notion_fastmcp")

# FastMCP 초기화
mcp = FastMCP("notion_mcp")

class NotionHelper:
    """Notion API 관련 도우미 함수들을 제공하는 클래스"""
    
    def __init__(self):
        """Notion 헬퍼 초기화"""
        # Notion API 토큰 설정
        self.api_token = os.environ.get("NOTION_API_TOKEN")
        if not self.api_token:
            logger.error("NOTION_API_TOKEN 환경 변수가 설정되지 않았습니다.")
            sys.exit(1)
        
        # Notion 클라이언트 초기화
        try:
            self.client = Client(auth=self.api_token)
            logger.info("Notion 클라이언트가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logger.error(f"Notion 클라이언트 초기화 실패: {e}")
            sys.exit(1)
            
        # 페이지 정보 캐시
        self.page_cache = {}
        
        # 업로드 전 내용 캐시
        self.upload_cache = {}

    def _format_notion_url(self, page_id: str) -> str:
        """Notion 페이지 ID를 URL 형식으로 변환합니다."""
        # 하이픈 제거 및 표준 포맷 변환
        clean_id = page_id.replace("-", "")
        return f"https://notion.so/{clean_id}"

    def _extract_page_id(self, url_or_id: str) -> str:
        """URL 또는 ID에서 Notion 페이지 ID를 추출합니다."""
        # URL일 경우 ID 부분 추출
        if url_or_id.startswith("http"):
            # notion.so/ 또는 www.notion.so/ 이후 부분 추출
            if "notion.so/" in url_or_id:
                parts = url_or_id.split("notion.so/")
                if len(parts) > 1:
                    path = parts[1].split("?")[0].split("#")[0]  # 쿼리 파라미터 및 프래그먼트 제거
                    # 페이지 이름이 있는 경우 처리
                    if "-" in path:
                        path_parts = path.split("-")
                        if len(path_parts) > 1:
                            return path_parts[-1]
                    return path
        
        # 이미 ID인 경우
        return url_or_id.replace("-", "")
        
    def get_page_structure(self, page_id):
        """페이지 구조를 가져옵니다."""
        try:
            children = self.client.blocks.children.list(block_id=page_id)
            pages = []
            
            for block in children.get('results', []):
                if block['type'] == 'child_page':
                    page_info = {
                        'id': block['id'],
                        'title': block['child_page']['title'],
                        'has_children': False
                    }
                    
                    # 하위 페이지 확인
                    sub_pages = self.client.blocks.children.list(block_id=block['id'])
                    if sub_pages['results']:
                        page_info['has_children'] = True
                    
                    pages.append(page_info)
                    self.page_cache[block['id']] = page_info
                    
            return pages
            
        except Exception as e:
            logger.error(f"페이지 구조 조회 중 오류 발생: {str(e)}")
            return []
            
    def verify_upload(self, page_id, original_blocks):
        """업로드된 내용을 검증합니다."""
        try:
            current_blocks = self.client.blocks.children.list(block_id=page_id).get("results", [])
            
            if len(original_blocks) != len(current_blocks):
                logger.warning(f"⚠️ 블록 수가 다릅니다: 원본 {len(original_blocks)}개, 현재 {len(current_blocks)}개")
                
            # 내용 비교
            for i, orig_block in enumerate(original_blocks):
                if i < len(current_blocks):
                    curr_block = current_blocks[i]
                    
                    # 블록 타입 확인
                    if orig_block["type"] != curr_block["type"]:
                        logger.warning(f"⚠️ 블록 {i+1}의 타입이 다릅니다: 원본 {orig_block['type']}, 현재 {curr_block['type']}")
                        continue
                    
                    # 텍스트 콘텐츠 비교
                    if orig_block["type"] in ["paragraph", "heading_1", "heading_2", "heading_3", 
                                             "bulleted_list_item", "numbered_list_item", "to_do", "code"]:
                        orig_text = self._get_text_from_block(orig_block)
                        curr_text = self._get_text_from_block(curr_block)
                        
                        if orig_text.strip() != curr_text.strip():
                            logger.warning(f"⚠️ 블록 {i+1}의 내용이 다릅니다:")
                            logger.warning(f"  원본: {orig_text[:100]}...")
                            logger.warning(f"  현재: {curr_text[:100]}...")
                else:
                    logger.warning(f"❌ 블록 {i+1}이 현재 버전에서 누락되었습니다.")
            
            # 추가 블록 확인
            if len(current_blocks) > len(original_blocks):
                for i in range(len(original_blocks), len(current_blocks)):
                    logger.warning(f"❌ 블록 {i+1}이 원본에 없는 추가 블록입니다.")
                    curr_text = self._get_text_from_block(current_blocks[i])
                    logger.warning(f"  내용: {curr_text[:100]}...")
                    
            return len(original_blocks) == len(current_blocks)
                
        except Exception as e:
            logger.error(f"업로드 검증 중 오류 발생: {str(e)}")
            return False
            
    def _get_text_from_block(self, block):
        """블록에서 텍스트 내용을 추출합니다."""
        block_type = block["type"]
        
        if block_type == "paragraph":
            return ''.join([t.get('plain_text', '') for t in block['paragraph']['rich_text']])
        elif block_type.startswith("heading_"):
            return ''.join([t.get('plain_text', '') for t in block[block_type]['rich_text']])
        elif block_type == "bulleted_list_item":
            return ''.join([t.get('plain_text', '') for t in block['bulleted_list_item']['rich_text']])
        elif block_type == "numbered_list_item":
            return ''.join([t.get('plain_text', '') for t in block['numbered_list_item']['rich_text']])
        elif block_type == "to_do":
            return ''.join([t.get('plain_text', '') for t in block['to_do']['rich_text']])
        elif block_type == "code":
            return ''.join([t.get('plain_text', '') for t in block['code']['rich_text']])
        else:
            return ""
            
    def store_original_content(self, page_id, content):
        """업로드 전 내용을 캐시에 저장합니다."""
        self.upload_cache[page_id] = content
            
    def markdown_to_blocks(self, md_content):
        """마크다운 내용을 노션 블록으로 변환합니다."""
        blocks = []
        current_block = {"type": "paragraph", "content": ""}
        lines = md_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            # 이미지 처리
            image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if image_match:
                caption, url = image_match.groups()
                blocks.append({
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": url
                        },
                        "caption": [
                            {
                                "type": "text",
                                "text": {
                                    "content": caption
                                }
                            }
                        ] if caption else []
                    }
                })
                continue
            
            # 빈 줄 처리
            if not line:
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                    current_block = {"type": "paragraph", "content": ""}
                continue
            
            # 제목 처리
            if line.startswith('# '):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                blocks.append({"type": "heading_1", "content": line[2:].strip()})
                current_block = {"type": "paragraph", "content": ""}
            elif line.startswith('## '):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                blocks.append({"type": "heading_2", "content": line[3:].strip()})
                current_block = {"type": "paragraph", "content": ""}
            elif line.startswith('### '):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                blocks.append({"type": "heading_3", "content": line[4:].strip()})
                current_block = {"type": "paragraph", "content": ""}
            
            # 글머리 기호 목록 처리
            elif line.startswith('* ') or (line.startswith('- ') and not line.startswith('- [')):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                blocks.append({"type": "bulleted_list_item", "content": line[2:].strip()})
                current_block = {"type": "paragraph", "content": ""}
            
            # 체크리스트 처리
            elif line.startswith('- ['):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                checked = line[3] == 'x'
                content = line[5:].strip()
                blocks.append({"type": "to_do", "content": content, "checked": checked})
                current_block = {"type": "paragraph", "content": ""}
            
            # 번호 매기기 목록 처리
            elif line[0].isdigit() and '.' in line[:3]:
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                content = line[line.find('.')+2:].strip()
                blocks.append({"type": "numbered_list_item", "content": content})
                current_block = {"type": "paragraph", "content": ""}
            
            # 코드 블록 처리
            elif line.startswith('```'):
                if current_block and current_block["content"]:
                    blocks.append(current_block)
                    current_block = {"type": "paragraph", "content": ""}
                
                # 언어 식별
                language = line[3:].strip()
                code_content = []
                
                # 코드 블록 끝까지 읽기
                while i < len(lines) and not lines[i].strip() == '```':
                    code_content.append(lines[i])
                    i += 1
                
                # 코드 끝 줄 건너뛰기
                if i < len(lines):
                    i += 1
                
                blocks.append({
                    "type": "code",
                    "content": '\n'.join(code_content),
                    "language": language if language else "plain text"
                })
            
            # 일반 문단 처리
            else:
                if not current_block:
                    current_block = {"type": "paragraph", "content": ""}
                if current_block["content"]:
                    current_block["content"] += "\n"
                current_block["content"] += line
        
        # 마지막 블록 추가
        if current_block and current_block["content"]:
            blocks.append(current_block)
        
        # 변환된 블록을 Notion API 형식으로 변환
        notion_blocks = []
        for block in blocks:
            if block["type"] == "paragraph":
                notion_blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }]
                    }
                })
            elif block["type"].startswith("heading_"):
                notion_blocks.append({
                    "type": block["type"],
                    block["type"]: {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }]
                    }
                })
            elif block["type"] == "bulleted_list_item":
                notion_blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }]
                    }
                })
            elif block["type"] == "numbered_list_item":
                notion_blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }]
                    }
                })
            elif block["type"] == "to_do":
                notion_blocks.append({
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }],
                        "checked": block.get("checked", False)
                    }
                })
            elif block["type"] == "code":
                notion_blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": block["content"]}
                        }],
                        "language": block.get("language", "plain text")
                    }
                })
            elif block["type"] == "image":
                notion_blocks.append(block)  # 이미지 블록은 이미 Notion API 형식
        
        return notion_blocks

# 전역 Notion 헬퍼 인스턴스
notion_helper = NotionHelper()

# MCP 도구 구현
@mcp.tool()
async def notion_create_page(parent_id: str, title: str, content: Optional[str] = None) -> str:
    """Notion에 새 페이지를 생성합니다.
    
    Args:
        parent_id: 상위 페이지 또는 데이터베이스 ID
        title: 페이지 제목
        content: 페이지 내용 (마크다운 형식, 선택 사항)
            
    Returns:
        생성된 페이지 정보를 담은 JSON 문자열
    """
    try:
        # 상위 컨테이너가 데이터베이스인지 페이지인지 확인
        parent_id = notion_helper._extract_page_id(parent_id)
        
        try:
            # 데이터베이스로 시도
            notion_helper.client.databases.retrieve(parent_id)
            parent = {"database_id": parent_id}
            
            # 데이터베이스에 페이지 생성 시 속성 구성
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        except Exception:
            # 페이지로 시도
            parent = {"page_id": parent_id}
            
            # 페이지에 하위 페이지 생성 시 속성 구성
            properties = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        
        # 페이지 생성 요청
        new_page = notion_helper.client.pages.create(
            parent=parent,
            properties=properties
        )
        
        # 내용이 있는 경우 내용 추가
        if content:
            result = await notion_save_content_to_page(new_page["id"], content)
        
        logger.info(f"새 페이지가 생성되었습니다: {title}")
        
        # 응답 구성
        return json.dumps({
            "page_id": new_page["id"],
            "url": notion_helper._format_notion_url(new_page["id"]),
            "title": title,
            "created_time": new_page["created_time"]
        })
        
    except Exception as e:
        logger.error(f"페이지 생성 중 오류 발생: {str(e)}")
        return json.dumps({"error": f"페이지 생성 실패: {str(e)}"})

@mcp.tool()
async def notion_save_content_to_page(page_id: str, content: str) -> str:
    """마크다운 형식으로 Notion 페이지에 내용을 저장합니다.
    
    Args:
        page_id: Notion 페이지 ID 또는 URL
        content: 저장할 마크다운 콘텐츠
            
    Returns:
        업데이트된 페이지 정보를 담은 JSON 문자열
    """
    try:
        page_id = notion_helper._extract_page_id(page_id)
        
        # 현재 페이지 정보 조회
        page = notion_helper.client.pages.retrieve(page_id)
        
        # 업로드 전 내용 캐싱 (검증용)
        notion_helper.store_original_content(page_id, content)
        
        # 마크다운에서 Notion 블록으로 변환
        blocks = notion_helper.markdown_to_blocks(content)
        
        # 기존 블록 삭제 (선택적)
        if True:  # 이 부분을 파라미터화할 수 있음
            existing_blocks = notion_helper.client.blocks.children.list(page_id)
            for block in existing_blocks.get('results', []):
                notion_helper.client.blocks.delete(block_id=block['id'])
            logger.info(f"✅ 기존 내용 삭제 완료")
        
        # 새 블록 추가
        response = notion_helper.client.blocks.children.append(page_id, children=blocks)
        
        # 업로드 검증
        verify_result = notion_helper.verify_upload(page_id, blocks)
        
        logger.info(f"✅ 페이지 {page_id}에 콘텐츠가 업데이트되었습니다. 검증 결과: {verify_result}")
        
        # 응답 구성
        title = ""
        for prop_name, prop_value in page.get("properties", {}).items():
            if prop_value["type"] == "title":
                title_array = prop_value.get("title", [])
                if title_array:
                    title = title_array[0].get("plain_text", "")
        
        return json.dumps({
            "page_id": page_id,
            "url": notion_helper._format_notion_url(page_id),
            "title": title,
            "updated_time": datetime.now().isoformat(),
            "verification": verify_result
        })
        
    except Exception as e:
        logger.error(f"페이지 콘텐츠 저장 중 오류 발생: {str(e)}, 타입: {type(e).__name__}")
        # API 응답 상세 정보 확인
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            logger.error(f"API 응답: {e.response.text}")
        return json.dumps({"error": f"페이지 콘텐츠 저장 실패: {str(e)}"})

@mcp.tool()
async def notion_query_database(database_id: str, filter_obj: Optional[str] = None, 
                               sorts: Optional[str] = None, 
                               page_size: int = 100) -> str:
    """Notion 데이터베이스를 쿼리합니다.
    
    Args:
        database_id: 데이터베이스 ID 또는 URL
        filter_obj: 필터 객체를 담은 JSON 문자열 (선택 사항)
        sorts: 정렬 기준을 담은 JSON 문자열 (선택 사항)
        page_size: 결과 페이지 크기 (선택 사항)
            
    Returns:
        쿼리 결과를 담은 JSON 문자열
    """
    try:
        database_id = notion_helper._extract_page_id(database_id)
        
        # 쿼리 파라미터 구성
        query_params = {
            "page_size": page_size
        }
        
        if filter_obj:
            query_params["filter"] = json.loads(filter_obj)
            
        if sorts:
            query_params["sorts"] = json.loads(sorts)
        
        # 데이터베이스 쿼리 요청
        results = notion_helper.client.databases.query(database_id, **query_params)
        
        # 결과 가공
        processed_results = []
        for page in results.get("results", []):
            processed_page = {
                "id": page["id"],
                "url": notion_helper._format_notion_url(page["id"]),
                "created_time": page["created_time"],
                "last_edited_time": page["last_edited_time"],
                "properties": {}
            }
            
            # 속성 가공
            for prop_name, prop_value in page.get("properties", {}).items():
                if prop_value["type"] == "title":
                    title_array = prop_value.get("title", [])
                    title = " ".join([t.get("plain_text", "") for t in title_array])
                    processed_page["properties"][prop_name] = title
                elif prop_value["type"] == "rich_text":
                    text_array = prop_value.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in text_array])
                    processed_page["properties"][prop_name] = text
                elif prop_value["type"] == "number":
                    processed_page["properties"][prop_name] = prop_value.get("number")
                elif prop_value["type"] == "select":
                    select_value = prop_value.get("select")
                    if select_value:
                        processed_page["properties"][prop_name] = select_value.get("name", "")
                elif prop_value["type"] == "multi_select":
                    multi_select = prop_value.get("multi_select", [])
                    processed_page["properties"][prop_name] = [item.get("name", "") for item in multi_select]
                elif prop_value["type"] == "date":
                    date_value = prop_value.get("date")
                    if date_value:
                        processed_page["properties"][prop_name] = date_value.get("start")
                elif prop_value["type"] == "checkbox":
                    processed_page["properties"][prop_name] = prop_value.get("checkbox", False)
                else:
                    # 기타 타입은 원본 그대로 저장
                    processed_page["properties"][prop_name] = prop_value
            
            processed_results.append(processed_page)
        
        logger.info(f"데이터베이스 {database_id} 쿼리 완료, {len(processed_results)}개 결과 반환")
        
        # 응답 구성
        return json.dumps({
            "database_id": database_id,
            "results": processed_results,
            "has_more": results.get("has_more", False),
            "next_cursor": results.get("next_cursor"),
            "total_results": len(processed_results)
        })
        
    except Exception as e:
        logger.error(f"데이터베이스 쿼리 중 오류 발생: {str(e)}")
        return json.dumps({"error": f"데이터베이스 쿼리 실패: {str(e)}"})

@mcp.tool()
async def notion_get_page(page_id: str) -> str:
    """Notion 페이지 정보를 조회합니다.
    
    Args:
        page_id: 페이지 ID 또는 URL
            
    Returns:
        페이지 정보를 담은 JSON 문자열
    """
    try:
        page_id = notion_helper._extract_page_id(page_id)
        
        # 페이지 정보 조회
        page = notion_helper.client.pages.retrieve(page_id)
        
        # 결과 가공
        processed_page = {
            "id": page["id"],
            "url": notion_helper._format_notion_url(page["id"]),
            "created_time": page["created_time"],
            "last_edited_time": page["last_edited_time"],
            "properties": {}
        }
        
        # 속성 가공
        for prop_name, prop_value in page.get("properties", {}).items():
            if prop_value["type"] == "title":
                title_array = prop_value.get("title", [])
                title = " ".join([t.get("plain_text", "") for t in title_array])
                processed_page["properties"][prop_name] = title
                # 제목을 별도 필드로도 저장
                if prop_name == "title" or prop_name == "Name":
                    processed_page["title"] = title
            elif prop_value["type"] == "rich_text":
                text_array = prop_value.get("rich_text", [])
                text = " ".join([t.get("plain_text", "") for t in text_array])
                processed_page["properties"][prop_name] = text
            elif prop_value["type"] == "number":
                processed_page["properties"][prop_name] = prop_value.get("number")
            elif prop_value["type"] == "select":
                select_value = prop_value.get("select")
                if select_value:
                    processed_page["properties"][prop_name] = select_value.get("name", "")
            elif prop_value["type"] == "multi_select":
                multi_select = prop_value.get("multi_select", [])
                processed_page["properties"][prop_name] = [item.get("name", "") for item in multi_select]
            elif prop_value["type"] == "date":
                date_value = prop_value.get("date")
                if date_value:
                    processed_page["properties"][prop_name] = date_value.get("start")
            elif prop_value["type"] == "checkbox":
                processed_page["properties"][prop_name] = prop_value.get("checkbox", False)
            else:
                # 기타 타입은 원본 그대로 저장
                processed_page["properties"][prop_name] = prop_value
        
        logger.info(f"페이지 {page_id} 정보 조회 완료")
        
        # 응답 구성
        return json.dumps(processed_page)
        
    except Exception as e:
        logger.error(f"페이지 정보 조회 중 오류 발생: {str(e)}")
        return json.dumps({"error": f"페이지 정보 조회 실패: {str(e)}"})

@mcp.tool()
async def notion_get_page_content(page_id: str) -> str:
    """Notion 페이지 내용을 마크다운 형식으로 조회합니다.
    
    Args:
        page_id: 페이지 ID 또는 URL
            
    Returns:
        페이지 내용을 담은 JSON 문자열 (마크다운 형식)
    """
    try:
        page_id = notion_helper._extract_page_id(page_id)
        
        # notion2md를 사용하여 마크다운 변환
        exporter = StringExporter(block_id=page_id)
        markdown_content = exporter.export()
        
        # 페이지 기본 정보 조회
        page_info_json = await notion_get_page(page_id)
        page_info = json.loads(page_info_json)
        
        logger.info(f"페이지 {page_id} 내용 조회 완료")
        
        # 응답 구성
        return json.dumps({
            "page_id": page_id,
            "url": notion_helper._format_notion_url(page_id),
            "title": page_info.get("title", ""),
            "markdown_content": markdown_content,
            "last_edited_time": page_info.get("last_edited_time")
        })
        
    except Exception as e:
        logger.error(f"페이지 내용 조회 중 오류 발생: {str(e)}")
        return json.dumps({"error": f"페이지 내용 조회 실패: {str(e)}"})

@mcp.tool()
async def notion_get_subpages(page_id: str) -> str:
    """Notion 페이지의 하위 페이지 목록을 조회합니다.
    
    Args:
        page_id: 페이지 ID 또는 URL
            
    Returns:
        하위 페이지 목록을 담은 JSON 문자열
    """
    try:
        page_id = notion_helper._extract_page_id(page_id)
        
        # 페이지의 하위 블록 조회
        blocks = notion_helper.client.blocks.children.list(page_id)
        
        # 하위 페이지만 필터링
        subpages = []
        for block in blocks.get("results", []):
            if block["type"] == "child_page":
                subpages.append({
                    "id": block["id"],
                    "url": notion_helper._format_notion_url(block["id"]),
                    "title": block["child_page"]["title"],
                    "type": "page"
                })
            elif block["type"] == "child_database":
                subpages.append({
                    "id": block["id"],
                    "url": notion_helper._format_notion_url(block["id"]),
                    "title": block["child_database"]["title"],
                    "type": "database"
                })
        
        logger.info(f"페이지 {page_id}의 하위 페이지 {len(subpages)}개 조회 완료")
        
        # 응답 구성
        return json.dumps({
            "page_id": page_id,
            "url": notion_helper._format_notion_url(page_id),
            "subpages": subpages,
            "total_subpages": len(subpages)
        })
        
    except Exception as e:
        logger.error(f"하위 페이지 조회 중 오류 발생: {str(e)}")
        return json.dumps({"error": f"하위 페이지 조회 실패: {str(e)}"})
        
@mcp.tool()
async def notion_export_page_md(page_id: str, file_path: Optional[str] = None) -> str:
    """Notion 페이지를 마크다운 파일로 내보냅니다.
    
    Args:
        page_id: 페이지 ID 또는 URL
        file_path: 저장할 파일 경로 (선택 사항)
            
    Returns:
        내보내기 결과를 담은 JSON 문자열
    """
    try:
        page_id = notion_helper._extract_page_id(page_id)
        
        # 페이지 정보 및 내용 조회
        page_content_json = await notion_get_page_content(page_id)
        page_content = json.loads(page_content_json)
        
        md_content = page_content.get("markdown_content", "")
        title = page_content.get("title", f"page_{page_id}")
        
        # 파일 경로가 지정되지 않은 경우 기본 경로 사용
        if not file_path:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pages_dir = os.path.join(script_dir, "notion_pages")
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(pages_dir):
                os.makedirs(pages_dir)
                
            file_path = os.path.join(pages_dir, f"{title}.md")
        
        # 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        logger.info(f"페이지 {page_id}가 {file_path}에 저장되었습니다.")
        
        # 응답 구성
        return json.dumps({
            "page_id": page_id,
            "title": title,
            "file_path": file_path,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"페이지 내보내기 중 오류 발생: {str(e)}")
        return json.dumps({
            "error": f"페이지 내보내기 실패: {str(e)}",
            "success": False
        })

if __name__ == "__main__":
    # 서버 실행
    logger.info("Notion FastMCP 서버 시작")
    mcp.run(transport='stdio') 