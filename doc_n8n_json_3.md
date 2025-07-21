🔍 Verifying Context7 MCP integration...
Context7 Documentation MCP Server running on stdio
✅ MCP server running
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
✅ Query executed successfully
📋 Result:
/cdrom/project/Context7-Explorer/GPT4.1/verify_mcp.py:40: DeprecationWarning: `result.data` is deprecated, use `result.output` instead.
  print(result.data)
Based on the n8n documentation, here's a comprehensive overview of JSON format usage in n8n:

## n8n JSON Data Structure

### Standard Data Format
n8n uses a specific JSON structure for data passed between nodes:

```json
[
  {
    "json": {
      "key1": "value1",
      "key2": {
        "nested": "data"
      }
    },
    "binary": {
      "file-name": {
        "data": "base64-encoded-data",
        "mimeType": "image/png",
        "fileExtension": "png",
        "fileName": "example.png"
      }
    }
  }
]
```

### Key JSON Format Requirements

1. **Root Structure**: Data must be wrapped in an array of objects
2. **json Property**: Regular data goes under the `"json"` key
3. **binary Property**: Binary data goes under the `"binary"` key (optional)

### Common JSON Format Examples

#### Webhook Input Format
```json
[
  {
    "headers": {
      "host": "n8n.instance.address"
    },
    "params": {},
    "query": {},
    "body": {
      "name": "Jim",
      "age": 30,
      "city": "New York"
    }
  }
]
```

#### Configuration Files
```json
{
  "executions": {
    "saveDataOnSuccess": "none"
  },
  "generic": {
    "timezone": "Europe/Berlin"
  },
  "nodes": {
    "exclude": "[\"n8n-nodes-base.executeCommand\"]"
  }
}
```

#### Workflow Definition
```json
{
  "name": "My Workflow",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1
    }
  ],
  "connections": {},
  "active": false
}
```

### JSON Formatting Tips

1. **HTTP Request Node**: Use double curly brackets for JSON expressions:
   ```json
   {{
     {
       "myjson": {
         "name1": "value1",
         "name2": "value2"
       }
     }
   }}
   ```

2. **Code Node Output**: Always return an array of objects with `json` property:
   ```javascript
   return [{ 
     json: { 
       key: "value" 
     } 
   }];
   ```

3. **Data Transformation**: Use expressions like `{{ $json.fieldName }}` to access JSON data

4. **JMESPath Queries**: Use `$jmespath()` for complex JSON queries:
   ```javascript
   {{ $jmespath($json.body.people, "[*].first") }}
   ```

### Common JSON Processing Workflows

- **PDF to JSON**: Extract text from PDF files
- **CSV to JSON**: Convert CSV data to JSON format
- **JSON to File**: Write JSON data to files
- **API Responses**: Process JSON responses from webhooks and HTTP requests

The JSON format in n8n is designed to be flexible yet standardized, ensuring consistent data flow between different nodes and integrations.

