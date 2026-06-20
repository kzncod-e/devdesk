<script setup lang="ts">
import { computed } from 'vue'

definePageMeta({ middleware: 'auth', layout: 'app' })

const route = useRoute()
const taskId = computed(() => Number(route.params.id))
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-8 md:px-8">
    <TaskDetail :task-id="taskId" />
  </div>
</template>
