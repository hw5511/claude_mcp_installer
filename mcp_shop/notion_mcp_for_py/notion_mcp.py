#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion MCP for Python
=====================

클라우드 데스크톱 앱을 위한 Notion MCP (Python 버전)
공식 Notion SDK와 notion2md 라이브러리를 사용하여 Notion 페이지를 관리하고 마크다운으로 변환합니다.

주요 기능:
- Notion 페이지 및 데이터베이스 조회/생성/수정/삭제
- 블록 관리
- 사용자 및 댓글 관리
- 마크다운 변환
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from functools import wraps

# 서드파티 라이브러리
try:
    # 공식 Notion SDK
    from notion_client import Client
    # Notion to Markdown 변환 라이브러리
    from notion2md.exporter.block import MarkdownExporter, StringExporter
except ImportError:
    print(json.dumps({"type": "error", "message": "필요한 라이브러리가 설치되지 않았습니다. pip install notion-client notion2md를 실행하세요."}))
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format=json.dumps({"type": "%(levelname)s", "message": "%(message)s"})
)
logger = logging.getLogger("notion_mcp")

# 원래 print 함수를 백업
original_print = print

# 모든 출력을 JSON 형식으로 변환하는 print 오버라이드
def json_print(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    original_print(json.dumps({"type": "log", "message": message}), **kwargs)

# print 함수 오버라이드
print = json_print

# 함수 별칭 생성 유틸리티 함수
def create_alias(original_func: Callable) -> Callable:
    """
    원본 함수의 별칭을 생성합니다.
    별칭은 원본 함수와 동일한 동작을 수행하지만 다른 이름으로 접근할 수 있습니다.
    """
    @wraps(original_func)
    def alias(*args, **kwargs):
        return original_func(*args, **kwargs)
    return alias

class NotionMCP:
    """Notion MCP 메인 클래스"""
    
    def __init__(self, name="notion_py"):
        self.name = name
        self.notion = None
        self.tools = []
        self._tool_registry = {}
        self.debug_print(f"MCP class initialized, name: {name}")
        self.initialize_client()
    
    def debug_print(self, message):
        """디버그 메시지 출력"""
        print(json.dumps({"type": "debug", "message": message}))
    
    def info_print(self, message):
        """정보 메시지 출력"""
        print(json.dumps({"type": "info", "message": message}))
    
    def error_print(self, message):
        """오류 메시지 출력"""
        print(json.dumps({"type": "error", "message": message}))
    
    def initialize_client(self):
        """Notion 클라이언트 초기화"""
        token = os.environ.get("NOTION_API_TOKEN")
        if not token:
            self.error_print("NOTION_API_TOKEN 환경 변수가 설정되지 않았습니다.")
            return False
        
        try:
            # 표준 입출력 리디렉션을 통한 원치 않는 로그 출력 방지
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            
            try:
                self.notion = Client(auth=token)
                self.debug_print("Notion 클라이언트가 성공적으로 초기화되었습니다.")
                return True
            finally:
                # 표준 출력 복원
                sys.stdout.close()
                sys.stderr.close()
                sys.stdout = original_stdout
                sys.stderr = original_stderr
        except Exception as e:
            self.error_print(f"Notion 클라이언트 초기화 오류: {str(e)}")
            return False
    
    def register_tool(self, tool):
        """MCP 도구 등록"""
        try:
            self.debug_print(f"도구 등록: {tool['name']}")
            self.tools.append(tool)
            self._tool_registry[tool['name']] = tool
        except Exception as e:
            self.error_print(f"도구 등록 오류: {str(e)}")
    
    def register_notion_tool(self, name, description, handler, parameters=None):
        """
        더 간결한 Notion 도구 등록 메서드
        
        Args:
            name (str): 도구 이름 ('notion_' 접두사는 자동으로 추가됨)
            description (str): 도구 설명
            handler (callable): 도구 핸들러 함수
            parameters (dict): 도구 매개변수 정의
        """
        if not name.startswith("notion_"):
            name = f"notion_{name}"
            
        tool = {
            "name": name,
            "description": description,
            "handler": handler
        }
        
        if parameters:
            tool["parameters"] = parameters
        
        self.register_tool(tool)
    
    def start(self):
        """MCP 서버 시작"""
        self.info_print(f"{self.name} MCP 서버 시작 중...")
        self.debug_print(f"{self.name} MCP 서버 등록된 도구 수: {len(self.tools)}")
        return True

# MCP 도구 핸들러 데코레이터
def mcp_handler(func):
    """
    MCP 도구 핸들러를 위한 데코레이터
    함수 실행 중 발생하는 예외를 안전하게 처리하고 일관된 오류 형식을 반환합니다.
    
    Args:
        func (callable): 래핑할 대상 함수
        
    Returns:
        callable: 래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {"error": str(e)}
    return wrapper

# MCP 인스턴스 생성
mcp = NotionMCP("notion_py")

# 페이지 생성 도구
@mcp_handler
def create_page(parent, properties, children=None, icon=None, cover=None, format="json"):
    """Notion 페이지 생성"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            params["children"] = children
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        response = mcp.notion.pages.create(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 페이지 내용 저장 도구
@mcp_handler
def save_content_to_page(page_id, children, format="json"):
    """Notion 페이지에 내용 저장"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        # 블록 추가를 위해 여러 번 API 호출 (Notion API 제한)
        MAX_BLOCKS_PER_REQUEST = 100
        results = []
        
        for i in range(0, len(children), MAX_BLOCKS_PER_REQUEST):
            block_batch = children[i:i + MAX_BLOCKS_PER_REQUEST]
            response = mcp.notion.blocks.children.append(
                block_id=page_id,
                children=block_batch
            )
            results.append(response)
        
        return format_response({"success": True, "results": results}, format)
    except Exception as e:
        return {"error": str(e)}

# 데이터베이스 쿼리 도구
@mcp_handler
def query_database(database_id, filter=None, sorts=None, start_cursor=None, page_size=None, format="json"):
    """Notion 데이터베이스 쿼리"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "database_id": database_id
        }
        
        if filter:
            params["filter"] = filter
        if sorts:
            params["sorts"] = sorts
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.databases.query(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 페이지 정보 조회 도구
@mcp_handler
def retrieve_page(page_id, format="json"):
    """Notion 페이지 정보를 조회합니다."""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.pages.retrieve(page_id=page_id)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭으로 처리
get_page = create_alias(retrieve_page)

# 페이지 내용 조회 도구
@mcp_handler
def retrieve_page_content(page_id, start_cursor=None, page_size=None, format="json"):
    """Notion 페이지의 내용을 조회합니다."""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "block_id": page_id
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.blocks.children.list(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭으로 처리
get_page_content = create_alias(retrieve_page_content)

# 데이터베이스 생성 도구
@mcp_handler
def create_database(parent, title, properties, icon=None, cover=None, format="json"):
    """Notion 데이터베이스 생성"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "parent": parent,
            "title": title,
            "properties": properties
        }
        
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        response = mcp.notion.databases.create(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 페이지를 마크다운으로 내보내기 도구
@mcp_handler
def export_page_to_markdown(page_id, output_path=None):
    """Notion 페이지를 마크다운으로 내보내기"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        # 표준 출력 리디렉션 (notion2md의 직접 출력 방지)
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            if output_path:
                # 마크다운 파일로 내보내기
                MarkdownExporter(block_id=page_id, output_path=output_path, download=True).export()
                return {"success": True, "message": f"페이지를 {output_path}에 마크다운으로 내보냈습니다."}
            else:
                # 문자열로 내보내기
                md_content = StringExporter(block_id=page_id).export()
                return {"success": True, "content": md_content}
        finally:
            # 표준 출력 복원
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except Exception as e:
        return {"error": str(e)}

# 블록에 자식 블록 추가 도구
@mcp_handler
def append_block_children(block_id, children, format="json"):
    """Notion 블록에 자식 블록 추가"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.blocks.children.append(
            block_id=block_id,
            children=children
        )
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭 정의 - 함수명 표준화를 위해
add_block_children = create_alias(append_block_children)

# 블록 정보 조회 도구
@mcp_handler
def retrieve_block(block_id, format="json"):
    """Notion 블록 정보 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.blocks.retrieve(block_id=block_id)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 블록 자식 목록 조회 도구
@mcp_handler
def retrieve_block_children(block_id, start_cursor=None, page_size=None, format="json"):
    """Notion 블록 자식 목록 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "block_id": block_id
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.blocks.children.list(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 블록 삭제 도구
@mcp_handler
def delete_block(block_id, format="json"):
    """Notion 블록 삭제"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.blocks.delete(block_id=block_id)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 페이지 속성 업데이트 도구
@mcp_handler
def update_page_properties(page_id, properties, icon=None, cover=None, format="json"):
    """Notion 페이지 속성 업데이트"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "page_id": page_id,
            "properties": properties
        }
        
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        response = mcp.notion.pages.update(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 데이터베이스 업데이트 도구
@mcp_handler
def update_database(database_id, title=None, description=None, properties=None, format="json"):
    """Notion 데이터베이스 업데이트"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "database_id": database_id
        }
        
        if title:
            params["title"] = title
        if description:
            params["description"] = description
        if properties:
            params["properties"] = properties
        
        response = mcp.notion.databases.update(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 데이터베이스 항목 생성 도구
@mcp_handler
def create_database_item(database_id, properties, icon=None, cover=None, children=None, format="json"):
    """Notion 데이터베이스 항목 생성"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        if children:
            params["children"] = children
        
        response = mcp.notion.pages.create(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭 정의 - 함수명 표준화를 위해
add_database_item = create_alias(create_database_item)

# Notion 검색 도구
@mcp_handler
def search(query=None, filter=None, sort=None, start_cursor=None, page_size=None, format="json"):
    """Notion 검색"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {}
        
        if query:
            params["query"] = query
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.search(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭 정의 - 함수명 표준화를 위해
find_notion_content = create_alias(search)

# 모든 사용자 목록 조회 도구
@mcp_handler
def list_all_users(start_cursor=None, page_size=None, format="json"):
    """Notion 워크스페이스의 모든 사용자 목록 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {}
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.users.list(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭 정의 - 함수명 표준화를 위해
get_all_users = create_alias(list_all_users)

# 사용자 정보 조회 도구
@mcp_handler
def retrieve_user(user_id, format="json"):
    """Notion 사용자 정보 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.users.retrieve(user_id=user_id)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 봇 사용자 정보 조회 도구
@mcp_handler
def retrieve_bot_user(format="json"):
    """Notion 봇 사용자 정보 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        response = mcp.notion.users.me()
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 별칭 정의 - 함수명 표준화를 위해
get_bot_user = create_alias(retrieve_bot_user)

# 댓글 생성 도구
@mcp_handler
def create_comment(rich_text, parent=None, discussion_id=None, format="json"):
    """Notion 댓글 생성"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    if not parent and not discussion_id:
        return {"error": "parent 또는 discussion_id 중 하나는 제공되어야 합니다."}
    
    if parent and discussion_id:
        return {"error": "parent와 discussion_id는 동시에 제공될 수 없습니다."}
    
    try:
        params = {
            "rich_text": rich_text
        }
        
        if parent:
            params["parent"] = parent
        if discussion_id:
            params["discussion_id"] = discussion_id
        
        response = mcp.notion.comments.create(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 댓글 목록 조회 도구
@mcp_handler
def retrieve_comments(block_id, start_cursor=None, page_size=None, format="json"):
    """Notion 페이지 또는 블록의 댓글 목록 조회"""
    if not mcp.notion:
        return {"error": "Notion 클라이언트가 초기화되지 않았습니다."}
    
    try:
        params = {
            "block_id": block_id
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = mcp.notion.comments.list(**params)
        return format_response(response, format)
    except Exception as e:
        return {"error": str(e)}

# 응답 형식 지정 함수
def format_response(data, format="json"):
    """응답 데이터의 형식을 지정합니다."""
    if format == "markdown" and data:
        try:
            # 마크다운 변환 로직
            # notion2md 라이브러리의 기능 활용
            return data
        except Exception as e:
            mcp.error_print(f"마크다운 변환 오류: {str(e)}")
    
    return data

# MCP 도구 등록
mcp.register_tool({
    "name": "notion_create_page",
    "description": "Create a new page in Notion",
    "parameters": {
        "parent": {
            "type": "object",
            "description": "Parent of the new page (database or page)",
            "required": True
        },
        "properties": {
            "type": "object",
            "description": "Page properties (title, etc.)",
            "required": True
        },
        "children": {
            "type": "array",
            "description": "Page content blocks array",
            "required": False
        },
        "icon": {
            "type": "object",
            "description": "Page icon",
            "required": False
        },
        "cover": {
            "type": "object",
            "description": "Page cover image",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": create_page
})

mcp.register_tool({
    "name": "notion_save_content_to_page",
    "description": "Save content to a Notion page",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "ID of the page to save content to",
            "required": True
        },
        "children": {
            "type": "array",
            "description": "Page content blocks array",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": save_content_to_page
})

mcp.register_tool({
    "name": "notion_query_database",
    "description": "Query a Notion database",
    "parameters": {
        "database_id": {
            "type": "string",
            "description": "ID of the database to query",
            "required": True
        },
        "filter": {
            "type": "object",
            "description": "Filter conditions",
            "required": False
        },
        "sorts": {
            "type": "array",
            "description": "Sort conditions array",
            "required": False
        },
        "start_cursor": {
            "type": "string",
            "description": "Pagination cursor",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Page size",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": query_database
})

mcp.register_tool({
    "name": "notion_get_page",
    "description": "Retrieve Notion page information",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "ID of the page to retrieve",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_page
})

mcp.register_tool({
    "name": "notion_get_page_content",
    "description": "Retrieve Notion page content",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "ID of the page to retrieve content from",
            "required": True
        },
        "start_cursor": {
            "type": "string",
            "description": "Pagination cursor",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Page size",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_page_content
})

mcp.register_tool({
    "name": "notion_create_database",
    "description": "Create a new database in Notion",
    "parameters": {
        "parent": {
            "type": "object",
            "description": "Parent page of the database",
            "required": True
        },
        "title": {
            "type": "array",
            "description": "Database title",
            "required": True
        },
        "properties": {
            "type": "object",
            "description": "Database property definitions",
            "required": True
        },
        "icon": {
            "type": "object",
            "description": "Database icon",
            "required": False
        },
        "cover": {
            "type": "object",
            "description": "Database cover image",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": create_database
})

mcp.register_tool({
    "name": "notion_export_to_markdown",
    "description": "Export Notion page to markdown",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "ID of the page to export",
            "required": True
        },
        "output_path": {
            "type": "string",
            "description": "Directory path where to save the exported markdown",
            "required": False
        }
    },
    "handler": export_page_to_markdown
})

mcp.register_tool({
    "name": "notion_append_block_children",
    "description": "Append child blocks to a parent block",
    "parameters": {
        "block_id": {
            "type": "string",
            "description": "The ID of the parent block",
            "required": True
        },
        "children": {
            "type": "array",
            "description": "Array of block objects to append",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": append_block_children
})

mcp.register_tool({
    "name": "notion_retrieve_block",
    "description": "Retrieve information about a specific block",
    "parameters": {
        "block_id": {
            "type": "string",
            "description": "The ID of the block to retrieve",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_block
})

mcp.register_tool({
    "name": "notion_retrieve_block_children",
    "description": "Retrieve the children of a specific block",
    "parameters": {
        "block_id": {
            "type": "string",
            "description": "The ID of the parent block",
            "required": True
        },
        "start_cursor": {
            "type": "string",
            "description": "Cursor for the next page of results",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Number of blocks to retrieve (default: 100, max: 100)",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_block_children
})

mcp.register_tool({
    "name": "notion_delete_block",
    "description": "Delete a specific block",
    "parameters": {
        "block_id": {
            "type": "string",
            "description": "The ID of the block to delete",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": delete_block
})

mcp.register_tool({
    "name": "notion_retrieve_page",
    "description": "Retrieve information about a specific page",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "The ID of the page to retrieve",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_page
})

mcp.register_tool({
    "name": "notion_update_page_properties",
    "description": "Update properties of a page",
    "parameters": {
        "page_id": {
            "type": "string",
            "description": "The ID of the page to update",
            "required": True
        },
        "properties": {
            "type": "object",
            "description": "Properties to update",
            "required": True
        },
        "icon": {
            "type": "object",
            "description": "Page icon",
            "required": False
        },
        "cover": {
            "type": "object",
            "description": "Page cover image",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": update_page_properties
})

mcp.register_tool({
    "name": "notion_update_database",
    "description": "Update information about a database",
    "parameters": {
        "database_id": {
            "type": "string",
            "description": "The ID of the database to update",
            "required": True
        },
        "title": {
            "type": "array",
            "description": "New title for the database",
            "required": False
        },
        "description": {
            "type": "array",
            "description": "New description for the database",
            "required": False
        },
        "properties": {
            "type": "object",
            "description": "Updated property schema",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": update_database
})

mcp.register_tool({
    "name": "notion_create_database_item",
    "description": "Create a new item in a Notion database",
    "parameters": {
        "database_id": {
            "type": "string",
            "description": "The ID of the database to add the item to",
            "required": True
        },
        "properties": {
            "type": "object",
            "description": "The properties of the new item",
            "required": True
        },
        "icon": {
            "type": "object",
            "description": "Item icon",
            "required": False
        },
        "cover": {
            "type": "object",
            "description": "Item cover image",
            "required": False
        },
        "children": {
            "type": "array",
            "description": "Item content blocks",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": create_database_item
})

mcp.register_tool({
    "name": "notion_search",
    "description": "Search pages or databases by title",
    "parameters": {
        "query": {
            "type": "string",
            "description": "Text to search for in page or database titles",
            "required": False
        },
        "filter": {
            "type": "object",
            "description": "Criteria to limit results to pages or databases",
            "required": False
        },
        "sort": {
            "type": "object",
            "description": "Criteria to sort the results",
            "required": False
        },
        "start_cursor": {
            "type": "string",
            "description": "Pagination start cursor",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Number of results to retrieve (default: 100, max: 100)",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": search
})

mcp.register_tool({
    "name": "notion_list_all_users",
    "description": "List all users in the Notion workspace",
    "parameters": {
        "start_cursor": {
            "type": "string",
            "description": "Pagination start cursor for listing users",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Number of users to retrieve (max: 100)",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": list_all_users
})

mcp.register_tool({
    "name": "notion_retrieve_user",
    "description": "Retrieve a specific user by user_id in Notion",
    "parameters": {
        "user_id": {
            "type": "string",
            "description": "The ID of the user to retrieve",
            "required": True
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_user
})

mcp.register_tool({
    "name": "notion_retrieve_bot_user",
    "description": "Retrieve the bot user associated with the current token in Notion",
    "parameters": {
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_bot_user
})

mcp.register_tool({
    "name": "notion_create_comment",
    "description": "Create a comment in Notion",
    "parameters": {
        "rich_text": {
            "type": "array",
            "description": "Array of rich text objects representing the comment content",
            "required": True
        },
        "parent": {
            "type": "object",
            "description": "Must include page_id if used",
            "required": False
        },
        "discussion_id": {
            "type": "string",
            "description": "An existing discussion thread ID",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": create_comment
})

mcp.register_tool({
    "name": "notion_retrieve_comments",
    "description": "Retrieve a list of unresolved comments from a Notion page or block",
    "parameters": {
        "block_id": {
            "type": "string",
            "description": "The ID of the block or page whose comments you want to retrieve",
            "required": True
        },
        "start_cursor": {
            "type": "string",
            "description": "Pagination start cursor",
            "required": False
        },
        "page_size": {
            "type": "number",
            "description": "Number of comments to retrieve (max: 100)",
            "required": False
        },
        "format": {
            "type": "string",
            "description": "Response format (json or markdown)",
            "required": False
        }
    },
    "handler": retrieve_comments
})

# 서버 시작 및 유지
if __name__ == "__main__":
    print(json.dumps({"type": "info", "message": "서버 초기화 중..."}), file=sys.stderr)
    
    try:
        # 서버 시작
        if mcp.start():
            print(json.dumps({"type": "info", "message": "서버가 성공적으로 시작되었습니다."}), file=sys.stderr)
            
            # JSON-RPC 처리를 위한 코드
            # 표준 입력에서 메시지 읽기
            def read_request_from_stdin():
                line = sys.stdin.readline()
                if not line:
                    return None
                return json.loads(line)
            
            # 표준 출력으로 응답 보내기
            def send_response(response):
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            
            # 메서드 처리
            def handle_method(request):
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")
                
                print(json.dumps({"type": "info", "message": f"Message from client: {json.dumps(request)}"}), file=sys.stderr)
                
                # initialize 메서드 처리
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "name": "notion_py",
                            "version": "1.0.0",
                            "capabilities": {
                                "tools": mcp.tools
                            }
                        }
                    }
                    return response
                # notifications 메서드 처리
                elif method.startswith("notifications/"):
                    # 알림은 응답이 필요 없음
                    return None
                # tool 메서드 호출 처리
                elif method.startswith("tools/"):
                    tool_name = method.split("/")[1]
                    if tool_name in mcp._tool_registry:
                        tool = mcp._tool_registry[tool_name]
                        handler = tool.get("handler")
                        if handler:
                            result = handler(**params)
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": result
                            }
                            return response
                    
                    # 도구를 찾지 못했거나 처리에 실패한 경우
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    return response
                # 기타 메서드 (아직 구현되지 않음)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {}  # 일단 빈 결과로 응답
                    }
                    return response
            
            # 메인 루프
            while True:
                try:
                    request = read_request_from_stdin()
                    if request is None:
                        break
                    
                    print(json.dumps({"type": "debug", "message": f"Request received: {request.get('method', 'unknown')}"}), file=sys.stderr)
                    
                    response = handle_method(request)
                    if response:  # notifications는 응답이 없음
                        send_response(response)
                except Exception as e:
                    print(json.dumps({"type": "error", "message": f"Error processing request: {str(e)}"}), file=sys.stderr)
                    
                    # 오류 응답
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if 'request' in locals() else None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    send_response(error_response)
        else:
            print(json.dumps({"type": "error", "message": "서버 시작 실패"}), file=sys.stderr)
    except Exception as e:
        print(json.dumps({"type": "error", "message": f"서버 오류: {str(e)}"}), file=sys.stderr) 