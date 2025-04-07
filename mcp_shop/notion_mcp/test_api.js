// 테스트 스크립트: notion-to-md 패키지 API 확인
const notionToMd = require("notion-to-md");

console.log("notionToMd type:", typeof notionToMd);
console.log("notionToMd keys:", Object.keys(notionToMd));

// 가능한 생성자 이름들 시도
console.log("NotionToMd exists:", !!notionToMd.NotionToMd);
console.log("NotionToMarkdown exists:", !!notionToMd.NotionToMarkdown);
console.log("default export:", notionToMd);

// 사용 가능한 모든 프로퍼티 확인
for (const key in notionToMd) {
  console.log(`Property: ${key}, Type: ${typeof notionToMd[key]}`);
} 