#!/usr/bin/env node

const { Client } = require("@notionhq/client");
const { NotionToMarkdown } = require("notion-to-md");
const base64 = require("base64-js");

// 디버깅을 위한 오류 출력
process.on('uncaughtException', (err) => {
  console.error('치명적인 오류 발생:', err);
});

// 환경 변수에서 Notion API 토큰 가져오기
const NOTION_API_TOKEN = process.env.NOTION_API_TOKEN;     
const MARKDOWN_CONVERSION = process.env.NOTION_MARKDOWN_CONVERSION === "true";

// Notion 클라이언트 초기화
let notion;
let n2m;

// MCP 클래스 정의 (Claude 데스크톱 호환용)
class MCP {
  constructor(name) {
    this.name = name;
    this.tools = [];
    this._toolRegistry = {};
    console.error('디버그: MCP 클래스 초기화됨, 이름:', name);
  }

  registerTool(tool) {
    try {
      console.error('디버그: 도구 등록 시도:', tool.name);
      this.tools.push(tool);
      this._toolRegistry[tool.name] = tool;
      
      // global.__register_tool 문제를 회피
      try {
        if (typeof global !== 'undefined' && global.__register_tool) {
          global.__register_tool(tool);
          console.error('디버그: global.__register_tool 성공:', tool.name);
        } else {
          console.error('디버그: global.__register_tool 없음, 내부 레지스트리 사용');
        }
      } catch (err) {
        // 오류 무시하고 계속 진행
        console.error('디버그: global.__register_tool 오류:', err.message);
      }
    } catch (error) {
      console.error('디버그: 도구 등록 오류:', error);
    }
  }

  start() {
    console.info(`${this.name} MCP 서버 시작 중...`);
    console.error(`디버그: ${this.name} MCP 서버 등록된 도구 수: ${this.tools.length}`);
    
    // 아래 간단한 서버 모킹은 Claude 데스크톱에 필요하지 않지만, 
    // 독립 실행 시 이 코드가 실행될 수 있도록 기본 구현 제공
    try {
      if (typeof process !== 'undefined' && typeof process.send === 'function') {
        process.on('message', (message) => {
          try {
            if (message && message.jsonrpc === '2.0') {
              console.error('디버그: 메시지 수신:', message.method || '메서드 없음');
              if (message.method === 'initialize') {
                console.error('디버그: 초기화 응답 전송');
                process.send({
                  jsonrpc: '2.0',
                  id: message.id,
                  result: {
                    capabilities: {}
                  }
                });
              }
              // 다른 메서드 처리...
            }
          } catch (err) {
            console.error('디버그: 메시지 처리 오류:', err);
          }
        });
      }
    } catch (err) {
      console.error('디버그: 메시지 핸들러 설정 오류:', err);
    }
    
    return Promise.resolve();
  }
}

// 초기화 함수
function initializeClient() {
  if (!NOTION_API_TOKEN) {
    console.error('NOTION_API_TOKEN 환경 변수가 설정되지 않았습니다.');
    return false;
  }

  try {
    notion = new Client({ auth: NOTION_API_TOKEN });
    n2m = new NotionToMarkdown({ notionClient: notion });
    console.error('디버그: Notion 클라이언트 초기화 성공');
    return true;
  } catch (error) {
    console.error('Notion 클라이언트 초기화 오류:', error);
    return false;
  }
}

// MCP 서버 초기화
const mcp = new MCP("notion");
console.info("서버 초기화 중...");

