#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import inspect
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Notion API 관련 라이브러리
from notion_client import Client
from notion2md.exporter.block import MarkdownExporter, StringExporter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_mcp.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notion_mcp")

class NotionMCP:
    """
    Claude 데스크톱 앱과 Notion을 연결하는 MCP (Multi-Channel Processing) 클래스
    """
    
    def __init__(self):
        """
        Notion MCP 초기화
        """
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
        
        # 메소드 및 도구 매핑
        self.methods = {
            "notion_create_page": self.notion_create_page,
            "notion_save_content_to_page": self.notion_save_content_to_page,
            "notion_query_database": self.notion_query_database,
            "notion_get_page": self.notion_get_page,
            "notion_get_page_content": self.notion_get_page_content,
            "notion_get_subpages": self.notion_get_subpages
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON-RPC 요청을 처리합니다.
        
        Args:
            request: JSON-RPC 요청 객체
            
        Returns:
            Dict[str, Any]: JSON-RPC 응답 객체
        """
        try:
            # JSON-RPC 2.0 검증
            if request.get("jsonrpc") != "2.0":
                return self._error_response(request.get("id"), -32600, "Invalid Request: Not JSON-RPC 2.0")
            
            # 필수 필드 검증
            if "method" not in request:
                return self._error_response(request.get("id"), -32600, "Invalid Request: Method not specified")
            
            method_name = request["method"]
            
            # 메소드 존재 확인
            if method_name not in self.methods:
                return self._error_response(request.get("id"), -32601, f"Method not found: {method_name}")
            
            # 메소드 실행
            method = self.methods[method_name]
            params = request.get("params", {})
            
            # 메소드 시그니처 확인 및 필수 매개변수 검증
            sig = inspect.signature(method)
            required_params = [
                param.name for param in sig.parameters.values()
                if param.default == inspect.Parameter.empty and param.name != 'self'
            ]
            
            for param_name in required_params:
                if param_name not in params:
                    return self._error_response(
                        request.get("id"),
                        -32602,
                        f"Invalid params: Missing required parameter '{param_name}'"
                    )
            
            # 메소드 호출
            result = method(**params)
            
            # 응답 구성
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Request handling error: {str(e)}")
            return self._error_response(request.get("id"), -32603, f"Internal error: {str(e)}")

    def _error_response(self, id: Optional[Union[str, int]], code: int, message: str) -> Dict[str, Any]:
        """
        JSON-RPC 오류 응답을 생성합니다.
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def _format_notion_url(self, page_id: str) -> str:
        """
        Notion 페이지 ID를 URL 형식으로 변환합니다.
        """
        # 하이픈 제거 및 표준 포맷 변환
        clean_id = page_id.replace("-", "")
        return f"https://notion.so/{clean_id}"

    def _extract_page_id(self, url_or_id: str) -> str:
        """
        URL 또는 ID에서 Notion 페이지 ID를 추출합니다.
        """
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

    # 도구 구현 메소드들
    def notion_create_page(self, parent_id: str, title: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Notion에 새 페이지를 생성합니다.
        
        Args:
            parent_id: 상위 페이지 또는 데이터베이스 ID
            title: 페이지 제목
            content: 페이지 내용 (마크다운 형식, 선택 사항)
            
        Returns:
            Dict[str, Any]: 생성된 페이지 정보
        """
        try:
            # 상위 컨테이너가 데이터베이스인지 페이지인지 확인
            parent_id = self._extract_page_id(parent_id)
            
            try:
                # 데이터베이스로 시도
                self.client.databases.retrieve(parent_id)
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
            new_page = self.client.pages.create(
                parent=parent,
                properties=properties
            )
            
            # 내용이 있는 경우 내용 추가
            if content:
                self.notion_save_content_to_page(new_page["id"], content)
            
            logger.info(f"새 페이지가 생성되었습니다: {title}")
            
            # 응답 구성
            return {
                "page_id": new_page["id"],
                "url": self._format_notion_url(new_page["id"]),
                "title": title,
                "created_time": new_page["created_time"]
            }
            
        except Exception as e:
            logger.error(f"페이지 생성 중 오류 발생: {str(e)}")
            raise Exception(f"페이지 생성 실패: {str(e)}")

    def notion_save_content_to_page(self, page_id: str, content: str) -> Dict[str, Any]:
        """
        마크다운 형식으로 Notion 페이지에 내용을 저장합니다.
        
        Args:
            page_id: Notion 페이지 ID 또는 URL
            content: 저장할 마크다운 콘텐츠
            
        Returns:
            Dict[str, Any]: 업데이트된 페이지 정보
        """
        try:
            page_id = self._extract_page_id(page_id)
            
            # 현재 페이지 정보 조회
            page = self.client.pages.retrieve(page_id)
            
            # 마크다운에서 Notion 블록으로 변환 (간단한 변환 예시)
            # 실제로는 더 복잡한 마크다운 파싱 로직이 필요
            blocks = []
            
            # 각 줄을 별도의 블록으로 처리
            for line in content.split("\n"):
                if not line.strip():
                    continue
                    
                # 제목 처리
                if line.startswith("# "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                        }
                    })
                elif line.startswith("## "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                        }
                    })
                elif line.startswith("### "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                        }
                    })
                # 목록 처리
                elif line.startswith("- "):
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                        }
                    })
                elif line.startswith("1. ") or line.startswith("* "):
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                        }
                    })
                # 기본 텍스트 처리
                else:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        }
                    })
            
            # 기존 블록 삭제 후 새 블록 추가
            # 먼저 기존 블록 조회
            existing_blocks = self.client.blocks.children.list(page_id)
            
            # 기존 블록 삭제
            for block in existing_blocks.get("results", []):
                self.client.blocks.delete(block["id"])
            
            # 새 블록 추가
            self.client.blocks.children.append(page_id, children=blocks)
            
            logger.info(f"페이지 {page_id}에 콘텐츠가 업데이트되었습니다.")
            
            # 응답 구성
            return {
                "page_id": page_id,
                "url": self._format_notion_url(page_id),
                "title": page["properties"].get("title", [{}])[0].get("plain_text", ""),
                "updated_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"페이지 콘텐츠 저장 중 오류 발생: {str(e)}")
            raise Exception(f"페이지 콘텐츠 저장 실패: {str(e)}")

    def notion_query_database(self, database_id: str, filter_obj: Optional[Dict[str, Any]] = None, 
                             sorts: Optional[List[Dict[str, Any]]] = None, 
                             page_size: int = 100) -> Dict[str, Any]:
        """
        Notion 데이터베이스를 쿼리합니다.
        
        Args:
            database_id: 데이터베이스 ID 또는 URL
            filter_obj: 필터 객체 (선택 사항)
            sorts: 정렬 기준 (선택 사항)
            page_size: 결과 페이지 크기 (선택 사항)
            
        Returns:
            Dict[str, Any]: 쿼리 결과
        """
        try:
            database_id = self._extract_page_id(database_id)
            
            # 쿼리 파라미터 구성
            query_params = {
                "page_size": page_size
            }
            
            if filter_obj:
                query_params["filter"] = filter_obj
                
            if sorts:
                query_params["sorts"] = sorts
            
            # 데이터베이스 쿼리 요청
            results = self.client.databases.query(database_id, **query_params)
            
            # 결과 가공
            processed_results = []
            for page in results.get("results", []):
                processed_page = {
                    "id": page["id"],
                    "url": self._format_notion_url(page["id"]),
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
            return {
                "database_id": database_id,
                "results": processed_results,
                "has_more": results.get("has_more", False),
                "next_cursor": results.get("next_cursor"),
                "total_results": len(processed_results)
            }
            
        except Exception as e:
            logger.error(f"데이터베이스 쿼리 중 오류 발생: {str(e)}")
            raise Exception(f"데이터베이스 쿼리 실패: {str(e)}")

    def notion_get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Notion 페이지 정보를 조회합니다.
        
        Args:
            page_id: 페이지 ID 또는 URL
            
        Returns:
            Dict[str, Any]: 페이지 정보
        """
        try:
            page_id = self._extract_page_id(page_id)
            
            # 페이지 정보 조회
            page = self.client.pages.retrieve(page_id)
            
            # 결과 가공
            processed_page = {
                "id": page["id"],
                "url": self._format_notion_url(page["id"]),
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
            return processed_page
            
        except Exception as e:
            logger.error(f"페이지 정보 조회 중 오류 발생: {str(e)}")
            raise Exception(f"페이지 정보 조회 실패: {str(e)}")

    def notion_get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Notion 페이지 내용을 마크다운 형식으로 조회합니다.
        
        Args:
            page_id: 페이지 ID 또는 URL
            
        Returns:
            Dict[str, Any]: 페이지 내용 (마크다운 형식)
        """
        try:
            page_id = self._extract_page_id(page_id)
            
            # notion2md를 사용하여 마크다운 변환
            exporter = StringExporter(block_id=page_id)
            markdown_content = exporter.export()
            
            # 페이지 기본 정보 조회
            page_info = self.notion_get_page(page_id)
            
            logger.info(f"페이지 {page_id} 내용 조회 완료")
            
            # 응답 구성
            return {
                "page_id": page_id,
                "url": self._format_notion_url(page_id),
                "title": page_info.get("title", ""),
                "markdown_content": markdown_content,
                "last_edited_time": page_info.get("last_edited_time")
            }
            
        except Exception as e:
            logger.error(f"페이지 내용 조회 중 오류 발생: {str(e)}")
            raise Exception(f"페이지 내용 조회 실패: {str(e)}")

    def notion_get_subpages(self, page_id: str) -> Dict[str, Any]:
        """
        Notion 페이지의 하위 페이지 목록을 조회합니다.
        
        Args:
            page_id: 페이지 ID 또는 URL
            
        Returns:
            Dict[str, Any]: 하위 페이지 목록
        """
        try:
            page_id = self._extract_page_id(page_id)
            
            # 페이지의 하위 블록 조회
            blocks = self.client.blocks.children.list(page_id)
            
            # 하위 페이지만 필터링
            subpages = []
            for block in blocks.get("results", []):
                if block["type"] == "child_page":
                    subpages.append({
                        "id": block["id"],
                        "url": self._format_notion_url(block["id"]),
                        "title": block["child_page"]["title"],
                        "type": "page"
                    })
                elif block["type"] == "child_database":
                    subpages.append({
                        "id": block["id"],
                        "url": self._format_notion_url(block["id"]),
                        "title": block["child_database"]["title"],
                        "type": "database"
                    })
            
            logger.info(f"페이지 {page_id}의 하위 페이지 {len(subpages)}개 조회 완료")
            
            # 응답 구성
            return {
                "page_id": page_id,
                "url": self._format_notion_url(page_id),
                "subpages": subpages,
                "total_subpages": len(subpages)
            }
            
        except Exception as e:
            logger.error(f"하위 페이지 조회 중 오류 발생: {str(e)}")
            raise Exception(f"하위 페이지 조회 실패: {str(e)}")

def main():
    """
    메인 함수: MCP 서버 시작
    """
    logger.info("Notion MCP 서버 시작")
    
    # Notion MCP 인스턴스 생성
    notion_mcp = NotionMCP()
    
    # 표준 입력에서 줄 단위로 JSON-RPC 요청 읽기
    for line in sys.stdin:
        try:
            # 빈 줄 무시
            if not line.strip():
                continue
                
            # JSON 파싱
            request = json.loads(line)
            
            # 요청 처리
            response = notion_mcp.handle_request(request)
            
            # 응답 출력
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"처리 중 예외 발생: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main() 