<template>
  <div class="form-check">
    <input
      class="form-check-input"
      type="checkbox"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <label class="form-check-label">
      <slot />
    </label>
  </div>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
});

defineEmits(["update:modelValue"]);
</script>
