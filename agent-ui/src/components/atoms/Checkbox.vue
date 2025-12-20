<!-- src/components/atoms/Checkbox.vue -->
<template>
  <div class="form-check">
    <input
      class="form-check-input"
      type="checkbox"
      :id="id"
      :checked="modelValue"
      :disabled="disabled"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <label class="form-check-label" :for="id">
      <slot />
    </label>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: boolean;
    id?: string;
    disabled?: boolean;
  }>(),
  {
    id: undefined,
    disabled: false,
  }
);

defineEmits<{
  (e: "update:modelValue", v: boolean): void;
}>();
</script>
