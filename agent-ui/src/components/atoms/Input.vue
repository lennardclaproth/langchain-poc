<template>
  <input
    :type="type"
    class="form-control"
    :class="{ 'is-invalid': invalid }"
    :placeholder="placeholder"
    :value="modelValue"
    :disabled="disabled"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
defineProps({
  modelValue: String,
  type: {
    type: String,
    default: "text",
  },
  placeholder: String,
  disabled: Boolean,
  invalid: Boolean,
});

defineEmits(["update:modelValue"]);
</script>
