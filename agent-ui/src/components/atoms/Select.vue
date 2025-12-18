<template>
  <select
    class="form-select"
    :class="{ 'is-invalid': invalid }"
    :value="modelValue"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <slot />
  </select>
</template>

<script setup>
defineProps({
  modelValue: [String, Number, Boolean],
  invalid: Boolean,
});

defineEmits(["update:modelValue"]);
</script>
