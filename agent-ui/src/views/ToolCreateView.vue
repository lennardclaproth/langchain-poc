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
        <ToolCreateBasicsCard v-model="basics" enabled-id="enabled-create-tool" />
        <ToolCreateContractsCard v-model="contractDraft" />
        <ToolCreateResponseCard v-model="responseDraft" />

            <!-- <div class="mb-0">
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
        </div> -->
      </div>
      </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
// import ToolCreateBasicsCard from "@/components/organisms/tools/ToolCreateBasicsCard.vue";
import ToolCreateBasicsCard, { type ToolCreateBasicsEndpointDraft } from "@/components/organisms/tools/ToolCreateBasicsCard.vue";
import ToolCreateContractsCard, {type ToolCreateContractBuilderDraft} from "@/components/organisms/tools/ToolCreateContractsCard.vue";
import ToolCreateResponseCard, { type ToolCreateResponseDraft } from "@/components/organisms/tools/ToolCreateResponseCard.vue";
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
