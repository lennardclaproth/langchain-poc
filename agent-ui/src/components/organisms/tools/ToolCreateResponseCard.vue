<!-- src/components/organisms/tools/ToolResponseCard.vue -->
<template>
  <Card>
      <h5 class="mb-3">Response</h5>

      <AppSelect
        v-model="form.format"
        label="Format"
        :options="formatOptions"
        class="mb-3"
      />

      <AppTextarea
        v-model="form.schemaJson"
        label="Schema (JSON)"
        :rows="6"
        monospace
        placeholder='{"type":"object","properties":{...}}'
        help="Optional, but useful for validation and UI."
      />
  </Card>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

// Atoms (adjust import paths)
import AppSelect from "@/components/atoms/Select.vue";
import AppTextarea from "@/components/atoms/Textarea.vue";
import Card from "@/components/atoms/Card.vue";

export type ToolCreateResponseDraft = {
  format: "json" | "text";
  schemaJson: string;
};

const props = defineProps<{ modelValue: ToolCreateResponseDraft }>();
const emit = defineEmits<{ (e: "update:modelValue", v: ToolCreateResponseDraft): void }>();

const form = reactive<ToolCreateResponseDraft>({
  format: props.modelValue.format ?? "text",
  schemaJson: props.modelValue.schemaJson ?? JSON.stringify({}, null, 2),
});

// Sync if parent replaces model (reset/load existing)
watch(
  () => props.modelValue,
  (v) => {
    form.format = v.format ?? "text";
    form.schemaJson = v.schemaJson ?? JSON.stringify({}, null, 2);
  },
  { deep: true }
);

// Emit on local change
watch(
  form,
  () => {
    emit("update:modelValue", { format: form.format, schemaJson: form.schemaJson });
  },
  { deep: true }
);

const formatOptions = [
  { label: "json", value: "json" },
  { label: "text", value: "text" },
];
</script>
