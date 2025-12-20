<!-- src/components/atoms/Input.vue -->
<template>
  <input
    :id="id"
    :type="type"
    class="form-control"
    :class="{
      'is-invalid': invalid,
      'font-monospace': monospace,
    }"
    :placeholder="placeholder"
    :value="modelValue"
    :disabled="disabled"
    :min="min"
    :max="max"
    :step="step"
    @input="onInput"
  />
</template>

<script setup lang="ts">
type InputType =
  | "text"
  | "email"
  | "password"
  | "search"
  | "url"
  | "tel"
  | "number"
  | "date"
  | "datetime-local"
  | "time";

const props = withDefaults(
  defineProps<{
    id?: string;
    modelValue: string | number | null | undefined;
    type?: InputType;
    placeholder?: string;
    disabled?: boolean;
    invalid?: boolean;
    monospace?: boolean;

    // useful for number inputs
    min?: number | string;
    max?: number | string;
    step?: number | string;
  }>(),
  {
    id: undefined,
    type: "text",
    disabled: false,
    invalid: false,
    monospace: false,
    placeholder: undefined,
    min: undefined,
    max: undefined,
    step: undefined,
  }
);

const emit = defineEmits<{
  (e: "update:modelValue", v: string | number | null): void;
}>();

function onInput(e: Event) {
  const el = e.target as HTMLInputElement;

  // Preserve numeric typing when using type="number"
  if (props.type === "number") {
    const raw = el.value;
    if (raw === "") {
      emit("update:modelValue", null);
      return;
    }
    const n = Number(raw);
    emit("update:modelValue", Number.isNaN(n) ? null : n);
    return;
  }

  emit("update:modelValue", el.value);
}
</script>
