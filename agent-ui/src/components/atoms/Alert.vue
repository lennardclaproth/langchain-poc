<!-- src/components/atoms/Alert.vue -->
<template>
  <div class="alert" :class="`alert-${variant}`" role="alert">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "success" | "danger" | "warning" | "info" | "light" | "dark";
  }>(),
  {
    variant: "danger",
  }
);
</script>
