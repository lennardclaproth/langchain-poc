<template>
  <select
    class="form-select"
    :class="{ 'is-invalid': invalid }"
    :value="modelValue"
    @change="onChange"
  >
    <option
      v-for="opt in normalizedOptions"
      :key="String(opt.value)"
      :value="opt.value"
    >
      {{ opt.label }}
    </option>

    <!-- allow manual options too -->
    <slot />
  </select>
</template>

<script setup lang="ts">
import { computed } from "vue";

type Option = { label: string; value: string | number | boolean | null | undefined };

const props = defineProps<{
  modelValue: string | number | boolean | null | undefined;
  invalid?: boolean;
  options?: Option[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: string | number | boolean | null): void;
}>();

const normalizedOptions = computed(() => props.options ?? []);

function onChange(e: Event) {
  const el = e.target as HTMLSelectElement;
  const raw = el.value;

  const match = normalizedOptions.value.find((o) => String(o.value) === raw);
  emit("update:modelValue", (match?.value ?? raw) as any);
}
</script>
