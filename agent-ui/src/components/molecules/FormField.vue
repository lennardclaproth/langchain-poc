<!-- src/components/molecules/FormField.vue -->
<script lang="ts">
/**
 * FormField
 *
 * Molecule that wraps a form control with:
 * - label
 * - optional info tooltip
 * - optional help text
 *
 * Use it to keep form layouts consistent across the app.
 */
export default {
  name: "FormField",
};
</script>

<template>
  <div :class="wrapperClass">
    <div class="d-flex align-items-center gap-2 mb-1">
      <label v-if="label" class="form-label mb-0" :for="forId">
        {{ label }}
      </label>

      <!-- Info tooltip (optional) -->
      <span v-if="info" class="d-inline-flex align-items-center">
        <span
          class="text-muted"
          role="button"
          tabindex="0"
          :aria-label="`Info: ${label ?? ''}`"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="info"
          ref="infoEl"
        >
          <slot name="info-icon">
            <i class="bi bi-info-circle"></i>
          </slot>
        </span>
      </span>
    </div>

    <!-- Control slot -->
    <slot />

    <!-- Validation messages -->
    <div v-if="error" class="invalid-feedback d-block">
      {{ error }}
    </div>
    <div v-else-if="success" class="valid-feedback d-block">
      {{ success }}
    </div>

    <!-- Optional help text (non-validation) -->
    <div v-if="help" class="form-text">
      {{ help }}
    </div>
  </div>
</template>

<script setup lang="ts">
    
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps<{
    /**
     * Label shown above the form control.
     */
  label?: string;
  forId?: string;           // pass your input/select/textarea id
  info?: string;            // tooltip text
  help?: string;            // helper text under field
  error?: string;           // show invalid state + message
  success?: string;         // show valid state + message
  class?: string;
}>();

const wrapperClass = computed(() => props.class);

const infoEl = ref<HTMLElement | null>(null);

let tooltipInstance: any = null;

onMounted(async () => {
  if (!props.info || !infoEl.value) return;

  // Bootstrap tooltip requires JS initialization.
  // We try to use global bootstrap if present; otherwise do nothing gracefully.
  const w = window as any;
  const Bootstrap = w.bootstrap;

  if (Bootstrap?.Tooltip) {
    tooltipInstance = new Bootstrap.Tooltip(infoEl.value);
  }
});

onBeforeUnmount(() => {
  if (tooltipInstance?.dispose) tooltipInstance.dispose();
  tooltipInstance = null;
});
</script>
