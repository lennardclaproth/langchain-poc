<template>
  <Card>
    <div>
      <!-- Title + status -->
      <div class="d-flex align-items-start justify-content-between gap-2 mb-2">
        <div>
          <h5 class="card-title mb-1">{{ tool.name }}</h5>
          <div class="text-muted small" v-if="tool.description">
            {{ tool.description }}
          </div>
        </div>

        <span
          class="badge"
          :class="tool.enabled ? 'text-bg-success' : 'text-bg-secondary'"
        >
          {{ tool.enabled ? "Enabled" : "Disabled" }}
        </span>
      </div>

      <!-- Endpoint -->
      <div class="border rounded p-2 bg-light mb-3">
        <div class="d-flex align-items-center justify-content-between">
          <span class="badge text-bg-primary">{{ tool.endpoint?.method || "—" }}</span>
          <span class="text-muted small" v-if="transportLabel">
            {{ transportLabel }}
          </span>
        </div>

        <div class="mt-2">
          <div class="small text-muted">Endpoint</div>
          <div class="font-monospace small text-break">
            {{ tool.endpoint?.url || "—" }}
          </div>
        </div>
      </div>

      <!-- Key details -->
      <div class="d-flex flex-wrap gap-2 mb-3">
        <span class="badge text-bg-light border text-dark" v-if="httpParams.path.length">
          Path: {{ httpParams.path.join(", ") }}
        </span>
        <span class="badge text-bg-light border text-dark" v-if="httpParams.query.length">
          Query: {{ httpParams.query.join(", ") }}
        </span>
        <span class="badge text-bg-light border text-dark" v-if="readOnly !== null">
          {{ readOnly ? "Read-only" : "Read-write" }}
        </span>
        <span class="badge text-bg-light border text-dark" v-if="idempotent !== null">
          {{ idempotent ? "Idempotent" : "Non-idempotent" }}
        </span>
        <span class="badge text-bg-light border text-dark" v-if="cacheTtl !== null">
          Cache TTL: {{ cacheTtl }}s
        </span>
      </div>

      <!-- Tags -->
      <div class="mb-3" v-if="tags.length">
        <div class="small text-muted mb-1">Tags</div>
        <div class="d-flex flex-wrap gap-2">
          <span v-for="t in tags" :key="t" class="badge rounded-pill text-bg-dark">
            {{ t }}
          </span>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-auto pt-2 border-top d-flex justify-content-between align-items-center">
        <div class="small text-muted">
          Updated: {{ updatedLabel }}
        </div>

        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-outline-primary" @click="$emit('view', tool)">
            View
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="$emit('edit', tool)">
            Edit
          </button>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from "vue";
import Card from "./atoms/Card.vue";

const props = defineProps({
  tool: { type: Object, required: true },
});

defineEmits(["view", "edit"]);

const transportLabel = computed(() => {
  const t = props.tool?.endpoint?.transport;
  return t ? String(t).toUpperCase() : "";
});

const httpParams = computed(() => {
  const http = props.tool?.contract?.http || {};
  return {
    path: Array.isArray(http.path) ? http.path : [],
    query: Array.isArray(http.query) ? http.query : [],
  };
});

const tags = computed(() => {
  const t = props.tool?.contract?.tags;
  return Array.isArray(t) ? t : [];
});

const cacheTtl = computed(() => {
  const v = props.tool?.contract?.cache_ttl_seconds;
  return typeof v === "number" ? v : null;
});

const readOnly = computed(() => {
  const v = props.tool?.contract?.read_only;
  return typeof v === "boolean" ? v : null;
});

const idempotent = computed(() => {
  const v = props.tool?.contract?.idempotent;
  return typeof v === "boolean" ? v : null;
});

const updatedLabel = computed(() => {
  const s = props.tool?.updated_at;
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleString();
});
</script>
