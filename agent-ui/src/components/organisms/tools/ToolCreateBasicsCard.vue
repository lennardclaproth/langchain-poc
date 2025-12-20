<!-- src/components/organisms/tools/ToolBasicsEndpointCard.vue -->
<template>
  <div class="card">
    <div class="card-body">
      <h5 class="mb-3">Basics</h5>
      <FormField
        label="Name"
      >
        <AppInput
          id="Name"
          v-model.trim="form.name"
          placeholder="e.g. get_post_by_id"
          class="mb-3"
        />
      </FormField>

      <AppTextarea
        v-model.trim="form.description"
        label="Description"
        :rows="3"
        class="mb-3"
      />

      <AppCheckbox
        :id="enabledId"
        v-model="form.enabled"
        class="mb-4">
        Enabled
      </AppCheckbox>

      <AppDivider class="my-4" />

      <h5 class="mb-3">Endpoint</h5>

      <AppSelect
        v-model="form.endpoint.transport"
        label="Transport"
        :options="transportOptions"
        class="mb-3"
      />

      <template v-if="form.endpoint.transport === 'http'">
        <div class="row g-3">
          <div class="col-12 d-flex gap-2 align-items-end">
            <div class="flex-shrink-0">
              <AppSelect
                v-model="form.endpoint.method"
                label="Method"
                :options="httpMethodOptions"
              />
            </div>
            <div class="flex-grow-1">
              <AppInput
                v-model.trim="form.endpoint.url"
                label="URL"
                placeholder="https://example.com/posts/{id}"
              />
            </div>
          </div>
          <div class="col-12">
            <AppTextarea
              v-model="form.headersJson"
              label="Headers (JSON object)"
              :rows="5"
              monospace
              placeholder='{"Accept":"application/json"}'
              :help="headersHelp"
            />
          </div>
        </div>
      </template>
      <template v-if="form.endpoint.transport === 'mcp'">
        <div class="row g-3">
          <div class="col-12">
            <AppInput
              v-model.trim="form.endpoint.mcp_server"
              label="MCP server"
              placeholder="e.g. my-mcp"
            />
          </div>
          <div class="col-12">
            <AppInput
              v-model.trim="form.endpoint.mcp_tool"
              label="MCP tool"
              placeholder="e.g. get_post_by_id"
            />
          </div>
        </div>
      </template>

      <div class="mt-3">
        <FormField
          label="Target (optional)"
          for-id="target"
          info="This is an optional routing hint for the tool dispatcher."
          help="Shown to users configuring the tool."
          class="mb-3"
        >
          <AppInput
            id="target"
            v-model.trim="form.endpoint.target"
            placeholder="optional"
          />
        </FormField>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";

// Atoms (adjust import paths to your project)
import AppCheckbox from "@/components/atoms/Checkbox.vue";
import AppDivider from "@/components/atoms/Divider.vue";
import AppInput from "@/components/atoms/Input.vue";
import AppSelect from "@/components/atoms/Select.vue";
import AppTextarea from "@/components/atoms/Textarea.vue";
import FormField from "@/components/molecules/FormField.vue";

type Transport = "http" | "mcp";
type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "HEAD" | "OPTIONS";

export type ToolCreateEndpointDraft = {
  transport: Transport;
  url: string;
  method: HttpMethod;
  headersJson: string; // kept at form-level, see ToolBasicsEndpointDraft
  mcp_server: string;
  mcp_tool: string;
  target: string;
};

export type ToolCreateBasicsEndpointDraft = {
  name: string;
  description: string;
  enabled: boolean;
  endpoint: {
    transport: Transport;
    url: string;
    method: HttpMethod;
    mcp_server: string;
    mcp_tool: string;
    target: string;
  };
  headersJson: string; // only relevant for http transport
};

const props = withDefaults(
  defineProps<{
    modelValue: ToolCreateBasicsEndpointDraft;
    enabledId?: string;
  }>(),
  {
    enabledId: "enabled",
  }
);

const emit = defineEmits<{
  (e: "update:modelValue", v: ToolCreateBasicsEndpointDraft): void;
}>();

const enabledId = computed(() => props.enabledId);

// Local editable copy (so you can use v-model inside)
const form = reactive<ToolCreateBasicsEndpointDraft>({
  name: props.modelValue.name ?? "",
  description: props.modelValue.description ?? "",
  enabled: props.modelValue.enabled ?? true,
  endpoint: {
    transport: props.modelValue.endpoint?.transport ?? "http",
    url: props.modelValue.endpoint?.url ?? "",
    method: props.modelValue.endpoint?.method ?? "GET",
    mcp_server: props.modelValue.endpoint?.mcp_server ?? "",
    mcp_tool: props.modelValue.endpoint?.mcp_tool ?? "",
    target: props.modelValue.endpoint?.target ?? "",
  },
  headersJson:
    props.modelValue.headersJson ??
    JSON.stringify({ Accept: "application/json" }, null, 2),
});

// Keep local form in sync if parent replaces modelValue (e.g. resetting form)
watch(
  () => props.modelValue,
  (v) => {
    form.name = v.name ?? "";
    form.description = v.description ?? "";
    form.enabled = v.enabled ?? true;
    form.endpoint.transport = v.endpoint?.transport ?? "http";
    form.endpoint.url = v.endpoint?.url ?? "";
    form.endpoint.method = v.endpoint?.method ?? "GET";
    form.endpoint.mcp_server = v.endpoint?.mcp_server ?? "";
    form.endpoint.mcp_tool = v.endpoint?.mcp_tool ?? "";
    form.endpoint.target = v.endpoint?.target ?? "";
    form.headersJson =
      v.headersJson ?? JSON.stringify({ Accept: "application/json" }, null, 2);
  },
  { deep: true }
);

// Emit on any local change
watch(
  form,
  () => {
    emit("update:modelValue", {
      name: form.name,
      description: form.description,
      enabled: form.enabled,
      endpoint: { ...form.endpoint },
      headersJson: form.headersJson,
    });
  },
  { deep: true }
);

// Small UX: if transport switches, clear irrelevant fields (optional but helpful)
watch(
  () => form.endpoint.transport,
  (t) => {
    if (t === "http") {
      form.endpoint.mcp_server = "";
      form.endpoint.mcp_tool = "";
      if (!form.endpoint.method) form.endpoint.method = "GET";
    } else {
      form.endpoint.url = "";
      // keep method; backend will ignore for mcp anyway, but you might want to blank it:
      // form.endpoint.method = "GET";
      form.headersJson = "{}";
    }
  }
);

const transportOptions = [
  { label: "http", value: "http" },
  { label: "mcp", value: "mcp" },
];

const httpMethodOptions = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"].map(
  (m) => ({ label: m, value: m })
);

const headersHelp = "Must be a valid JSON object. Example: {\"Accept\":\"application/json\"}.";
</script>
