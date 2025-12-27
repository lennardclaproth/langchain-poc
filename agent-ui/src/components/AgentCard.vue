<template>
  <div class="card shadow-sm border-0 rounded-4">
    <div class="card-body p-4">
      <!-- Header -->
      <div class="d-flex justify-content-between align-items-start mb-3">
        <div>
          <h5 class="mb-1">{{ agent.name }}</h5>
          <div class="text-muted small">{{ agent.role }}</div>
        </div>

        <span
          class="badge rounded-pill"
          :class="agent.enabled ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'"
        >
          {{ agent.enabled ? "Enabled" : "Disabled" }}
        </span>
      </div>

      <!-- Instructions -->
      <div v-if="agent.instructions" class="mb-3">
        <div class="small fw-semibold text-muted mb-1">Instructions</div>
        <div class="border rounded-3 p-2 bg-light small">
          {{ agent.instructions }}
        </div>
      </div>

      <!-- Model config -->
      <div class="mb-3">
        <div class="small fw-semibold text-muted mb-2">Model configuration</div>

        <div v-if="agent.model" class="row g-2 small">
          <div class="col-6">
            <span class="text-muted">Provider</span><br />
            <strong>{{ agent.model.provider ?? "—" }}</strong>
          </div>

          <div class="col-6">
            <span class="text-muted">Model</span><br />
            <strong>{{ agent.model.model }}</strong>
          </div>

          <div class="col-6">
            <span class="text-muted">Temperature</span><br />
            <strong>{{ agent.model.temperature ?? "default" }}</strong>
          </div>

          <div class="col-6">
            <span class="text-muted">Max tokens</span><br />
            <strong>{{ agent.model.maxOutputTokens ?? "—" }}</strong>
          </div>

          <div v-if="hasModelParams" class="col-12">
            <span class="text-muted">Params</span>
            <pre class="mt-1 p-2 rounded bg-dark text-light small">
{{ formattedModelParams }}
            </pre>
          </div>
        </div>

        <div v-else class="text-muted small fst-italic">
          No model configured
        </div>
      </div>

      <!-- Context tool -->
      <div class="mb-3">
        <div class="small fw-semibold text-muted mb-2">Context tool</div>

        <div v-if="agent.contextTool" class="small">
          <div>
            <span class="text-muted">Tool ID</span><br />
            <strong>{{ agent.contextTool.toolId }}</strong>
          </div>

          <div class="mt-2">
            <span class="text-muted">Mode</span><br />
            <strong>{{ agent.contextTool.mode ?? "system" }}</strong>
          </div>

          <div v-if="hasContextConfig" class="mt-2">
            <span class="text-muted">Config</span>
            <pre class="mt-1 p-2 rounded bg-dark text-light small">
{{ formattedContextConfig }}
            </pre>
          </div>
        </div>

        <div v-else class="text-muted small fst-italic">
          No context tool attached
        </div>
      </div>

      <!-- Footer -->
      <div class="d-flex justify-content-between text-muted small pt-2 border-top">
        <span>Created: {{ formatDate(agent.createdAt) }}</span>
        <span>Updated: {{ formatDate(agent.updatedAt) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Agent } from "@/domain/api-models";

const props = defineProps<{
  agent: Agent;
}>();

const hasModelParams = computed(
  () => !!props.agent.model?.params && Object.keys(props.agent.model.params).length > 0
);

const hasContextConfig = computed(
  () => !!props.agent.contextTool?.config && Object.keys(props.agent.contextTool.config).length > 0
);

const formattedModelParams = computed(() =>
  JSON.stringify(props.agent.model?.params, null, 2)
);

const formattedContextConfig = computed(() =>
  JSON.stringify(props.agent.contextTool?.config, null, 2)
);

function formatDate(d: Date | null) {
  if (!d) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(d));
}
</script>
