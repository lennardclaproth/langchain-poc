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

<script setup>
import { computed } from "vue";

const props = defineProps({
  as: {
    type: String,
    default: "button", // button | a | RouterLink (passed in)
  },
  type: {
    type: String,
    default: "button", // button | submit | reset
  },
  variant: {
    type: String,
    default: "primary",
    // primary | secondary | outline | danger | ghost
  },
  size: {
    type: String,
    default: "md", // sm | md | lg
  },
  block: {
    type: Boolean,
    default: false, // full width
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["click"]);

function onClick(event) {
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

function variantClass(v) {
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

function sizeClass(s) {
  if (s === "sm") return "btn-sm";
  if (s === "lg") return "btn-lg";
  return null;
}
</script>
