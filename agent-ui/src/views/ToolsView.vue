<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-4">
      <div>
        <h2 class="mb-0">Tools</h2>
        <div class="text-muted">All available tools</div>
      </div>

      <RouterLink to="/tools/new" class="btn btn-primary d-flex align-items-center gap-2">
        <i class="bi bi-plus-lg"></i>
        <span>New tool</span>
      </RouterLink>
    </div>

    <div class="row g-4">
      <div v-for="tool in tools" :key="tool.id" class="col-12 col-md-6 col-lg-4">
        <ToolCard :tool="tool" @view="onView" @edit="onEdit" />
      </div>
    </div>
  </div>
</template>

<script setup>
import ToolCard from "../components/ToolCard.vue";

// paste your tools JSON here for now:
const tools = [
  {
    "name": "get_post_by_id",
    "id": "e29b02aa-372b-42ae-8695-6ea750c784f7",
    "enabled": true,
    "endpoint": {
      "transport": "http",
      "url": "https://jsonplaceholder.typicode.com/posts/%7Bid%7D",
      "method": "GET",
      "headers": {
        "Accept": "application/json"
      },
      "mcp_server": null,
      "mcp_tool": null,
      "target": null
    },
    "response": {
      "schema": {
        "type": "object",
        "properties": {
          "userId": {
            "type": "integer"
          },
          "id": {
            "type": "integer"
          },
          "title": {
            "type": "string"
          },
          "body": {
            "type": "string"
          }
        }
      },
      "format": "json"
    },
    "updated_at": "2025-12-18T12:24:08.392788",
    "description": "Fetch a post from JSONPlaceholder by its ID.",
    "contract": {
      "schema_version": "jsonschema-2020-12",
      "input_schema": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "ID of the post to fetch",
            "enum": null,
            "default": null,
            "minLength": null,
            "maxLength": null,
            "minimum": 1,
            "maximum": null,
            "properties": null,
            "items": null
          }
        },
        "required": [
          "id"
        ],
        "additionalProperties": false
      },
      "http": {
        "query": [],
        "json": [],
        "form": [],
        "path": [
          "id"
        ]
      },
      "tags": [
        "jsonplaceholder",
        "posts",
        "example"
      ],
      "examples": [
        {
          "id": 1
        }
      ],
      "read_only": true,
      "idempotent": true,
      "cache_ttl_seconds": 300
    },
    "created_at": "2025-12-18T12:24:08.392780"
  },
  {
    "name": "get_post",
    "id": "770d6ca2-cd33-446b-995a-37d485cb7088",
    "enabled": true,
    "endpoint": {
      "transport": "http",
      "url": "https://jsonplaceholder.typicode.com/posts",
      "method": "GET",
      "headers": {
        "Accept": "application/json"
      },
      "mcp_server": null,
      "mcp_tool": null,
      "target": null
    },
    "response": {
      "schema": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "userId": {
              "type": "integer"
            },
            "id": {
              "type": "integer"
            },
            "title": {
              "type": "string"
            },
            "body": {
              "type": "string"
            }
          }
        }
      },
      "format": "json"
    },
    "updated_at": "2025-12-17T21:45:36.631733",
    "description": "Fetch a post by ID from JSONPlaceholder",
    "contract": {
      "schema_version": "jsonschema-2020-12",
      "input_schema": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "ID of the post to fetch",
            "enum": null,
            "default": null,
            "minLength": null,
            "maxLength": null,
            "minimum": 1,
            "maximum": null,
            "properties": null,
            "items": null
          }
        },
        "required": [
          "id"
        ],
        "additionalProperties": false
      },
      "http": {
        "query": [
          "id"
        ],
        "json": [],
        "form": [],
        "path": []
      },
      "tags": [
        "jsonplaceholder",
        "posts"
      ],
      "examples": [],
      "read_only": true,
      "idempotent": true,
      "cache_ttl_seconds": 60
    },
    "created_at": "2025-12-17T21:45:36.631724"
  }
];

function onView(tool) {
  console.log("view", tool.id);
}

function onEdit(tool) {
  console.log("edit", tool.id);
}
</script>
