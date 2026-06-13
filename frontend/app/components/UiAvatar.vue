<script setup lang="ts">
import { computed } from 'vue'

import type { UserBrief } from '~/types/api'

const props = withDefaults(defineProps<{ user: UserBrief; size?: number }>(), {
  size: 24,
})

const initials = computed(() =>
  (props.user.name || '?')
    .split(' ')
    .map(p => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase(),
)

const dim = computed(() => `${props.size}px`)
const fontSize = computed(() => `${Math.round(props.size * 0.42)}px`)
</script>

<template>
  <span
    class="inline-grid shrink-0 place-items-center overflow-hidden rounded-full bg-accent-soft font-semibold text-accent ring-2 ring-surface"
    :style="{ width: dim, height: dim, fontSize }"
    :title="user.name"
  >
    <img
      v-if="user.avatar_url"
      :src="user.avatar_url"
      :alt="user.name"
      class="size-full object-cover"
    >
    <template v-else>{{ initials }}</template>
  </span>
</template>
