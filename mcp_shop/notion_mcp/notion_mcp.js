const { Client } = require("@notionhq/client");

// 원본 콘솔 기능 저장 (다른 코드보다 먼저)
const originalConsoleError = console.error;
const originalConsoleLog = console.log;
const originalConsoleInfo = console.info;

// 알파 버전의 올바른 패키지 API를 사용
const notionToMd = require("notion-to-md");
const base64 = require("base64-js");

// 객체가 출력되는 것을 방지하기 위한 안전한 출력 함수
function safeStringify(obj) {
  if (typeof obj === 'string') return obj;
  
  try {
    // 이미 JSON 문자열인 경우 그대로 반환
    if (typeof obj === 'string' && (obj.startsWith('{') || obj.startsWith('['))) {
      JSON.parse(obj); // 유효한 JSON인지 확인
      return obj;
    }
    
    // 객체인 경우 안전하게 문자열화
    if (obj && typeof obj === 'object') {
      if (obj instanceof Error) {
        return JSON.stringify({
          message: obj.message,
          stack: obj.stack
        });
      }
      
      // 순환 참조를 처리하기 위한 객체 복제
      const seen = new WeakSet();
      const safeObj = JSON.stringify(obj, (key, value) => {
        if (typeof value === 'object' && value !== null) {
          if (seen.has(value)) {
            return '[Circular Reference]';
          }
          seen.add(value);
        }
        return value;
      });
      return safeObj;
    }
    
    return String(obj);
  } catch (err) {
    return `[Unstringifiable Object: ${typeof obj}]`;
  }
}

// 콘솔 함수 오버라이드
console.error = function(...args) {
  // 첫 번째 인자가 이미 JSON 객체인 경우 그대로 출력
  if (args.length === 1 && typeof args[0] === 'string' && args[0].startsWith('{') && args[0].includes('"type"')) {
    originalConsoleError(args[0]);
    return;
  }
  
  // 안전하게 JSON 형식으로 변환
  const safeArgs = args.map(arg => {
    if (typeof arg === 'string') return arg;
    return safeStringify(arg);
  });
  
  // 기본 메시지 형식으로 변환
  originalConsoleError(JSON.stringify({ type: "error", message: safeArgs.join(' ') }));
};

console.log = function(...args) {
  // 안전하게 JSON 형식으로 변환
  const safeArgs = args.map(arg => {
    if (typeof arg === 'string') return arg;
    return safeStringify(arg);
  });
  
  originalConsoleLog(JSON.stringify({ type: "log", message: safeArgs.join(' ') }));
};

console.info = function(...args) {
  // 안전하게 JSON 형식으로 변환
  const safeArgs = args.map(arg => {
    if (typeof arg === 'string') return arg;
    return safeStringify(arg);
  });
  
  originalConsoleInfo(JSON.stringify({ type: "info", message: safeArgs.join(' ') }));
};

// 노션투마크다운 내부 로깅 방지를 위한 설정
const originalConsole = {
  log: console.log,
  error: console.error,
  info: console.info
};

