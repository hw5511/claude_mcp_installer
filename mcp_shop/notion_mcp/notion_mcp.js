#!/usr/bin/env node

const { Client } = require('@notionhq/client');
const { NotionToMarkdown } = require('notion-to-md');
const { MCP } = require('@modelcontextprotocol/core');
const base64 = require('base64-js');

// 환경 변수에서 Notion API 토큰 가져오기
const NOTION_API_TOKEN = process.env.NOTION_API_TOKEN;
const MARKDOWN_CONVERSION = process.env.NOTION_MARKDOWN_CONVERSION === 'true';

// Notion 클라이언트 초기화
let notion;
let n2m;

// 초기화 함수
function initializeClient() {
  if (!NOTION_API_TOKEN) {
    console.error('NOTION_API_TOKEN 환경 변수가 설정되지 않았습니다.');
    return false;
  }
  
  try {
    notion = new Client({ auth: NOTION_API_TOKEN });
    n2m = new NotionToMarkdown({ notionClient: notion });
    return true;
  } catch (error) {
    console.error('Notion 클라이언트 초기화 오류:', error);
    return false;
  }
}

// MCP 서버 초기화
const mcp = new MCP("notion");
console.info("Initializing server...");

// 응답 포맷팅 함수
async function formatResponse(data, format = 'json') {
  if (format === 'markdown' && MARKDOWN_CONVERSION && data) {
    try {
      if (Array.isArray(data)) {
        // 배열일 경우 각 항목을 마크다운으로 변환
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
        // 단일 페이지일 경우
        const mdBlocks = await n2m.pageToMarkdown(data.id);
        const mdString = n2m.toMarkdownString(mdBlocks);
        return {
          id: data.id,
          title: data.properties?.title?.title?.[0]?.text?.content || 'Untitled',
          content: mdString.parent
        };
      } else if (data.object === 'list' && data.results) {
        // 리스트 결과일 경우
        const results = await Promise.all(data.results.map(async (item) => {
          if (item.object === 'page') {
            try {
              const mdBlocks = await n2m.pageToMarkdown(item.id);
              const mdString = n2m.toMarkdownString(mdBlocks);
              return {
                id: item.id,
                title: item.properties?.title?.title?.[0]?.text?.content || 'Untitled',
                content: mdString.parent,
                url: item.url
              };
            } catch (e) {
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
  
  // 기본적으로 JSON 반환
  return data;
}

// MCP 도구 등록 - 페이지 생성
mcp.registerTool({
  name: 'notion_create_page',
  description: 'Notion에 새 페이지를 생성합니다. 부모 ID(페이지 또는 데이터베이스)와 속성을 지정해야 합니다.',
  parameters: {
    parent: {
      type: 'object',
      description: '페이지가 속할 부모. 데이터베이스 ID 또는 페이지 ID가 필요합니다.',
      required: true
    },
    properties: {
      type: 'object',
      description: '페이지 속성. 부모가 데이터베이스인 경우 필수입니다.',
      required: false
    },
    children: {
      type: 'array',
      description: '페이지에 추가할 블록 목록',
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
      const createPageParams = {
        parent: parent,
        properties: properties || {}
      };
      
      if (children) createPageParams.children = children;
      if (icon) createPageParams.icon = icon;
      if (cover) createPageParams.cover = cover;
      
      const response = await notion.pages.create(createPageParams);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 페이지 내용 저장
mcp.registerTool({
  name: 'notion_update_page',
  description: '기존 Notion 페이지를 업데이트합니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '업데이트할 페이지의 ID',
      required: true
    },
    properties: {
      type: 'object',
      description: '업데이트할 페이지 속성',
      required: false
    },
    archived: {
      type: 'boolean',
      description: '페이지를 보관할지 여부',
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
  handler: async ({ page_id, properties, archived, icon, cover, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const updateParams = {};
      if (properties) updateParams.properties = properties;
      if (archived !== undefined) updateParams.archived = archived;
      if (icon) updateParams.icon = icon;
      if (cover) updateParams.cover = cover;
      
      const response = await notion.pages.update({
        page_id: page_id,
        ...updateParams
      });
      
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 데이터베이스 쿼리
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
      description: '정렬 조건',
      required: false
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
  handler: async ({ database_id, filter, sorts, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const queryParams = {
        database_id: database_id
      };
      
      if (filter) queryParams.filter = filter;
      if (sorts) queryParams.sorts = sorts;
      if (start_cursor) queryParams.start_cursor = start_cursor;
      if (page_size) queryParams.page_size = page_size;
      
      const response = await notion.databases.query(queryParams);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 페이지 정보 가져오기
mcp.registerTool({
  name: 'notion_retrieve_page',
  description: 'Notion 페이지 정보를 가져옵니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '가져올 페이지 ID',
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

// 페이지 내용 가져오기
mcp.registerTool({
  name: 'notion_get_page_content',
  description: 'Notion 페이지의 내용을 가져옵니다',
  parameters: {
    page_id: {
      type: 'string',
      description: '내용을 가져올 페이지 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ page_id, format = 'markdown' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      // 페이지 정보 가져오기
      const pageInfo = await notion.pages.retrieve({ page_id });
      
      // 페이지 블록 가져오기
      const blocks = await n2m.pageToMarkdown(page_id);
      const mdString = n2m.toMarkdownString(blocks);
      
      // 페이지 제목 추출
      let title = 'Untitled';
      if (pageInfo.properties) {
        const titleProp = Object.values(pageInfo.properties).find(
          prop => prop.type === 'title'
        );
        if (titleProp && titleProp.title && titleProp.title.length > 0) {
          title = titleProp.title.map(t => t.plain_text).join('');
        }
      }
      
      if (format === 'markdown') {
        return {
          id: page_id,
          title: title,
          content: mdString.parent,
          url: pageInfo.url
        };
      } else {
        return {
          id: page_id,
          title: title,
          blocks: blocks,
          info: pageInfo,
          url: pageInfo.url
        };
      }
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 데이터베이스 생성
mcp.registerTool({
  name: 'notion_create_database',
  description: 'Notion에 새 데이터베이스를 생성합니다',
  parameters: {
    parent: {
      type: 'object',
      description: '데이터베이스를 생성할 부모 페이지',
      required: true
    },
    title: {
      type: 'array',
      description: '데이터베이스 제목',
      required: false
    },
    properties: {
      type: 'object',
      description: '데이터베이스 속성 스키마',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ parent, title, properties, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const createParams = {
        parent: parent,
        properties: properties
      };
      
      if (title) createParams.title = title;
      
      const response = await notion.databases.create(createParams);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 데이터베이스 정보 가져오기
mcp.registerTool({
  name: 'notion_retrieve_database',
  description: 'Notion 데이터베이스 정보를 가져옵니다',
  parameters: {
    database_id: {
      type: 'string',
      description: '가져올 데이터베이스 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ database_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.databases.retrieve({ database_id });
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 블록 정보 가져오기
mcp.registerTool({
  name: 'notion_retrieve_block',
  description: '특정 Notion 블록에 대한 정보를 가져옵니다',
  parameters: {
    block_id: {
      type: 'string',
      description: '가져올 블록 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ block_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.blocks.retrieve({ block_id });
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 블록 자식 가져오기
mcp.registerTool({
  name: 'notion_retrieve_block_children',
  description: '특정 Notion 블록의 자식 블록들을 가져옵니다',
  parameters: {
    block_id: {
      type: 'string',
      description: '부모 블록 ID',
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
      const params = { block_id };
      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;
      
      const response = await notion.blocks.children.list(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 블록 추가
mcp.registerTool({
  name: 'notion_append_block_children',
  description: '부모 블록에 자식 블록을 추가합니다',
  parameters: {
    block_id: {
      type: 'string',
      description: '부모 블록 ID',
      required: true
    },
    children: {
      type: 'array',
      description: '추가할 블록 객체 배열',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ block_id, children, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.blocks.children.append({
        block_id,
        children
      });
      
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 블록 삭제
mcp.registerTool({
  name: 'notion_delete_block',
  description: '특정 블록을 삭제합니다',
  parameters: {
    block_id: {
      type: 'string',
      description: '삭제할 블록 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ block_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.blocks.delete({
        block_id
      });
      
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 검색
mcp.registerTool({
  name: 'notion_search',
  description: 'Notion에서 페이지나 데이터베이스를 검색합니다',
  parameters: {
    query: {
      type: 'string',
      description: '검색할 텍스트',
      required: false
    },
    filter: {
      type: 'object',
      description: '페이지나 데이터베이스로 결과 제한',
      required: false
    },
    sort: {
      type: 'object',
      description: '결과 정렬 기준',
      required: false
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
  handler: async ({ query, filter, sort, start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const params = {};
      if (query) params.query = query;
      if (filter) params.filter = filter;
      if (sort) params.sort = sort;
      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;
      
      const response = await notion.search(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 사용자 목록 가져오기
mcp.registerTool({
  name: 'notion_list_all_users',
  description: 'Notion 워크스페이스의 모든 사용자 목록을 가져옵니다',
  parameters: {
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
  handler: async ({ start_cursor, page_size, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const params = {};
      if (start_cursor) params.start_cursor = start_cursor;
      if (page_size) params.page_size = page_size;
      
      const response = await notion.users.list(params);
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: '이 기능은 Notion Enterprise 플랜과 Organization API 키가 필요할 수 있습니다.' };
    }
  }
});

// 사용자 정보 가져오기
mcp.registerTool({
  name: 'notion_retrieve_user',
  description: '특정 Notion 사용자 정보를 가져옵니다',
  parameters: {
    user_id: {
      type: 'string',
      description: '가져올 사용자 ID',
      required: true
    },
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ user_id, format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.users.retrieve({
        user_id
      });
      
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message, note: '이 기능은 Notion Enterprise 플랜과 Organization API 키가 필요할 수 있습니다.' };
    }
  }
});

// 봇 사용자 정보 가져오기
mcp.registerTool({
  name: 'notion_retrieve_bot_user',
  description: '현재 토큰과 연결된 봇 사용자 정보를 가져옵니다',
  parameters: {
    format: {
      type: 'string',
      description: '응답 형식 (json 또는 markdown)',
      required: false
    }
  },
  handler: async ({ format = 'json' }) => {
    if (!initializeClient()) return { error: 'Notion 클라이언트 초기화 실패' };
    
    try {
      const response = await notion.users.me();
      return formatResponse(response, format);
    } catch (error) {
      return { error: error.message };
    }
  }
});

// 댓글 생성
mcp.registerTool({
  name: 'notion_create_comment',
  description: 'Notion에 댓글을 생성합니다',
  parameters: {
    rich_text: {
      type: 'array',
      description: '댓글 내용을 나타내는 리치 텍스트 객체 배열',
      required: true
    },
    parent: {
      type: 'object',
      description: '댓글이 속한 부모 객체 (page_id 포함)',
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
      return { error: error.message, note: '이 기능은 통합에 댓글 삽입 기능이 필요합니다.' };
    }
  }
});

// 댓글 가져오기
mcp.registerTool({
  name: 'notion_retrieve_comments',
  description: 'Notion 페이지나 블록의 미해결 댓글 목록을 가져옵니다',
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
      return { error: error.message, note: '이 기능은 통합에 댓글 읽기 기능이 필요합니다.' };
    }
  }
});

// 서버 시작
mcp.start().then(() => {
  console.info("Server started and connected successfully");
  
  // Notion 클라이언트 초기화
  if (!NOTION_API_TOKEN) {
    console.error("NOTION_API_TOKEN이 설정되지 않았습니다. 환경 변수를 확인해주세요.");
  } else {
    initializeClient();
  }
}).catch(err => {
  console.error("Error starting MCP server:", err);
}); 