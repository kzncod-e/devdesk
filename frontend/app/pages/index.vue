<script setup lang="ts">
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 p-8 text-center">
    <h1 class="text-4xl font-bold tracking-tight">DevDesk</h1>
    <p class="text-lg text-slate-600">
      Projects, tasks, snippets and bookmarks — one workspace for daily development.
    </p>
    <div class="flex gap-4">
      <NuxtLink
        to="/login"
        class="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700"
      >
        Log in
      </NuxtLink>
      <NuxtLink
        to="/register"
        class="rounded-lg border border-slate-300 px-5 py-2.5 font-medium hover:bg-slate-100"
      >
        Register
      </NuxtLink>
    </div>
  </main>
</template>
