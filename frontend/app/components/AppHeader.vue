<script setup lang="ts">
const { user, logout } = useAuth()
</script>

<template>
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex max-w-6xl items-center gap-4 px-6 py-3">
      <NuxtLink to="/app" class="text-lg font-bold tracking-tight">DevDesk</NuxtLink>
      <slot />
      <div class="ml-auto flex items-center gap-3 text-sm">
        <span v-if="user" class="text-slate-600">{{ user.name }}</span>
        <button
          class="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100"
          @click="logout()"
        >
          Log out
        </button>
      </div>
    </div>
  </header>
</template>