// 디버깅을 위한 오류 출력
process.on('uncaughtException', (err) => {
  console.error(`Uncaught exception: ${err.message}`);
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
    console.error(JSON.stringify({ type: "debug", message: `MCP class initialized, name: ${name}` }));
  }

  registerTool(tool) {
    try {
      console.error(JSON.stringify({ type: "debug", message: `Registering tool: ${tool.name}` }));
      this.tools.push(tool);
      this._toolRegistry[tool.name] = tool;
      
      // global.__register_tool 문제를 회피
      try {
        if (typeof global !== 'undefined' && global.__register_tool) {
          global.__register_tool(tool);
          console.error(JSON.stringify({ type: "debug", message: `global.__register_tool success: ${tool.name}` }));
        } else {
          console.error(JSON.stringify({ type: "debug", message: 'global.__register_tool not found, using internal registry' }));
        }
      } catch (err) {
        // 오류 무시하고 계속 진행
        console.error(JSON.stringify({ type: "debug", message: `global.__register_tool error: ${err.message}` }));
      }
    } catch (error) {
      console.error(JSON.stringify({ type: "error", message: `Tool registration error: ${error}` }));
    }
  }

  start() {
    console.error(JSON.stringify({ type: "info", message: `${this.name} MCP server starting...` }));
    console.error(JSON.stringify({ type: "debug", message: `${this.name} MCP server registered tools: ${this.tools.length}` }));
    
    // 아래 간단한 서버 모킹은 Claude 데스크톱에 필요하지 않지만, 
    // 독립 실행 시 이 코드가 실행될 수 있도록 기본 구현 제공
    try {
      if (typeof process !== 'undefined' && typeof process.send === 'function') {
        process.on('message', (message) => {
          try {
            if (message && message.jsonrpc === '2.0') {
              console.error(JSON.stringify({ type: "debug", message: `Message received: ${message.method || 'no method'}` }));
              if (message.method === 'initialize') {
                console.error(JSON.stringify({ type: "debug", message: 'Sending initialize response' }));
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
            console.error(JSON.stringify({ type: "error", message: `Message processing error: ${err}` }));
          }
        });
      }
    } catch (err) {
      console.error(JSON.stringify({ type: "error", message: `Message handler setup error: ${err}` }));
    }
    
    return Promise.resolve();
  }
}

// 초기화 함수
function initializeClient() {
  if (!NOTION_API_TOKEN) {
    console.error(JSON.stringify({ type: "error", message: 'NOTION_API_TOKEN environment variable is not set.' }));
    return false;
  }

  try {
    notion = new Client({ auth: NOTION_API_TOKEN });
    // NotionConverter 객체 생성 시 콘솔 조작을 제거하고 직접 초기화
    n2m = new notionToMd.NotionConverter({ notionClient: notion });
    
    console.error(JSON.stringify({ type: "debug", message: 'Notion client initialized successfully' }));
    return true;
  } catch (error) {
    console.error(JSON.stringify({ type: "error", message: `Notion client initialization error: ${error.message || String(error)}` }));
    return false;
  }
}

// MCP 서버 초기화
const mcp = new MCP("notion");
console.error(JSON.stringify({ type: "info", message: "Initializing server..." }));

// 응답 처리 함수
async function formatResponse(data, format = 'json') {
  if (format === 'markdown' && MARKDOWN_CONVERSION && data) {
    try {
      if (Array.isArray(data)) {
        // 배열인 경우 각 항목을 마크다운으로 변환
        const markdownResults = [];
        for (const item of data) {
          if (item.object === 'page') {
            try {
              // 콘솔 조작 없이 직접 마크다운 변환 실행
              const mdBlocks = await n2m.pageToMarkdown(item.id);
              const mdString = n2m.toMarkdownString(mdBlocks);
              
              markdownResults.push({
                id: item.id,
                title: item.properties?.title?.title?.[0]?.text?.content || 'Untitled',
                content: mdString.parent
              });
            } catch (err) {
              console.error(JSON.stringify({ type: "error", message: `Markdown conversion error: ${err.message || String(err)}` }));
              markdownResults.push(item);
            }
          } else {
            markdownResults.push(item);
          }
        }
        return markdownResults;
      } else if (data.object === 'page') {
        // 단일 페이지인 경우
        try {
          // 콘솔 조작 없이 직접 마크다운 변환 실행
          const mdBlocks = await n2m.pageToMarkdown(data.id);
          const mdString = n2m.toMarkdownString(mdBlocks);
          
          return {
            id: data.id,
            title: data.properties?.title?.title?.[0]?.text?.content || 'Untitled',
            content: mdString.parent
          };
        } catch (err) {
          console.error(JSON.stringify({ type: "error", message: `Markdown conversion error: ${err.message || String(err)}` }));
          return data;
        }
      } else if (data.object === 'list' && data.results) {
        // 리스트 결과인 경우
        const results = await Promise.all(data.results.map(async (item) => {
          if (item.object === 'page') {
            try {
              // 콘솔 조작 없이 직접 마크다운 변환 실행
              const mdBlocks = await n2m.pageToMarkdown(item.id);
              const mdString = n2m.toMarkdownString(mdBlocks);
              
              return {
                id: item.id,
                title: item.properties?.title?.title?.[0]?.text?.content || 'Untitled',
                content: mdString.parent
              };
            } catch (error) {
              console.error(JSON.stringify({ type: "error", message: `Markdown conversion error: ${error.message || String(error)}` }));
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
      // 오류 출력도 JSON 형식으로 변경
      console.error(JSON.stringify({ type: "error", message: `Markdown conversion error: ${error.message || String(error)}` }));
    }
  }
  return data;
}

// 도구 등록: 페이지 생성
mcp.registerTool({
  name: 'notion_create_page',
  description: 'Create a new page in Notion',
  parameters: {
    parent: {
      type: 'object',
      description: 'Parent of the new page (database or page)',
      required: true
    },
    properties: {
      type: 'object',
      description: 'Page properties (title, etc.)',
      required: true
    },
    children: {
      type: 'array',
      description: 'Page content blocks array',
      required: false
    },
    icon: {
      type: 'object',
      description: 'Page icon',
      required: false
    },
    cover: {
      type: 'object',
      description: 'Page cover image',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ parent, properties, children, icon, cover, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Save content to a Notion page',
  parameters: {
    page_id: {
      type: 'string',
      description: 'ID of the page to save content to',
      required: true
    },
    children: {
      type: 'array',
      description: 'Page content blocks array',
      required: true
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ page_id, children, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Query a Notion database',
  parameters: {
    database_id: {
      type: 'string',
      description: 'ID of the database to query',
      required: true
    },
    filter: {
      type: 'object',
      description: 'Filter conditions',
      required: false
    },
    sorts: {
      type: 'array',
      description: 'Sort conditions array',
      required: false
    },
    start_cursor: {
      type: 'string',
      description: 'Pagination cursor',
      required: false
    },
    page_size: {
      type: 'number',
      description: 'Page size',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ database_id, filter, sorts, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Retrieve Notion page information',
  parameters: {
    page_id: {
      type: 'string',
      description: 'ID of the page to retrieve',
      required: true
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ page_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Retrieve Notion page content',
  parameters: {
    page_id: {
      type: 'string',
      description: 'ID of the page to retrieve content from',
      required: true
    },
    start_cursor: {
      type: 'string',
      description: 'Pagination cursor',
      required: false
    },
    page_size: {
      type: 'number',
      description: 'Page size',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ page_id, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Create a new database in Notion',
  parameters: {
    parent: {
      type: 'object',
      description: 'Parent page of the database',
      required: true
    },
    title: {
      type: 'array',
      description: 'Database title',
      required: true
    },
    properties: {
      type: 'object',
      description: 'Database property definitions',
      required: true
    },
    icon: {
      type: 'object',
      description: 'Database icon',
      required: false
    },
    cover: {
      type: 'object',
      description: 'Database cover image',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ parent, title, properties, icon, cover, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

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
  description: 'Create a comment in Notion',
  parameters: {
    rich_text: {
      type: 'array',
      description: 'Rich text objects array for comment content',
      required: true
    },
    parent: {
      type: 'object',
      description: 'Parent object of the comment (includes page_id)',
      required: false
    },
    discussion_id: {
      type: 'string',
      description: 'Existing discussion thread ID',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ rich_text, parent, discussion_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

    try {
      if (!parent && !discussion_id) {
        return { error: 'Either parent or discussion_id is required' };
      }

      if (parent && discussion_id) {
        return { error: 'Cannot specify both parent and discussion_id' };
      }

      const params = {
        rich_text
      };

      if (parent) params.parent = parent;
      if (discussion_id) params.discussion_id = discussion_id;

      const response = await notion.comments.create(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: 'This feature requires the integration to have comment insertion capability' };
    }
  }
});

// 댓글 가져오기
mcp.registerTool({
  name: 'notion_retrieve_comments',
  description: 'Retrieve comments from a Notion page or block',
  parameters: {
    block_id: {
      type: 'string',
      description: 'ID of the block or page to retrieve comments from',
      required: true
    },
    start_cursor: {
      type: 'string',
      description: 'Cursor for the next page',
      required: false
    },
    page_size: {
      type: 'number',
      description: 'Page size (max 100)',
      required: false
    },
    format: {
      type: 'string',
      description: 'Response format (json or markdown)',
      required: false
    }
  },
  handler: async ({ block_id, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion client initialization failed' };

    try {
      const params = {
        block_id
      };

      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;

      const response = await notion.comments.list(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: 'This feature requires the integration to have comment reading capability' };
    }
  }
});

// 서버 시작
mcp.start().then(() => {
  console.error(JSON.stringify({ type: "info", message: "Server started and connected successfully" }));
  console.error(JSON.stringify({ type: "debug", message: "Server start successful" }));
  
  try {
    // Notion 클라이언트 초기화
    if (!NOTION_API_TOKEN) {
      console.error(JSON.stringify({ type: "error", message: "NOTION_API_TOKEN is not set. Please check your environment variables." }));
    } else {
      initializeClient();
    }
    
    // 서버가 종료되지 않도록 유지
    console.error(JSON.stringify({ type: "debug", message: "Activating server keep-alive mode" }));
    const interval = setInterval(() => {
      console.error(JSON.stringify({ type: "debug", message: "Server running..." }));
    }, 30000);
    
    // 정상적인 종료 처리
    process.on('SIGINT', () => {
      console.error(JSON.stringify({ type: "debug", message: 'SIGINT signal received, shutting down gracefully...' }));
      clearInterval(interval);
      process.exit(0);
    });
    
    process.on('SIGTERM', () => {
      console.error(JSON.stringify({ type: "debug", message: 'SIGTERM signal received, shutting down gracefully...' }));
      clearInterval(interval);
      process.exit(0);
    });
    
    // 프로세스가 종료되지 않도록 참조 유지
    if (!process.env.NOTION_MCP_TEST_MODE) {
      process.stdin.resume();
    }
    
  } catch (err) {
    console.error(JSON.stringify({ type: "error", message: `Initialization error: ${err}` }));
  }
}).catch(err => {
  console.error(JSON.stringify({ type: "error", message: `MCP server start error: ${err}` }));
});