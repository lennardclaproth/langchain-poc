<template>
  <Card>

      <div class="d-flex align-items-center justify-content-between mb-2">
        <h5 class="mb-0">Contract</h5>
        <span class="text-muted small">Input schema builder</span>
      </div>

      <!-- Top controls -->
      <div class="row g-3 mb-3">
        <div class="col-12 col-md-6">
          <FormField label="Schema version">
            <AppSelect
              v-model="form.contract.schema_version"
              :options="schemaVersionOptions"
            />
          </FormField>
        </div>

        <div class="col-6 col-md-3">
          <FormField label="Read-only">
            <AppSelect
              v-model="form.contract.read_only"
              :options="booleanOptions"
            />
          </FormField>
        </div>

        <div class="col-6 col-md-3">
          <FormField label="Idempotent">
            <AppSelect
              v-model="form.contract.idempotent"
              :options="booleanOptions"
            />
          </FormField>
        </div>
      </div>

      <div class="row g-3 mb-3">
        <div class="col-12 col-md-6">
          <FormField label="Tags (comma-separated)">
            <AppInput
              v-model="form.tagsText"
              placeholder="jsonplaceholder, posts"
            />
          </FormField>
        </div>

        <div class="col-12 col-md-6">
          <FormField label="Cache TTL (seconds)">
            <AppInput
              v-model.number="form.contract.cache_ttl_seconds"
              type="number"
              :min="0"
              placeholder="Only allowed for read-only + idempotent"
              :disabled="!(form.contract.read_only && form.contract.idempotent)"
              :help="!(form.contract.read_only && form.contract.idempotent)
                ? 'Enabled only when read-only=true and idempotent=true.'
                : ''"
            />
          </FormField>
        </div>
      </div>

      <AppDivider class="my-4" />

      <!-- Properties builder header -->
      <div class="d-flex align-items-center justify-content-between mb-2">
        <h6 class="mb-0">Input properties</h6>
        <AppButton
          variant="primary"
          type="button"
          class="rounded-circle"
          @click="addProp"
        >
          <AppIcon name="plus-lg" />
        </AppButton>
      </div>

      <div v-if="form.propsList.length === 0" class="text-muted small border rounded p-3">
        No properties yet. Add one (e.g. <span class="font-monospace">id</span>).
      </div>

      <Card
        v-for="(p, idx) in form.propsList"
        :key="p._key"
        class="mb-3"
      >
        <div class="d-flex align-items-center justify-content-between mb-2">
          <div class="fw-semibold">Property #{{ idx + 1 }}</div>
          <AppButton variant="danger" size="sm" type="button" class="rounded-circle" @click="removeProp(idx)">
            <AppIcon name="trash" />
          </AppButton>
        </div>

        <div class="row g-3">
          <div class="col-12 col-md-4">
            <FormField label="Name">
              <AppInput v-model.trim="p.name" placeholder="id" />
            </FormField>
          </div>

          <div class="col-12 col-md-4">
            <FormField label="Type">
              <AppSelect v-model="p.type" :options="jsonTypeOptions" />
            </FormField>
          </div>

          <div class="col-12 col-md-4">
              <FormField label="Required">
                <AppCheckbox v-model="p.required" :id="`req-${p._key}`" />
              </FormField>
          </div>

          <div class="col-12">
            <FormField label="Description">
              <AppInput v-model.trim="p.description" placeholder="ID of the post to fetch" />
            </FormField>
          </div>

          <div class="col-12 col-md-6">
            <FormField label="Default (JSON)">
              <AppInput
                v-model="p.defaultJson"
                placeholder='null or "abc" or 1'
                monospace
              />
            </FormField>
          </div>

          <div class="col-12 col-md-6">
            <FormField label="Enum (comma-separated)">
              <AppInput v-model="p.enumText" placeholder="optional" />
            </FormField>
          </div>

          <!-- string constraints -->
          <template v-if="p.type === 'string'">
            <div class="col-6 col-md-3">
              <FormField label="minLength">
                <AppInput v-model.number="p.minLength" type="number" :min="0" />
              </FormField>
            </div>
            <div class="col-6 col-md-3">
              <FormField label="maxLength">
                <AppInput v-model.number="p.maxLength" type="number" :min="0" />
              </FormField>
            </div>
          </template>

          <!-- numeric constraints -->
          <template v-if="p.type === 'integer' || p.type === 'number'">
            <div class="col-6 col-md-3">
              <FormField label="minimum">
                <AppInput v-model.number="p.minimum" type="number" />
              </FormField>
            </div>
            <div class="col-6 col-md-3">
              <FormField label="maximum">
                <AppInput v-model.number="p.maximum" type="number" />
              </FormField>
            </div>
          </template>

          <!-- array items -->
          <template v-if="p.type === 'array'">
            <div class="col-12">
              <div class="small text-muted mb-1">Items</div>
              <Card class="bg-light">
                <div class="row g-2">
                  <div class="col-12 col-md-4">
                    <FormField label="Type">
                      <AppSelect
                        v-model="p.items.type"
                        :options="arrayItemTypeOptions"
                        size="sm"
                      />
                    </FormField>
                  </div>
                  <div class="col-12 col-md-8">
                    <FormField label="Description">
                      <AppInput v-model.trim="p.items.description" size="sm" />
                    </FormField>
                  </div>
                </div>
              </Card>
            </div>
          </template>

          <!-- object nested -->
          <template v-if="p.type === 'object'">
            <div class="col-12">
              <div class="d-flex align-items-center justify-content-between mb-1">
                <div class="small text-muted">Nested properties (optional)</div>
                <AppButton variant="secondary" size="sm" type="button" @click="addNestedProp(p)">
                  Add nested
                </AppButton>
              </div>

              <div v-if="p.nested.length === 0" class="small text-muted border rounded p-2">
                No nested properties.
              </div>

              <div
                v-for="(np, nidx) in p.nested"
                :key="np._key"
                class="border rounded p-2 mb-2"
              >
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <div class="small fw-semibold">Nested #{{ nidx + 1 }}</div>
                  <AppButton variant="danger" size="sm" type="button" @click="removeNestedProp(p, nidx)">
                    <AppIcon name="bi-trash" />
                  </AppButton>
                </div>

                <div class="row g-2">
                  <div class="col-12 col-md-4">
                    <FormField label="Name">
                      <AppInput v-model.trim="np.name" size="sm" />
                    </FormField>
                  </div>
                  <div class="col-12 col-md-4">
                    <FormField label="Type">
                      <AppSelect v-model="np.type" :options="nestedTypeOptions" size="sm" />
                    </FormField>
                  </div>
                  <div class="col-12 col-md-4">
                    <div class="mt-4 pt-1">
                      <FormField label="Required">
                        <AppCheckbox v-model="np.required" :id="`nreq-${np._key}`" />
                      </FormField>
                    </div>
                  </div>
                  <div class="col-12">
                    <FormField label="Description">
                      <AppInput v-model.trim="np.description" size="sm" />
                    </FormField>
                  </div>
                </div>
              </div>

              <div class="form-text">
                This is a basic nested editor. You can extend it later to fully recursive objects/arrays.
              </div>
            </div>
          </template>
        </div>
      </Card>

      <div class="small text-muted">
        Required keys:
        <span class="font-monospace">{{ requiredKeys.join(", ") || "—" }}</span>
      </div>

      <AppDivider class="my-4" />

      <h6 class="mb-2">HTTP binding</h6>
      <div class="row g-3">
        <div class="col-12 col-md-6">
          <AppInput
            v-model="form.httpText.path"
            label="Path params (comma-separated)"
            placeholder="id"
            help="Any path param must be marked required."
          />
        </div>
        <div class="col-12 col-md-6">
          <FormField label="Query params">
            <AppInput v-model="form.httpText.query" placeholder="id" />
          </FormField>
        </div>
        <div class="col-12 col-md-6">
          <FormField label="JSON body fields">
            <AppInput v-model="form.httpText.json" placeholder="title, body" />
          </FormField>
        </div>
        <div class="col-12 col-md-6">
          <FormField label="Form fields">
            <AppInput v-model="form.httpText.form" placeholder="file" />
          </FormField>
        </div>
      </div>
    </Card>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";

