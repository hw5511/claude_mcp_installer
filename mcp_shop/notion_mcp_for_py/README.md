# Notion MCP (Python)

이 MCP는 Claude 데스크톱 애플리케이션에서 Notion API를 사용할 수 있게 해주는 Python 기반 통합입니다.

## 기능

- Notion 페이지 생성 및 관리
- 데이터베이스 쿼리 및 관리
- Notion 페이지를 마크다운으로 내보내기
- 콘텐츠 조회 및 업데이트

## 설치 요구사항

- Python 3.6 이상
- pip 패키지 관리자
- Notion API 토큰

## 필요한 라이브러리

- [notion-client](https://github.com/ramnes/notion-sdk-py): 공식 Notion Python SDK
- [notion2md](https://github.com/echo724/notion2md): Notion 페이지를 마크다운으로 변환하는 라이브러리

## 설정 방법

### 1. Notion API 토큰 발급

1. [Notion 통합 페이지](https://www.notion.so/my-integrations)에 접속합니다.
2. "새 통합 만들기" 버튼을 클릭합니다.
3. 통합 이름을 지정하고, 관련 워크스페이스를 선택합니다.
4. "제출" 버튼을 클릭하여 통합을 생성합니다.
5. 생성된 "내부 통합 토큰"을 복사합니다.

### 2. 통합 권한 설정

1. Notion에서 통합을 사용할 페이지나 데이터베이스로 이동합니다.
2. 페이지 상단 오른쪽의 "공유" 버튼을 클릭합니다.
3. "통합 초대" 섹션에서 만든 통합을 선택합니다.
4. 필요한 권한을 부여하고 "초대" 버튼을 클릭합니다.

## 도구 목록

이 MCP는 다음과 같은 도구를 제공합니다:

1. **notion_create_page**: Notion에 새 페이지를 생성합니다.
2. **notion_save_content_to_page**: Notion 페이지에 내용을 저장합니다.
3. **notion_query_database**: Notion 데이터베이스를 쿼리합니다.
4. **notion_get_page**: Notion 페이지 정보를 조회합니다.
5. **notion_get_page_content**: Notion 페이지 내용을 조회합니다.
6. **notion_create_database**: Notion에 새 데이터베이스를 생성합니다.
7. **notion_export_to_markdown**: Notion 페이지를 마크다운으로 내보냅니다.

## 마크다운 내보내기 기능

이 MCP의 특별한 기능 중 하나는 Notion 페이지를 마크다운으로 내보내는 기능입니다. 이 기능은 [notion2md](https://github.com/echo724/notion2md) 라이브러리를 사용하여 구현되었습니다.

### 사용 예시:

```python
# 마크다운 문자열로 내보내기
result = notion_export_to_markdown(page_id="페이지_ID")
markdown_content = result["content"]

# 파일로 내보내기
result = notion_export_to_markdown(
    page_id="페이지_ID", 
    output_path="/path/to/output/directory"
)
```

## 문제 해결

- **인증 오류**: API 토큰이 올바른지, 환경 변수가 제대로 설정되었는지 확인하세요.
- **권한 오류**: 통합에 해당 페이지나 데이터베이스에 대한 접근 권한이 있는지 확인하세요.
- **라이브러리 오류**: `pip install notion-client notion2md`를 실행하여 필요한 라이브러리가 설치되었는지 확인하세요.

## 라이선스

MIT 라이선스에 따라 배포됩니다. 