<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h2 class="mb-0">Create tool</h2>
        <div class="text-muted">Define a new tool</div>
      </div>

      <RouterLink to="/tools" class="btn btn-outline-secondary d-flex align-items-center gap-2">
        <i class="bi bi-arrow-left"></i>
        <span>Back</span>
      </RouterLink>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="row g-4">
      <!-- Left: Basics + endpoint -->
      <div class="col-12 col-lg-5">
        <div class="card">
          <div class="card-body">
            <h5 class="mb-3">Basics</h5>

            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model.trim="name" class="form-control" placeholder="e.g. get_post_by_id" />
            </div>

            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea v-model.trim="description" class="form-control" rows="3" />
            </div>

            <div class="form-check mb-4">
              <input id="enabled" v-model="enabled" class="form-check-input" type="checkbox" />
              <label class="form-check-label" for="enabled">Enabled</label>
            </div>

            <hr class="my-4" />

            <h5 class="mb-3">Endpoint</h5>

            <div class="mb-3">
              <label class="form-label">Transport</label>
              <select v-model="endpoint.transport" class="form-select">
                <option value="http">http</option>
                <option value="mcp">mcp</option>
              </select>
            </div>

            <template v-if="endpoint.transport === 'http'">
              <div class="row g-3">
                <div class="col-12 col-md-6">
                  <label class="form-label">Method</label>
                  <select v-model="endpoint.method" class="form-select">
                    <option>GET</option>
                    <option>POST</option>
                    <option>PUT</option>
                    <option>PATCH</option>
                    <option>DELETE</option>
                    <option>HEAD</option>
                    <option>OPTIONS</option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label">URL</label>
                  <input v-model.trim="endpoint.url" class="form-control"
                         placeholder="https://example.com/posts/{id}" />
                </div>

                <div class="col-12">
                  <label class="form-label">Headers (JSON object)</label>
                  <textarea v-model="headersJson" class="form-control font-monospace" rows="5"
                            placeholder='{"Accept":"application/json"}'></textarea>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="row g-3">
                <div class="col-12">
                  <label class="form-label">MCP server</label>
                  <input v-model.trim="endpoint.mcp_server" class="form-control" placeholder="e.g. my-mcp" />
                </div>
                <div class="col-12">
                  <label class="form-label">MCP tool</label>
                  <input v-model.trim="endpoint.mcp_tool" class="form-control" placeholder="e.g. get_post_by_id" />
                </div>
              </div>
            </template>

            <div class="mt-3">
              <label class="form-label">Target (optional)</label>
              <input v-model.trim="endpoint.target" class="form-control" placeholder="optional" />
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Contract builder + response -->
      <div class="col-12 col-lg-7">
        <!-- Contract -->
        <div class="card mb-4">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h5 class="mb-0">Contract</h5>
              <span class="text-muted small">Input schema builder</span>
            </div>

            <div class="row g-3 mb-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Schema version</label>
                <select v-model="contract.schema_version" class="form-select">
                  <option value="jsonschema-2020-12">jsonschema-2020-12</option>
                  <option value="jsonschema-draft-07">jsonschema-draft-07</option>
                </select>
              </div>

              <div class="col-6 col-md-3">
                <label class="form-label">Read-only</label>
                <select v-model="contract.read_only" class="form-select">
                  <option :value="true">true</option>
                  <option :value="false">false</option>
                </select>
              </div>

              <div class="col-6 col-md-3">
                <label class="form-label">Idempotent</label>
                <select v-model="contract.idempotent" class="form-select">
                  <option :value="true">true</option>
                  <option :value="false">false</option>
                </select>
              </div>
            </div>

            <div class="row g-3 mb-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Tags (comma-separated)</label>
                <input v-model="tagsText" class="form-control" placeholder="jsonplaceholder, posts" />
              </div>
              <div class="col-12 col-md-6">
                <label class="form-label">Cache TTL (seconds)</label>
                <input v-model.number="contract.cache_ttl_seconds" type="number" min="0" class="form-control"
                       :disabled="!(contract.read_only && contract.idempotent)"
                       placeholder="Only allowed for read-only + idempotent" />
                <div class="form-text" v-if="!(contract.read_only && contract.idempotent)">
                  Enabled only when read-only=true and idempotent=true.
                </div>
              </div>
            </div>

            <hr class="my-4" />

            <!-- Properties builder -->
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h6 class="mb-0">Input properties</h6>
              <button class="btn btn-sm btn-outline-primary d-flex align-items-center gap-2" type="button" @click="addProp()">
                <i class="bi bi-plus-lg"></i><span>Add property</span>
              </button>
            </div>

            <div v-if="propsList.length === 0" class="text-muted small border rounded p-3">
              No properties yet. Add one (e.g. <span class="font-monospace">id</span>).
            </div>

            <div v-for="(p, idx) in propsList" :key="p._key" class="border rounded p-3 mb-3">
              <div class="d-flex align-items-center justify-content-between mb-2">
                <div class="fw-semibold">
                  Property #{{ idx + 1 }}
                </div>
                <button class="btn btn-sm btn-outline-danger" type="button" @click="removeProp(idx)">
                  <i class="bi bi-trash"></i>
                </button>
              </div>

              <div class="row g-3">
                <div class="col-12 col-md-4">
                  <label class="form-label">Name</label>
                  <input v-model.trim="p.name" class="form-control" placeholder="id" />
                </div>

                <div class="col-12 col-md-4">
                  <label class="form-label">Type</label>
                  <select v-model="p.type" class="form-select">
                    <option value="">(auto)</option>
                    <option value="string">string</option>
                    <option value="integer">integer</option>
                    <option value="number">number</option>
                    <option value="boolean">boolean</option>
                    <option value="object">object</option>
                    <option value="array">array</option>
                  </select>
                </div>

                <div class="col-12 col-md-4">
                  <label class="form-label">Required</label>
                  <div class="form-check mt-2">
                    <input class="form-check-input" type="checkbox" v-model="p.required" :id="`req-${p._key}`" />
                    <label class="form-check-label" :for="`req-${p._key}`">Yes</label>
                  </div>
                </div>

                <div class="col-12">
                  <label class="form-label">Description</label>
                  <input v-model.trim="p.description" class="form-control" placeholder="ID of the post to fetch" />
                </div>

                <!-- enum/default -->
                <div class="col-12 col-md-6">
                  <label class="form-label">Default (JSON)</label>
                  <input v-model="p.defaultJson" class="form-control font-monospace" placeholder='null or "abc" or 1' />
                </div>

                <div class="col-12 col-md-6">
                  <label class="form-label">Enum (comma-separated)</label>
                  <input v-model="p.enumText" class="form-control" placeholder="optional" />
                </div>

                <!-- string constraints -->
                <template v-if="p.type === 'string'">
                  <div class="col-6 col-md-3">
                    <label class="form-label">minLength</label>
                    <input v-model.number="p.minLength" type="number" min="0" class="form-control" />
                  </div>
                  <div class="col-6 col-md-3">
                    <label class="form-label">maxLength</label>
                    <input v-model.number="p.maxLength" type="number" min="0" class="form-control" />
                  </div>
                </template>

                <!-- numeric constraints -->
                <template v-if="p.type === 'integer' || p.type === 'number'">
                  <div class="col-6 col-md-3">
                    <label class="form-label">minimum</label>
                    <input v-model.number="p.minimum" type="number" class="form-control" />
                  </div>
                  <div class="col-6 col-md-3">
                    <label class="form-label">maximum</label>
                    <input v-model.number="p.maximum" type="number" class="form-control" />
                  </div>
                </template>

                <!-- array items -->
                <template v-if="p.type === 'array'">
                  <div class="col-12">
                    <div class="small text-muted mb-1">Items</div>
                    <div class="border rounded p-2 bg-light">
                      <div class="row g-2">
                        <div class="col-12 col-md-4">
                          <label class="form-label small">Type</label>
                          <select v-model="p.items.type" class="form-select form-select-sm">
                            <option value="string">string</option>
                            <option value="integer">integer</option>
                            <option value="number">number</option>
                            <option value="boolean">boolean</option>
                            <option value="object">object</option>
                          </select>
                        </div>
                        <div class="col-12 col-md-8">
                          <label class="form-label small">Description</label>
                          <input v-model.trim="p.items.description" class="form-control form-control-sm" />
                        </div>
                      </div>
                    </div>
                  </div>
                </template>

                <!-- object nested (basic one-level) -->
                <template v-if="p.type === 'object'">
                  <div class="col-12">
                    <div class="d-flex align-items-center justify-content-between mb-1">
                      <div class="small text-muted">Nested properties (optional)</div>
                      <button class="btn btn-sm btn-outline-secondary" type="button" @click="addNestedProp(p)">
                        Add nested
                      </button>
                    </div>

                    <div v-if="p.nested.length === 0" class="small text-muted border rounded p-2">
                      No nested properties.
                    </div>

                    <div v-for="(np, nidx) in p.nested" :key="np._key" class="border rounded p-2 mb-2">
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="small fw-semibold">Nested #{{ nidx + 1 }}</div>
                        <button class="btn btn-sm btn-outline-danger" type="button" @click="removeNestedProp(p, nidx)">
                          <i class="bi bi-trash"></i>
                        </button>
                      </div>

                      <div class="row g-2">
                        <div class="col-12 col-md-4">
                          <label class="form-label small">Name</label>
                          <input v-model.trim="np.name" class="form-control form-control-sm" />
                        </div>
                        <div class="col-12 col-md-4">
                          <label class="form-label small">Type</label>
                          <select v-model="np.type" class="form-select form-select-sm">
                            <option value="string">string</option>
                            <option value="integer">integer</option>
                            <option value="number">number</option>
                            <option value="boolean">boolean</option>
                          </select>
                        </div>
                        <div class="col-12 col-md-4">
                          <label class="form-label small">Required</label>
                          <div class="form-check mt-1">
                            <input class="form-check-input" type="checkbox" v-model="np.required" />
                          </div>
                        </div>
                        <div class="col-12">
                          <label class="form-label small">Description</label>
                          <input v-model.trim="np.description" class="form-control form-control-sm" />
                        </div>
                      </div>
                    </div>

                    <div class="form-text">
                      This is a basic nested editor. You can extend it later to fully recursive objects/arrays.
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Required list preview -->
            <div class="small text-muted">
              Required keys: <span class="font-monospace">{{ requiredKeys.join(", ") || "—" }}</span>
            </div>

            <hr class="my-4" />

            <h6 class="mb-2">HTTP binding</h6>
            <div class="row g-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Path params (comma-separated)</label>
                <input v-model="httpText.path" class="form-control" placeholder="id" />
                <div class="form-text">Any path param must be marked required.</div>
              </div>
              <div class="col-12 col-md-6">
                <label class="form-label">Query params</label>
                <input v-model="httpText.query" class="form-control" placeholder="id" />
              </div>
              <div class="col-12 col-md-6">
                <label class="form-label">JSON body fields</label>
                <input v-model="httpText.json" class="form-control" placeholder="title, body" />
              </div>
              <div class="col-12 col-md-6">
                <label class="form-label">Form fields</label>
                <input v-model="httpText.form" class="form-control" placeholder="file" />
              </div>
            </div>
          </div>
        </div>

        <!-- Response -->
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="mb-3">Response</h5>

            <div class="mb-3">
              <label class="form-label">Format</label>
              <select v-model="response.format" class="form-select">
                <option value="json">json</option>
                <option value="text">text</option>
              </select>
            </div>

            <div class="mb-0">
              <label class="form-label">Schema (JSON)</label>
              <textarea v-model="responseSchemaJson" class="form-control font-monospace" rows="6"
                        placeholder='{"type":"object","properties":{...}}'></textarea>
              <div class="form-text">Optional, but useful for validation and UI.</div>
            </div>
          </div>
        </div>

        <div class="d-flex gap-2">
          <button class="btn btn-primary d-flex align-items-center gap-2" @click="save">
            <i class="bi bi-check-lg"></i><span>Create</span>
          </button>
          <button class="btn btn-outline-secondary" type="button" @click="addExampleFromRequired">
            Add example from required
          </button>
        </div>

        <div v-if="payloadPreview" class="mt-3">
          <div class="small text-muted mb-1">Payload preview</div>
          <pre class="bg-light border rounded p-2 small mb-0">{{ payloadPreview }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const error = ref("");

const name = ref("");
const description = ref("");
const enabled = ref(true);

const endpoint = ref({
  transport: "http",
  url: "https://example.com/",
  method: "GET",
  mcp_server: "",
  mcp_tool: "",
  target: "",
});

const headersJson = ref(JSON.stringify({ Accept: "application/json" }, null, 2));

const contract = ref({
  schema_version: "jsonschema-2020-12",
  read_only: false,
  idempotent: false,
  cache_ttl_seconds: 0,
});

const tagsText = ref("");

const httpText = ref({
  query: "",
  json: "",
  form: "",
  path: "",
});

const response = ref({ format: "text" });
const responseSchemaJson = ref(JSON.stringify({}, null, 2));

const propsList = ref([]);

function uid() {
  return Math.random().toString(36).slice(2);
}

function addProp() {
  propsList.value.push({
    _key: uid(),
    name: "",
    type: "string",
    description: "",
    required: false,
    enumText: "",
    defaultJson: "null",
    minLength: null,
    maxLength: null,
    minimum: null,
    maximum: null,
    items: { type: "string", description: "" }, // for arrays
    nested: [], // for objects
  });
}

function removeProp(idx) {
  propsList.value.splice(idx, 1);
}

function addNestedProp(parent) {
  parent.nested.push({
    _key: uid(),
    name: "",
    type: "string",
    description: "",
    required: false,
  });
}

function removeNestedProp(parent, idx) {
  parent.nested.splice(idx, 1);
}

function splitList(text) {
  return text.split(",").map(s => s.trim()).filter(Boolean);
}

function parseJson(label, text) {
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${label} is not valid JSON.`);
  }
}

const requiredKeys = computed(() =>
  propsList.value
    .filter(p => p.required && p.name.trim())
    .map(p => p.name.trim())
);

function buildProperty(p) {
  const prop = {};

  if (p.type) prop.type = p.type;
  if (p.description?.trim()) prop.description = p.description.trim();

  // enum (best-effort typing: numbers/bools via JSON.parse per token)
  const enumVals = splitList(p.enumText).map(tok => {
    try { return JSON.parse(tok); } catch { return tok; }
  });
  if (enumVals.length) prop.enum = enumVals;

  // default
  if (p.defaultJson?.trim()) {
    try {
      prop.default = JSON.parse(p.defaultJson);
    } catch {
      // allow raw string default if user types unquoted
      prop.default = p.defaultJson;
    }
  }

  // constraints
  if (p.type === "string") {
    if (Number.isInteger(p.minLength)) prop.minLength = p.minLength;
    if (Number.isInteger(p.maxLength)) prop.maxLength = p.maxLength;
  }
  if (p.type === "integer" || p.type === "number") {
    if (typeof p.minimum === "number") prop.minimum = p.minimum;
    if (typeof p.maximum === "number") prop.maximum = p.maximum;
  }

  // array
  if (p.type === "array") {
    prop.items = {};
    if (p.items?.type) prop.items.type = p.items.type;
    if (p.items?.description?.trim()) prop.items.description = p.items.description.trim();
  }

  // object (basic one-level nested)
  if (p.type === "object" && Array.isArray(p.nested) && p.nested.length) {
    const nestedProps = {};
    for (const np of p.nested) {
      if (!np.name?.trim()) continue;
      nestedProps[np.name.trim()] = {
        type: np.type || "string",
        description: np.description?.trim() || undefined,
      };
    }
    prop.properties = nestedProps;
  }

  return prop;
}

function buildInputSchema() {
  const properties = {};
  const required = [];

  for (const p of propsList.value) {
    const key = p.name?.trim();
    if (!key) continue;

    properties[key] = buildProperty(p);
    if (p.required) required.push(key);
  }

  return {
    type: "object",
    properties,
    required,
    additionalProperties: false,
  };
}

function buildHttpBinding(inputSchema) {
  const http = {
    query: splitList(httpText.value.query),
    json: splitList(httpText.value.json),
    form: splitList(httpText.value.form),
    path: splitList(httpText.value.path),
  };

  // If all empty, omit http (your backend allows Optional)
  const any = http.query.length || http.json.length || http.form.length || http.path.length;
  if (!any) return null;

  // Front-end guardrails matching backend validators:
  const propKeys = new Set(Object.keys(inputSchema.properties));
  for (const bucket of ["query", "json", "form", "path"]) {
    for (const k of http[bucket]) {
      if (!propKeys.has(k)) {
        throw new Error(`http.${bucket} contains '${k}' but it's not in input schema properties.`);
      }
    }
  }

  const requiredSet = new Set(inputSchema.required);
  const missingReq = http.path.filter(k => !requiredSet.has(k));
  if (missingReq.length) {
    throw new Error(`http.path params must be required: ${missingReq.join(", ")}`);
  }

  // no-overlap check (mirrors HttpBinding.no_overlap)
  const seen = new Map();
  for (const bucket of ["query", "json", "form", "path"]) {
    for (const k of http[bucket]) {
      if (seen.has(k)) {
        throw new Error(`Param '${k}' appears in both '${seen.get(k)}' and '${bucket}'.`);
      }
      seen.set(k, bucket);
    }
  }

  return http;
}