// Atoms (adjust import paths)
import AppButton from "@/components/atoms/Button.vue";
import AppCheckbox from "@/components/atoms/Checkbox.vue";
import AppDivider from "@/components/atoms/Divider.vue";
import AppIcon from "@/components/atoms/Icon.vue";
import AppInput from "@/components/atoms/Input.vue";
import AppSelect from "@/components/atoms/Select.vue";
import Card from "@/components/atoms/Card.vue";
import FormField from "@/components/molecules/FormField.vue";

type JsonType = "" | "string" | "integer" | "number" | "boolean" | "object" | "array";
type ArrayItemType = "string" | "integer" | "number" | "boolean" | "object";
type NestedType = "string" | "integer" | "number" | "boolean";

export type NestedPropDraft = {
  _key: string;
  name: string;
  type: NestedType;
  description: string;
  required: boolean;
};

export type PropDraft = {
  _key: string;
  name: string;
  type: JsonType;
  description: string;
  required: boolean;
  enumText: string;
  defaultJson: string;
  minLength: number | null;
  maxLength: number | null;
  minimum: number | null;
  maximum: number | null;
  items: { type: ArrayItemType; description: string };
  nested: NestedPropDraft[];
};

export type ToolContractMetaDraft = {
  schema_version: "jsonschema-2020-12" | "jsonschema-draft-07";
  read_only: boolean;
  idempotent: boolean;
  cache_ttl_seconds: number;
};

