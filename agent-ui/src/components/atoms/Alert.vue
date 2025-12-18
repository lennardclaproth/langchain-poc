<template>
  <div class="alert" :class="`alert-${variant}`">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: "danger",
  },
});
</script>
