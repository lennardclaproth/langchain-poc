# OCTOBOX Agent Store

## How to run

run the following command from within the virtual environment.

```bash
uvicorn main:app --reload --port 8000
```

## Simple tool

To create a simple tool you can use the following json schema:

```json
{
  "name": "get_post_by_id",
  "description": "Fetch a post from JSONPlaceholder by its ID.",
  "enabled": true,

  "endpoint": {
    "transport": "http",
    "url": "https://jsonplaceholder.typicode.com/posts/{id}",
    "method": "GET",
    "headers": {
      "Accept": "application/json"
    }
  },

  "contract": {
    "schema_version": "jsonschema-2020-12",

    "input_schema": {
      "type": "object",
      "properties": {
        "id": {
          "type": "integer",
          "description": "ID of the post to fetch",
          "minimum": 1
        }
      },
      "required": ["id"],
      "additionalProperties": false
    },

    "http": {
      "path": ["id"]
    },

    "tags": ["jsonplaceholder", "posts", "example"],

    "examples": [
      {
        "id": 1
      }
    ],

    "read_only": true,
    "idempotent": true,
    "cache_ttl_seconds": 300
  },

  "response": {
    "schema": {
      "type": "object",
      "properties": {
        "userId": { "type": "integer" },
        "id": { "type": "integer" },
        "title": { "type": "string" },
        "body": { "type": "string" }
      }
    },
    "format": "json"
  }
}
```
