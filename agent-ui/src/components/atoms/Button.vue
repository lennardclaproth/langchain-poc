<!-- src/components/atoms/Button.vue -->
<template>
  <component
    :is="as"
    :type="as === 'button' ? type : undefined"
    :disabled="disabled"
    class="btn"
    :class="computedClasses"
    @click="onClick"
  >
    <slot name="icon-left" />
    <slot />
    <slot name="icon-right" />
  </component>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    as?: any; // 'button' | 'a' | RouterLink component
    type?: "button" | "submit" | "reset";
    variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
    size?: "sm" | "md" | "lg";
    block?: boolean;
    disabled?: boolean;
  }>(),
  {
    as: "button",
    type: "button",
    variant: "primary",
    size: "md",
    block: false,
    disabled: false,
  }
);

const emit = defineEmits<{
  (e: "click", event: MouseEvent): void;
}>();

function onClick(event: MouseEvent) {
  if (props.disabled) {
    event.preventDefault();
    return;
  }
  emit("click", event);
}

const computedClasses = computed(() => [
  variantClass(props.variant),
  sizeClass(props.size),
  {
    "w-100": props.block,
    disabled: props.disabled,
  },
]);

function variantClass(v: typeof props.variant) {
  switch (v) {
    case "secondary":
      return "btn-secondary";
    case "outline":
      return "btn-outline-secondary";
    case "danger":
      return "btn-danger";
    case "ghost":
      return "btn-link text-decoration-none";
    default:
      return "btn-primary";
  }
}

function sizeClass(s: typeof props.size) {
  if (s === "sm") return "btn-sm";
  if (s === "lg") return "btn-lg";
  return null;
}
</script>
