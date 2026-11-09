<script setup lang="ts">
const config = useRuntimeConfig()
const { data, error } = await useFetch<{ name: string; version: string }>(
  `$${config.public.apiBase}/system/info`
)
</script>

<template>
  <UContainer class="py-10">
    <UCard>
      <template #header>
        <h1 class="text-2xl font-semibold">${PROJECT_NAME}</h1>
      </template>
      <UAlert v-if="error" color="error" title="Backend unavailable" :description="error.message" />
      <dl v-else class="grid grid-cols-2 gap-3">
        <dt>Name</dt><dd>{{ data?.name }}</dd>
        <dt>Version</dt><dd>{{ data?.version }}</dd>
      </dl>
    </UCard>
  </UContainer>
</template>

