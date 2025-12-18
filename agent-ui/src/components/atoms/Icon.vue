<template>
  <i :class="`bi bi-${name}`" aria-hidden="true" />
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true,
  },
});
</script>