// 응답 처리 함수
async function formatResponse(data, format = 'json') {
  if (format === 'markdown' && MARKDOWN_CONVERSION && data) {
    try {
      if (Array.isArray(data)) {
        // 배열인 경우 각 항목을 마크다운으로 변환
        const markdownResults = [];
        for (const item of data) {
          if (item.object === 'page') {
            const mdBlocks = await n2m.pageToMarkdown(item.id);
            const mdString = n2m.toMarkdownString(mdBlocks);
            markdownResults.push({
              id: item.id,
              title: item.properties?.title?.title?.[0]?.text?.content || 'Untitled',
              content: mdString.parent
            });
          } else {
            markdownResults.push(item);
          }
        }
        return markdownResults;
      } else if (data.object === 'page') {
        // 단일 페이지인 경우
        const mdBlocks = await n2m.pageToMarkdown(data.id);
        const mdString = n2m.toMarkdownString(mdBlocks);
        return {
          id: data.id,
          title: data.properties?.title?.title?.[0]?.text?.content || 'Untitled',
          content: mdString.parent
        };
      } else if (data.object === 'list' && data.results) {
        // 리스트 결과인 경우
        const results = await Promise.all(data.results.map(async (item) => {
          if (item.object === 'page') {
            try {
              const mdBlocks = await n2m.pageToMarkdown(item.id);
              const mdString = n2m.toMarkdownString(mdBlocks);
              return {
                id: item.id,
                title: item.properties?.title?.title?.[0]?.text?.content || 'Untitled',
                content: mdString.parent
              };
            } catch (error) {
              return item;
            }
          }
          return item;
        }));
        return {
          ...data,
          results
        };
      }
    } catch (error) {
      console.error('마크다운 변환 오류:', error);
    }
  }
  return data;
}

