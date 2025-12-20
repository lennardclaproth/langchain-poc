<!-- src/components/atoms/Textarea.vue -->
<template>
  <textarea
    class="form-control"
    :rows="rows"
    :class="{
      'is-invalid': invalid,
      'font-monospace': monospace,
    }"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string;
    rows?: number;
    placeholder?: string;
    invalid?: boolean;
    disabled?: boolean;
    monospace?: boolean;
  }>(),
  {
    rows: 3,
    invalid: false,
    disabled: false,
    monospace: false,
    placeholder: undefined,
  }
);

defineEmits<{
  (e: "update:modelValue", v: string): void;
}>();
</script>
