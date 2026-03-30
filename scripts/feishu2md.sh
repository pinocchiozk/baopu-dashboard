#!/bin/bash
# feishu2md - 将飞书云文档导出为 Markdown
# 用法：feishu2md <doc_token> [output.md]

DOC_TOKEN="$1"
OUTPUT="${2:-output.md}"

if [ -z "$DOC_TOKEN" ]; then
    echo "用法：feishu2md <doc_token> [output.md]"
    echo "示例：feishu2md GESQd3tI6oUkLRx4govchHGUnnc doc.md"
    exit 1
fi

# 获取 token
get_token() {
    curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
      -H "Content-Type: application/json" \
      -d '{"app_id":"cli_a9217cf004b89bde","app_secret":"96QItZ1TdXNfuJYaOgvadfycyvepv53E"}' | jq -r '.tenant_access_token'
}

TOKEN=$(get_token)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ 获取 token 失败"
    exit 1
fi

echo "✅ Token 获取成功"

# 获取文档信息
DOC_INFO=$(curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/$DOC_TOKEN" \
  -H "Authorization: Bearer $TOKEN")

DOC_TITLE=$(echo "$DOC_INFO" | jq -r '.data.document.title')
echo "📄 文档标题：$DOC_TITLE"

# 获取 blocks 并转换为 markdown
BLOCKS=$(curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/$DOC_TOKEN/blocks" \
  -H "Authorization: Bearer $TOKEN")

echo "$BLOCKS" | jq -r '
.data.items[] |
if .block_type == 1 then
  "# " + (.page.elements[0].text_run.content // "")
elif .block_type == 3 then
  "\n## " + (.heading1.elements[0].text_run.content // "")
elif .block_type == 4 then
  "\n### " + (.heading2.elements[0].text_run.content // "")
elif .block_type == 5 then
  "\n#### " + (.heading3.elements[0].text_run.content // "")
elif .block_type == 2 then
  "\n" + (.text.elements[0].text_run.content // "")
else
  ""
end
' > "$OUTPUT"

echo "✅ 导出完成：$OUTPUT"
echo ""
echo "📄 内容预览:"
head -20 "$OUTPUT"
