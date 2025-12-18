<template>
  <textarea
    class="form-control"
    :rows="rows"
    :class="{ 'is-invalid': invalid }"
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', $event.target.value)"
    />
</template>

<script setup>
defineProps({
  modelValue: String,
  rows: {
    type: Number,
    default: 3,
  },
  placeholder: String,
  invalid: Boolean,
});

defineEmits(["update:modelValue"]);
</script>
