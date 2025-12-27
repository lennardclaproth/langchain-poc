<template>
  <div>
    <!-- Page header -->
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h2 class="mb-1">Agents</h2>
        <p class="text-muted mb-0">Agent configuration and status.</p>
      </div>

      <Button
            :as="RouterLink"
            v-bind="{ to: '/agents/new' }"
            variant="primary"
            class="d-flex align-items-center gap-2"
          >
            <Icon name="plus-lg" />
            <span>New Agent</span>
          </Button>
    </div>

    <!-- Agents grid -->
    <div class="row g-4">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="col-12 col-md-6 col-xl-4"
      >
        <AgentCard :agent="agent" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import AgentCard from "@/components/AgentCard.vue";
import type { Agent } from "@/domain/api-models";
import { RouterLink } from "vue-router";
import Button from "@/components/atoms/Button.vue";
import Icon from "@/components/atoms/Icon.vue";
/**
 * Mock data — replace later with API call
 */
const agents = ref<Agent[]>([
  {
    id: "agent-1",
    name: "Contract Builder",
    role: "Builds and validates tool contracts",
    instructions:
      "Ensure the schema follows JSON Schema 2020-12 and validate all inputs strictly.",
    enabled: true,
    model: {
      provider: "openai",
      model: "gpt-4o-mini",
      temperature: 0.2,
      maxOutputTokens: 1024,
      params: {
        top_p: 0.9,
      },
    },
    contextTool: {
      toolId: "contract-context",
      mode: "system",
      config: {
        maxContracts: 5,
      },
    },
    createdAt: new Date("2024-11-01T10:30:00Z"),
    updatedAt: new Date("2024-11-15T14:12:00Z"),
  },
  {
    id: "agent-2",
    name: "HTTP Mapper",
    role: "Maps schemas to HTTP bindings",
    instructions: null,
    enabled: false,
    model: {
      provider: "anthropic",
      model: "claude-3-haiku",
      temperature: 0.5,
      maxOutputTokens: null,
    },
    contextTool: null,
    createdAt: new Date("2024-10-12T08:00:00Z"),
    updatedAt: null,
  },
  {
    id: "agent-3",
    name: "Schema Explainer",
    role: "Explains schemas to humans",
    instructions:
      "Use concise language and show examples whenever possible.",
    enabled: true,
    model: null,
    contextTool: {
      toolId: "docs-context",
      mode: "user",
    },
    createdAt: new Date("2024-09-20T09:45:00Z"),
    updatedAt: new Date("2024-10-01T16:20:00Z"),
  },
]);
</script>