export type ToolCreateContractBuilderDraft = {
  contract: ToolContractMetaDraft;
  tagsText: string;
  httpText: { query: string; json: string; form: string; path: string };
  propsList: PropDraft[];
};

const props = defineProps<{ modelValue: ToolCreateContractBuilderDraft }>();
const emit = defineEmits<{ (e: "update:modelValue", v: ToolCreateContractBuilderDraft): void }>();

const form = reactive<ToolCreateContractBuilderDraft>({
  contract: {
    schema_version: props.modelValue.contract?.schema_version ?? "jsonschema-2020-12",
    read_only: props.modelValue.contract?.read_only ?? false,
    idempotent: props.modelValue.contract?.idempotent ?? false,
    cache_ttl_seconds: props.modelValue.contract?.cache_ttl_seconds ?? 0,
  },
  tagsText: props.modelValue.tagsText ?? "",
  httpText: props.modelValue.httpText ?? { query: "", json: "", form: "", path: "" },
  propsList: props.modelValue.propsList ?? [],
});

let isSyncingFromProps = false;

watch(
  () => props.modelValue,
  (v) => {
    isSyncingFromProps = true;

    // patch fields (don’t replace the whole reactive object)
    form.contract.schema_version = v.contract?.schema_version ?? "jsonschema-2020-12";
    form.contract.read_only = v.contract?.read_only ?? false;
    form.contract.idempotent = v.contract?.idempotent ?? false;
    form.contract.cache_ttl_seconds = v.contract?.cache_ttl_seconds ?? 0;

    form.tagsText = v.tagsText ?? "";

    // patch object fields
    const http = v.httpText ?? { query: "", json: "", form: "", path: "" };
    form.httpText.query = http.query ?? "";
    form.httpText.json = http.json ?? "";
    form.httpText.form = http.form ?? "";
    form.httpText.path = http.path ?? "";

    // IMPORTANT: mutate the existing array instead of replacing it
    form.propsList.splice(0, form.propsList.length, ...(v.propsList ?? []));

    isSyncingFromProps = false;
  },
  { deep: true, immediate: true }
);

watch(
  form,
  () => {
    if (isSyncingFromProps) return;

    emit("update:modelValue", {
      contract: { ...form.contract },
      tagsText: form.tagsText,
      httpText: { ...form.httpText },
      propsList: form.propsList,
    });
  },
  { deep: true }
);

// TTL rule (also guard it, so it doesn’t bounce)
watch(
  () => [form.contract.read_only, form.contract.idempotent] as const,
  ([ro, idem]) => {
    if (isSyncingFromProps) return;
    if (!(ro && idem)) form.contract.cache_ttl_seconds = 0;
  }
);

function uid() {
  return Math.random().toString(36).slice(2);
}

function addProp() {
  form.propsList.push({
    _key: uid(),
    name: "",
    type: "string",
    description: "",
    required: false,
    enumText: "",
    defaultJson: "null",
    minLength: null,
    maxLength: null,
    minimum: null,
    maximum: null,
    items: { type: "string", description: "" },
    nested: [],
  });
}

function removeProp(idx: number) {
  form.propsList.splice(idx, 1);
}

function addNestedProp(parent: PropDraft) {
  parent.nested.push({
    _key: uid(),
    name: "",
    type: "string",
    description: "",
    required: false,
  });
}

function removeNestedProp(parent: PropDraft, idx: number) {
  parent.nested.splice(idx, 1);
}

const requiredKeys = computed(() =>
  form.propsList
    .filter((p) => p.required && p.name.trim())
    .map((p) => p.name.trim())
);

const schemaVersionOptions = [
  { label: "jsonschema-2020-12", value: "jsonschema-2020-12" },
  { label: "jsonschema-draft-07", value: "jsonschema-draft-07" },
];

const booleanOptions = [
  { label: "true", value: true },
  { label: "false", value: false },
];

const jsonTypeOptions = [
  { label: "(auto)", value: "" },
  { label: "string", value: "string" },
  { label: "integer", value: "integer" },
  { label: "number", value: "number" },
  { label: "boolean", value: "boolean" },
  { label: "object", value: "object" },
  { label: "array", value: "array" },
];

const arrayItemTypeOptions = ["string", "integer", "number", "boolean", "object"].map((v) => ({ label: v, value: v }));
const nestedTypeOptions = ["string", "integer", "number", "boolean"].map((v) => ({ label: v, value: v }));
</script>
