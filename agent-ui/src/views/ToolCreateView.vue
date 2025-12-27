<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h2 class="mb-0">Create tool</h2>
        <div class="text-muted">Define a new tool</div>
      </div>

      <Button
            :as="RouterLink"
            v-bind="{ to: '/tools' }"
            variant="ghost"
            class="d-flex align-items-center gap-2"
          >
            <Icon name="arrow-left" />
            <span>back</span>
          </Button>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="row g-4">
        <ToolCreateBasicsCard v-model="basics" enabled-id="enabled-create-tool" />
        <ToolCreateContractsCard v-model="contractDraft" />
        <ToolCreateResponseCard v-model="responseDraft" />
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ToolCreateBasicsCard, { type ToolCreateBasicsEndpointDraft } from "@/components/organisms/tools/ToolCreateBasicsCard.vue";
import ToolCreateContractsCard, {type ToolCreateContractBuilderDraft} from "@/components/organisms/tools/ToolCreateContractsCard.vue";
import ToolCreateResponseCard, { type ToolCreateResponseDraft } from "@/components/organisms/tools/ToolCreateResponseCard.vue";
import Button from "@/components/atoms/Button.vue";
import Icon from "@/components/atoms/Icon.vue";
import { RouterLink } from "vue-router";
const error = ref("");

const basics = ref<ToolCreateBasicsEndpointDraft>({
  name: "",
  description: "",
  enabled: true,
  endpoint: {
    transport: "http",
    url: "https://example.com/",
    method: "GET",
    mcp_server: "",
    mcp_tool: "",
    target: "",
  },
  headersJson: JSON.stringify({ Accept: "application/json" }, null, 2),
});

const contractDraft = ref<ToolCreateContractBuilderDraft>({
  contract: {
    schema_version: "jsonschema-2020-12",
    read_only: false,
    idempotent: false,
    cache_ttl_seconds: 0,
  },
  tagsText: "",
  httpText: { query: "", json: "", form: "", path: "" },
  propsList: [],
});

const responseDraft = ref<ToolCreateResponseDraft>({
  format: "text",
  schemaJson: JSON.stringify({}, null, 2),
});

</script>
