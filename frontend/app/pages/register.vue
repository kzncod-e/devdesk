<script setup lang="ts">
const { register } = useAuth()
const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await register(name.value, email.value, password.value)
    await navigateTo('/app')
  } catch (err: unknown) {
    const status = (err as { status?: number })?.status
    if (status === 409) error.value = 'That email is already registered.'
    else if (status === 422) error.value = 'Password must be at least 8 characters.'
    else error.value = 'Registration failed. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-sm flex-col justify-center p-8">
    <h1 class="mb-6 text-2xl font-bold">Register</h1>
    <form class="flex flex-col gap-4" @submit.prevent="submit">
      <label class="flex flex-col gap-1 text-sm font-medium">
        Name
        <input
          v-model="name"
          type="text"
          required
          autocomplete="name"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
      <label class="flex flex-col gap-1 text-sm font-medium">
        Email
        <input
          v-model="email"
          type="email"
          required
          autocomplete="email"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
      <label class="flex flex-col gap-1 text-sm font-medium">
        Password
        <input
          v-model="password"
          type="password"
          required
          minlength="8"
          autocomplete="new-password"
          class="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        >
      </label>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="busy"
        class="rounded-lg bg-indigo-600 px-4 py-2.5 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ busy ? 'Creating account…' : 'Create account' }}
      </button>
    </form>
    <p class="mt-4 text-sm text-slate-600">
      Already have an account?
      <NuxtLink to="/login" class="font-medium text-indigo-600 hover:underline">Log in</NuxtLink>
    </p>
  </main>
</template>
