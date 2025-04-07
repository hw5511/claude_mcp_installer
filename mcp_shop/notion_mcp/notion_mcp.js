#!/usr/bin/env node

const { Client } = require('@notionhq/client');
const { NotionToMarkdown } = require('notion-to-md');
const { MCP } = require('@modelcontextprotocol/core');

// Notion API 클라이언트 초기화
const notion = new Client({
  auth: process.env.NOTION_API_TOKEN,
});

// Notion to Markdown 컨버터 초기화
const n2m = new NotionToMarkdown({ notionClient: notion });

// MCP 서버 초기화
const server = new MCP.Server();

// 페이지 생성 함수
async function createPage(databaseId, properties, content) {
  try {
    // 기본 페이지 생성
    const response = await notion.pages.create({
      parent: {
        database_id: databaseId,
      },
      properties: properties,
    });

    // 내용이 있는 경우 내용 추가
    if (content) {
      await notion.blocks.children.append({
        block_id: response.id,
        children: [
          {
            object: 'block',
            type: 'paragraph',
            paragraph: {
              rich_text: [
                {
                  type: 'text',
                  text: {
                    content: content,
                  },
                },
              ],
            },
          },
        ],
      });
    }

    return response;
  } catch (error) {
    console.error('Error creating page:', error);
    throw error;
  }
}

// 페이지 내용 저장 함수
async function saveContentToPage(pageId, content) {
  try {
    // 페이지 ID에서 하이픈 제거
    const formattedPageId = pageId.replace(/-/g, '');
    
    // 내용을 여러 블록으로 분할 (Notion API 제한 때문)
    const contentBlocks = [];
    const paragraphs = content.split('\n\n');
    
    for (const paragraph of paragraphs) {
      if (paragraph.trim()) {
        contentBlocks.push({
          object: 'block',
          type: 'paragraph',
          paragraph: {
            rich_text: [
              {
                type: 'text',
                text: {
                  content: paragraph,
                },
              },
            ],
          },
        });
      }
    }
    
    // 내용이 많을 경우 청크로 나누기 (100개 블록 제한)
    const chunkSize = 100;
    for (let i = 0; i < contentBlocks.length; i += chunkSize) {
      const chunk = contentBlocks.slice(i, i + chunkSize);
      await notion.blocks.children.append({
        block_id: formattedPageId,
        children: chunk,
      });
    }
    
    return { success: true, pageId: formattedPageId };
  } catch (error) {
    console.error('Error saving content to page:', error);
    throw error;
  }
}

// 데이터베이스 쿼리 함수
async function queryDatabase(databaseId, filter = null, sorts = null) {
  try {
    const queryParams = {
      database_id: databaseId,
    };
    
    if (filter) {
      queryParams.filter = filter;
    }
    
    if (sorts) {
      queryParams.sorts = sorts;
    }
    
    const response = await notion.databases.query(queryParams);
    return response.results;
  } catch (error) {
    console.error('Error querying database:', error);
    throw error;
  }
}

// 페이지 정보 가져오기 함수
async function getPage(pageId) {
  try {
    const formattedPageId = pageId.replace(/-/g, '');
    const response = await notion.pages.retrieve({ page_id: formattedPageId });
    return response;
  } catch (error) {
    console.error('Error retrieving page:', error);
    throw error;
  }
}

// 페이지 내용 가져오기 함수
async function getPageContent(pageId) {
  try {
    const formattedPageId = pageId.replace(/-/g, '');
    
    // 페이지 블록 가져오기
    const blocks = await notion.blocks.children.list({
      block_id: formattedPageId,
    });
    
    // 마크다운으로 변환
    const mdblocks = await n2m.blocksToMarkdown(blocks.results);
    const markdown = n2m.toMarkdownString(mdblocks);
    
    return markdown;
  } catch (error) {
    console.error('Error getting page content:', error);
    throw error;
  }
}

// 데이터베이스 생성 함수
async function createDatabase(parentPageId, title, properties) {
  try {
    const formattedPageId = parentPageId.replace(/-/g, '');
    
    const response = await notion.databases.create({
      parent: {
        page_id: formattedPageId,
      },
      title: [
        {
          type: 'text',
          text: {
            content: title,
          },
        },
      ],
      properties: properties,
    });
    
    return response;
  } catch (error) {
    console.error('Error creating database:', error);
    throw error;
  }
}

// 함수 등록
server.registerTool({
  name: 'save_content_to_page',
  description: 'Save content to a Notion page',
  parameters: {
    type: 'object',
    properties: {
      page_id: {
        type: 'string',
        description: 'ID of the Notion page to save content to',
      },
      content: {
        type: 'string',
        description: 'Content to save to the page',
      },
    },
    required: ['page_id', 'content'],
  },
  handler: async (params) => {
    return await saveContentToPage(params.page_id, params.content);
  },
});

server.registerTool({
  name: 'query_database',
  description: 'Query a Notion database with optional filter and sort',
  parameters: {
    type: 'object',
    properties: {
      database_id: {
        type: 'string',
        description: 'ID of the Notion database to query',
      },
      filter: {
        type: 'object',
        description: 'Optional filter for the query',
      },
      sorts: {
        type: 'array',
        description: 'Optional sort for the query',
      },
    },
    required: ['database_id'],
  },
  handler: async (params) => {
    return await queryDatabase(params.database_id, params.filter, params.sorts);
  },
});

server.registerTool({
  name: 'get_page',
  description: 'Get information about a Notion page',
  parameters: {
    type: 'object',
    properties: {
      page_id: {
        type: 'string',
        description: 'ID of the Notion page to retrieve',
      },
    },
    required: ['page_id'],
  },
  handler: async (params) => {
    return await getPage(params.page_id);
  },
});

server.registerTool({
  name: 'get_page_content',
  description: 'Get the content of a Notion page as markdown',
  parameters: {
    type: 'object',
    properties: {
      page_id: {
        type: 'string',
        description: 'ID of the Notion page to retrieve content from',
      },
    },
    required: ['page_id'],
  },
  handler: async (params) => {
    return await getPageContent(params.page_id);
  },
});

server.registerTool({
  name: 'create_page',
  description: 'Create a new page in a Notion database',
  parameters: {
    type: 'object',
    properties: {
      database_id: {
        type: 'string',
        description: 'ID of the Notion database to create the page in',
      },
      properties: {
        type: 'object',
        description: 'Properties for the new page',
      },
      content: {
        type: 'string',
        description: 'Optional content for the new page',
      },
    },
    required: ['database_id', 'properties'],
  },
  handler: async (params) => {
    return await createPage(params.database_id, params.properties, params.content);
  },
});

server.registerTool({
  name: 'create_database',
  description: 'Create a new database in a Notion page',
  parameters: {
    type: 'object',
    properties: {
      parent_page_id: {
        type: 'string',
        description: 'ID of the parent page to create the database in',
      },
      title: {
        type: 'string',
        description: 'Title for the new database',
      },
      properties: {
        type: 'object',
        description: 'Properties schema for the new database',
      },
    },
    required: ['parent_page_id', 'title', 'properties'],
  },
  handler: async (params) => {
    return await createDatabase(params.parent_page_id, params.title, params.properties);
  },
});

// 서버 시작
server.start();

console.log('Notion MCP server started...'); 