function buildPayload() {
  const headers = parseJson("Headers", headersJson.value);
  if (!headers || typeof headers !== "object" || Array.isArray(headers)) {
    throw new Error("Headers must be a JSON object.");
  }

  const input_schema = buildInputSchema();

  const http = buildHttpBinding(input_schema);

  const tags = splitList(tagsText.value);

  // TTL rule: only allowed when read_only + idempotent
  let cache_ttl_seconds = Number(contract.value.cache_ttl_seconds || 0);
  if (!cache_ttl_seconds) cache_ttl_seconds = null;
  if (cache_ttl_seconds !== null && !(contract.value.read_only && contract.value.idempotent)) {
    throw new Error("cache_ttl_seconds requires read_only=true and idempotent=true.");
  }

  const respSchema = parseJson("Response schema", responseSchemaJson.value);

  // Endpoint transport-specific shaping (match backend validator expectations: null fields)
  const ep =
    endpoint.value.transport === "http"
      ? {
          transport: "http",
          url: endpoint.value.url || null,
          method: endpoint.value.method || null,
          headers,
          mcp_server: null,
          mcp_tool: null,
          target: endpoint.value.target || null,
        }
      : {
          transport: "mcp",
          url: null,
          method: null,
          headers: {},
          mcp_server: endpoint.value.mcp_server || null,
          mcp_tool: endpoint.value.mcp_tool || null,
          target: endpoint.value.target || null,
        };

  return {
    name: name.value,
    description: description.value,
    enabled: enabled.value,
    endpoint: ep,
    contract: {
      schema_version: contract.value.schema_version,
      input_schema,
      http,
      tags,
      examples: examples.value,
      read_only: contract.value.read_only,
      idempotent: contract.value.idempotent,
      cache_ttl_seconds,
    },
    response: {
      schema: respSchema,
      format: response.value.format,
    },
  };
}

const examples = ref([]);

function addExampleFromRequired() {
  // Create a minimal example object with placeholders based on required keys + type guesses
  const ex = {};
  for (const p of propsList.value) {
    const key = p.name?.trim();
    if (!key || !p.required) continue;

    if (p.type === "integer" || p.type === "number") ex[key] = 1;
    else if (p.type === "boolean") ex[key] = true;
    else if (p.type === "array") ex[key] = [];
    else if (p.type === "object") ex[key] = {};
    else ex[key] = "string";
  }
  examples.value.push(ex);
}

const payloadPreview = computed(() => {
  try {
    error.value = "";
    return JSON.stringify(buildPayload(), null, 2);
  } catch {
    return "";
  }
});

function save() {
  error.value = "";
  try {
    const payload = buildPayload();

    // TODO: replace with POST /api/tools
    console.log("CREATE TOOL", payload);

    router.push("/tools");
  } catch (e) {
    error.value = e.message || "Invalid input.";
  }
}
</script>