// 도구 등록: 페이지 생성
mcp.registerTool({
  name: 'notion_create_page',
  description: 'Notion에 새 페이지를 생성합니다',
  parameters: {
    parent: {
      type: 'object',
      description: '새 페이지의 부모 (데이터베이스 또는 페이지)',
      required: true
    },
    properties: {
      type: 'object',
      description: '페이지 속성 (제목 등)',
      required: true
    },
    children: {
      type: 'array',
      description: '페이지 내용 블록 배열',
      required: false
    },
    icon: {
      type: 'object',
      description: '페이지 아이콘',
      required: false
    },
    cover: {
      type: 'object',
      description: '페이지 커버 이미지',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ parent, properties, children, icon, cover, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const params = {
        parent,
        properties
      };

      if (children) params.children = children;
      if (icon) params.icon = icon;
      if (cover) params.cover = cover;

      const response = await notion.pages.create(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 도구 등록: 페이지에 내용 저장
mcp.registerTool({
  name: 'notion_save_content_to_page',
  description: 'Notion 페이지에 내용을 저장합니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '내용을 저장할 페이지 ID',
      required: true
    },
    children: {
      type: 'array',
      description: '페이지 내용 블록 배열',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ page_id, children, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      // 블록 추가를 위해 여러 번 API 호출 (Notion API 제한)
      const MAX_BLOCKS_PER_REQUEST = 100;
      const results = [];

      for (let i = 0; i < children.length; i += MAX_BLOCKS_PER_REQUEST) {
        const blockBatch = children.slice(i, i + MAX_BLOCKS_PER_REQUEST);
        const response = await notion.blocks.children.append({
          block_id: page_id,
          children: blockBatch
        });
        results.push(response);
      }

      return formatResponse({ success: true, results }, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 도구 등록: 데이터베이스 쿼리
mcp.registerTool({
  name: 'notion_query_database',
  description: 'Notion 데이터베이스를 쿼리합니다',
  parameters: {
    database_id: {
      type: 'string',
      description: '쿼리할 데이터베이스 ID',
      required: true
    },
    filter: {
      type: 'object',
      description: '필터 조건',
      required: false
    },
    sorts: {
      type: 'array',
      description: '정렬 조건 배열',
      required: false
    },
    start_cursor: {
      type: 'string',
      description: '페이징 커서',
      required: false
    },
    page_size: {
      type: 'number',
      description: '페이지 크기',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ database_id, filter, sorts, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const params = {
        database_id
      };

      if (filter) params.filter = filter;
      if (sorts) params.sorts = sorts;
      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;

      const response = await notion.databases.query(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 도구 등록: 페이지 정보 조회
mcp.registerTool({
  name: 'notion_get_page',
  description: 'Notion 페이지 정보를 조회합니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '조회할 페이지 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ page_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const response = await notion.pages.retrieve({ page_id });
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 도구 등록: 페이지 내용 조회
mcp.registerTool({
  name: 'notion_get_page_content',
  description: 'Notion 페이지 내용을 조회합니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '내용을 조회할 페이지 ID',
      required: true
    },
    start_cursor: {
      type: 'string',
      description: '페이징 커서',
      required: false
    },
    page_size: {
      type: 'number',
      description: '페이지 크기',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ page_id, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const params = {
        block_id: page_id
      };

      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;

      const response = await notion.blocks.children.list(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 도구 등록: 데이터베이스 생성
mcp.registerTool({
  name: 'notion_create_database',
  description: 'Notion에 새 데이터베이스를 생성합니다',
  parameters: {
    parent: {
      type: 'object',
      description: '데이터베이스의 부모 페이지',
      required: true
    },
    title: {
      type: 'array',
      description: '데이터베이스 제목',
      required: true
    },
    properties: {
      type: 'object',
      description: '데이터베이스 속성 정의',
      required: true
    },
    icon: {
      type: 'object',
      description: '데이터베이스 아이콘',
      required: false
    },
    cover: {
      type: 'object',
      description: '데이터베이스 커버 이미지',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ parent, title, properties, icon, cover, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const params = {
        parent,
        title,
        properties
      };

      if (icon) params.icon = icon;
      if (cover) params.cover = cover;

      const response = await notion.databases.create(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 댓글 작성
mcp.registerTool({
  name: 'notion_create_comment',
  description: 'Notion에 댓글을 작성합니다',
  parameters: {
    rich_text: {
      type: 'array',
      description: '댓글 내용을 담는 리치 텍스트 객체 배열',
      required: true
    },
    parent: {
      type: 'object',
      description: '댓글을 달한 부모 객체 (page_id 포함)',
      required: false
    },
    discussion_id: {
      type: 'string',
      description: '기존 토론 스레드 ID',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ rich_text, parent, discussion_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      if (!parent && !discussion_id) {
        return { error: 'parent 또는 discussion_id 중 하나가 필요합니다' };
      }

      if (parent && discussion_id) {
        return { error: 'parent와 discussion_id를 동시에 지정할 수 없습니다' };
      }

      const params = {
        rich_text
      };

      if (parent) params.parent = parent;
      if (discussion_id) params.discussion_id = discussion_id;

      const response = await notion.comments.create(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: '이 기능은 호환성을 위한 댓글 삽입 기능이 필요합니다' };
    }
  }
});

// 댓글 가져오기
mcp.registerTool({
  name: 'notion_retrieve_comments',
  description: 'Notion 페이지나 블록에 달린/연결된 댓글 목록을 가져옵니다',
  parameters: {
    block_id: {
      type: 'string',
      description: '댓글을 가져올 블록이나 페이지 ID',
      required: true
    },
    start_cursor: {
      type: 'string',
      description: '다음 페이지를 위한 커서',
      required: false
    },
    page_size: {
      type: 'number',
      description: '결과 페이지 크기 (최대 100)',
      required: false
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ block_id, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };

    try {
      const params = {
        block_id
      };

      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;

      const response = await notion.comments.list(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: '이 기능은 호환성을 위한 댓글 읽기 기능이 필요합니다' };
    }
  }
});

// 서버 시작
mcp.start().then(() => {
  console.info("서버가 성공적으로 시작되었습니다");
  console.error("디버그: 서버 시작 성공");
  
  try {
    // Notion 클라이언트 초기화
    if (!NOTION_API_TOKEN) {
      console.error("NOTION_API_TOKEN이 설정되지 않았습니다. 환경 변수를 확인해주세요.");
    } else {
      initializeClient();
    }
    
    // 서버가 종료되지 않도록 유지
    console.error("디버그: 서버 유지 모드 활성화");
    const interval = setInterval(() => {
      console.error("디버그: 서버 실행 중...");
    }, 30000);
    
    // 정상적인 종료 처리
    process.on('SIGINT', () => {
      console.error('디버그: SIGINT 신호 받음, 정상 종료 중...');
      clearInterval(interval);
      process.exit(0);
    });
    
    process.on('SIGTERM', () => {
      console.error('디버그: SIGTERM 신호 받음, 정상 종료 중...');
      clearInterval(interval);
      process.exit(0);
    });
    
    // 프로세스가 종료되지 않도록 참조 유지
    if (!process.env.NOTION_MCP_TEST_MODE) {
      process.stdin.resume();
    }
    
  } catch (err) {
    console.error("초기화 오류:", err);
  }
}).catch(err => {
  console.error("MCP 서버 시작 오류:", err);
});