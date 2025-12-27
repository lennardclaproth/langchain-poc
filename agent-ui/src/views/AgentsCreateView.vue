<template>
  <div class="container-fluid">
    <!-- Header -->
    <div class="mb-4">
      <h2 class="mb-1">Create agent</h2>
      <p class="text-muted mb-0">Define an agent, its model config, and an optional context tool.</p>
    </div>

    <div class="row g-4">
      <!-- Form -->
      <div class="col-12 col-lg-7">
        <form class="card shadow-sm border-0 rounded-4" @submit.prevent="create">
          <div class="card-body p-4">
            <!-- Basics -->
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h5 class="mb-0">Basics</h5>
              <span class="badge rounded-pill" :class="form.enabled ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'">
                {{ form.enabled ? "Enabled" : "Disabled" }}
              </span>
            </div>

            <div class="row g-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Name</label>
                <input v-model.trim="form.name" class="form-control" placeholder="Contract Builder" />
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Role</label>
                <input v-model.trim="form.role" class="form-control" placeholder="Builds and validates tool contracts" />
              </div>

              <div class="col-12">
                <label class="form-label">Instructions (optional)</label>
                <textarea
                  v-model.trim="form.instructions"
                  class="form-control"
                  rows="4"
                  placeholder="Give the agent rules, style, constraints…"
                />
                <div class="form-text">Leave empty if not needed.</div>
              </div>

              <div class="col-12">
                <div class="form-check form-switch">
                  <input id="enabled" class="form-check-input" type="checkbox" v-model="form.enabled" />
                  <label class="form-check-label" for="enabled">Enabled</label>
                </div>
              </div>
            </div>

            <hr class="my-4" />

            <!-- Model config -->
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h5 class="mb-0">Model configuration</h5>
              <div class="form-check form-switch m-0">
                <input id="useModel" class="form-check-input" type="checkbox" v-model="useModel" />
                <label class="form-check-label" for="useModel">Attach model</label>
              </div>
            </div>

            <div v-if="useModel" class="row g-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Provider (optional)</label>
                <input v-model.trim="form.model.provider" class="form-control" placeholder="openai" />
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Model</label>
                <input v-model.trim="form.model.model" class="form-control" placeholder="gpt-4o-mini" />
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Temperature (optional)</label>
                <input v-model.number="form.model.temperature" type="number" step="0.1" min="0" max="2" class="form-control" placeholder="0.2" />
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Max output tokens (optional)</label>
                <input v-model.number="form.model.maxOutputTokens" type="number" min="1" class="form-control" placeholder="1024" />
              </div>

              <div class="col-12">
                <label class="form-label">Params (JSON, optional)</label>
                <textarea
                  v-model.trim="modelParamsText"
                  class="form-control font-monospace"
                  rows="4"
                  placeholder='{"top_p":0.9}'
                />
                <div class="form-text">
                  Stored into <code>model.params</code>. Invalid JSON will block saving.
                </div>
              </div>
            </div>

            <div v-else class="text-muted small fst-italic">
              No model attached.
            </div>

            <hr class="my-4" />

            <!-- Context tool -->
            <div class="d-flex align-items-center justify-content-between mb-2">
              <h5 class="mb-0">Context tool</h5>
              <div class="form-check form-switch m-0">
                <input id="useTool" class="form-check-input" type="checkbox" v-model="useTool" />
                <label class="form-check-label" for="useTool">Attach tool</label>
              </div>
            </div>

            <div v-if="useTool" class="row g-3">
              <div class="col-12 col-md-6">
                <label class="form-label">Tool ID</label>
                <input v-model.trim="form.contextTool.toolId" class="form-control" placeholder="contract-context" />
              </div>

              <div class="col-12 col-md-6">
                <label class="form-label">Mode</label>
                <select v-model="form.contextTool.mode" class="form-select">
                  <option value="system">system</option>
                  <option value="user">user</option>
                  <option value="tool">tool</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label">Tool config (JSON, optional)</label>
                <textarea
                  v-model.trim="toolConfigText"
                  class="form-control font-monospace"
                  rows="4"
                  placeholder='{"maxContracts":5}'
                />
                <div class="form-text">
                  Stored into <code>contextTool.config</code>. Invalid JSON will block saving.
                </div>
              </div>
            </div>

            <div v-else class="text-muted small fst-italic">
              No context tool attached.
            </div>

            <!-- Actions -->
            <div class="d-flex gap-2 justify-content-end mt-4">
              <button type="button" class="btn btn-outline-secondary" @click="reset">
                Reset
              </button>
              <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
                Create agent
              </button>
            </div>

            <div v-if="error" class="alert alert-danger mt-3 mb-0">
              {{ error }}
            </div>
          </div>
        </form>
      </div>

      <!-- Live preview -->
      <div class="col-12 col-lg-5">
        <div class="sticky-top" style="top: 1rem;">
          <div class="mb-2 text-muted small">Preview</div>
          <AgentCard :agent="previewAgent" />
          <div class="mt-3">
            <div class="text-muted small mb-1">Payload preview</div>
            <pre class="p-3 rounded bg-dark text-light small mb-0">{{ payloadPreview }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import AgentCard from "@/components/AgentCard.vue";
import type { Agent, AgentContextTool, AgentModelConfig } from "@/domain/api-models";

type CreateAgentRequest = {
  name: string;
  role: string;
  instructions: string | null;
  enabled: boolean;
  model: AgentModelConfig | null;
  contextTool: AgentContextTool | null;
};

const useModel = ref(true);
const useTool = ref(false);

const modelParamsText = ref('{"top_p":0.9}');
const toolConfigText = ref("");

const error = ref<string | null>(null);

const form = reactive<{
  name: string;
  role: string;
  instructions: string;
  enabled: boolean;
  model: AgentModelConfig;
  contextTool: AgentContextTool;
}>({
  name: "",
  role: "",
  instructions: "",
  enabled: true,
  model: {
    provider: "",
    model: "gpt-4o-mini",
    temperature: 0.2,
    maxOutputTokens: 1024,
    params: {},
  },
  contextTool: {
    toolId: "",
    mode: "system",
    config: {},
  },
});

function tryParseJson(text: string): Record<string, unknown> | null {
  const trimmed = text.trim();
  if (!trimmed) return {};
  try {
    const v = JSON.parse(trimmed);
    if (v === null || Array.isArray(v) || typeof v !== "object") return null;
    return v as Record<string, unknown>;
  } catch {
    return null;
  }
}

const modelParams = computed(() => (useModel.value ? tryParseJson(modelParamsText.value) : {}));
const toolConfig = computed(() => (useTool.value ? tryParseJson(toolConfigText.value) : {}));

const canSubmit = computed(() => {
  if (!form.name.trim() || !form.role.trim()) return false;
  if (useModel.value) {
    if (!form.model.model.trim()) return false;
    if (modelParams.value === null) return false;
  }
  if (useTool.value) {
    if (!form.contextTool.toolId.trim()) return false;
    if (toolConfig.value === null) return false;
  }
  return true;
});

const payload = computed<CreateAgentRequest>(() => {
  const instructions = form.instructions.trim();
  const model: AgentModelConfig | null = useModel.value
    ? {
        provider: form.model.provider?.trim() || undefined,
        model: form.model.model.trim(),
        temperature: form.model.temperature ?? undefined,
        maxOutputTokens: form.model.maxOutputTokens ?? null,
        params: modelParams.value ?? undefined,
      }
    : null;

  const contextTool: AgentContextTool | null = useTool.value
    ? {
        toolId: form.contextTool.toolId.trim(),
        mode: form.contextTool.mode ?? "system",
        config: toolConfig.value ?? undefined,
      }
    : null;

  return {
    name: form.name.trim(),
    role: form.role.trim(),
    instructions: instructions ? instructions : null,
    enabled: form.enabled,
    model,
    contextTool,
  };
});

const payloadPreview = computed(() => JSON.stringify(payload.value, null, 2));

const previewAgent = computed<Agent>(() => ({
  id: "preview",
  name: payload.value.name || "Unnamed agent",
  role: payload.value.role || "Role",
  instructions: payload.value.instructions,
  enabled: payload.value.enabled,
  model: payload.value.model,
  contextTool: payload.value.contextTool,
  createdAt: null,
  updatedAt: null,
}));

function reset() {
  error.value = null;
  form.name = "";
  form.role = "";
  form.instructions = "";
  form.enabled = true;

  useModel.value = true;
  form.model.provider = "";
  form.model.model = "gpt-4o-mini";
  form.model.temperature = 0.2;
  form.model.maxOutputTokens = 1024;
  modelParamsText.value = '{"top_p":0.9}';

  useTool.value = false;
  form.contextTool.toolId = "";
  form.contextTool.mode = "system";
  toolConfigText.value = "";
}

async function create() {
  error.value = null;

  // Client-side validation w/ helpful error
  if (!canSubmit.value) {
    if (useModel.value && modelParams.value === null) {
      error.value = "Model params must be valid JSON (an object).";
      return;
    }
    if (useTool.value && toolConfig.value === null) {
      error.value = "Tool config must be valid JSON (an object).";
      return;
    }
    error.value = "Please fill all required fields.";
    return;
  }

  // Replace this with your API call
  // await api.createAgent(payload.value)
  console.log("Create agent payload:", payload.value);

  // For demo UX
  reset();
}
</script>
