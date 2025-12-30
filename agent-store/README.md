# OCTOBOX Agent Store

## How to run

run the following command from within the virtual environment.

```bash
uvicorn main:app --reload --port 8000
```

## Simple HTTP tool

To create a simple tool you can use the following json schema:

**JsonPlaceholder**
```json
{
  "name": "get_post_by_id",
  "description": "Fetch a post from JSONPlaceholder by its ID.",
  "enabled": true,

  "endpoint": {
    "transport": "http",
    "url": "https://jsonplaceholder.typicode.com/posts/",
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

**GeoCodeCity**
```json
{
  "name": "geocode_city",
  "description": "Get latitude/longitude for a city name using Open-Meteo geocoding.",
  "enabled": true,
  "endpoint": {
    "transport": "http",
    "url": "https://geocoding-api.open-meteo.com/v1/search",
    "method": "GET",
    "headers": { "Accept": "application/json" }
  },
  "contract": {
    "schema_version": "jsonschema-2020-12",
    "input_schema": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "count": { "type": "integer", "minimum": 1, "maximum": 10, "default": 1 }
      },
      "required": ["name"],
      "additionalProperties": false
    },
    "http": {
      "query": ["name", "count"]
    },
    "tags": ["weather", "open-meteo", "geocoding"],
    "examples": [{ "name": "Berlin", "count": 1 }],
    "read_only": true,
    "idempotent": true,
    "cache_ttl_seconds": 86400
  },
  "response": {
    "schema": {
      "type": "object",
      "properties": {
        "results": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "country": { "type": "string" },
              "latitude": { "type": "number" },
              "longitude": { "type": "number" }
            },
            "required": ["name", "latitude", "longitude"]
          }
        }
      },
      "additionalProperties": true
    },
    "format": "json"
  }
}
```

**WeatherByCoords**
``` json
{
  "name": "get_weather_by_coords",
  "description": "Fetch current weather from Open-Meteo by latitude/longitude.",
  "enabled": true,

  "endpoint": {
    "transport": "http",
    "url": "https://api.open-meteo.com/v1/forecast",
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
        "latitude": {
          "type": "number",
          "minimum": -90,
          "maximum": 90,
          "description": "Latitude in decimal degrees"
        },
        "longitude": {
          "type": "number",
          "minimum": -180,
          "maximum": 180,
          "description": "Longitude in decimal degrees"
        },
        "timezone": {
          "type": "string",
          "default": "auto",
          "description": "Timezone name or 'auto'"
        },

        "current": {
          "type": "string",
          "default": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
          "description": "Comma-separated list of current weather fields to return"
        }
      },
      "required": ["latitude", "longitude"],
      "additionalProperties": false
    },

    "http": {
      "query": ["latitude", "longitude", "timezone", "current"]
    },

    "tags": ["weather", "open-meteo", "forecast"],
    "examples": [
      {
        "latitude": 52.52,
        "longitude": 13.405,
        "timezone": "Europe/Berlin"
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
        "latitude": { "type": "number" },
        "longitude": { "type": "number" },
        "timezone": { "type": "string" },
        "current": {
          "type": "object",
          "properties": {
            "time": { "type": "string" },
            "temperature_2m": { "type": "number" },
            "relative_humidity_2m": { "type": "number" },
            "apparent_temperature": { "type": "number" },
            "precipitation": { "type": "number" },
            "weather_code": { "type": "integer" },
            "wind_speed_10m": { "type": "number" }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "format": "json"
  }
}
```

## Simple internal tool

To create a simple internal tool:

```json
{
  "name": "My Debug Printer",
  "description": "A tool for printing debug messages to the console",
  "enabled": true,
  "endpoint": {
    "transport": "internal",
    "target": "internal.print",
    "static_inputs": {
      "prefix": "[DEBUG] "
    }
  }
}
```