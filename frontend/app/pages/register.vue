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
  <div class="grid min-h-screen grid-cols-1 lg:grid-cols-2 bg-canvas text-ink overflow-hidden">
    <!-- Left column: Brand Identity & Aesthetics (Hidden on mobile) -->
    <div class="relative hidden lg:flex flex-col justify-between p-12 bg-surface border-r border-line overflow-hidden select-none">
      <div class="bg-blueprint absolute inset-0 opacity-80" aria-hidden="true" />
      <div class="bg-grid absolute inset-0 opacity-30" aria-hidden="true" />
      <div class="pointer-events-none absolute -left-1/4 -top-1/4 h-[80%] w-[80%] rounded-full bg-accent-soft/40 blur-3xl" aria-hidden="true" />
      
      <!-- Brand Top -->
      <div class="relative z-10 flex items-center gap-2">
        <UiLogo :size="32" show-name />
      </div>

      <!-- Feature highlight / Creative pitch -->
      <div class="relative z-10 space-y-3.5 max-w-md">
        <span class="text-eyebrow">Workspace Creation</span>
        <h2 class="text-title font-medium leading-tight">
          Establish your focus environment.
        </h2>
        <p class="text-sm text-ink-muted leading-relaxed">
          Create an account and start managing your workspace context, tracking tasks, organizing code snippets, and managing developer bookmark references in seconds.
        </p>
      </div>

      <!-- Brand Footer -->
      <div class="relative z-10 flex items-center gap-1.5 text-xs text-ink-subtle">
        <span>DevDesk © 2026</span>
        <span>·</span>
        <span>Handcrafted for productivity</span>
      </div>
    </div>

    <!-- Right column: Forms integrated into the canvas -->
    <div class="relative flex flex-col justify-center items-center p-8 lg:p-16">
      <div class="bg-grid pointer-events-none absolute inset-0 opacity-20 lg:hidden" aria-hidden="true" />
      
      <!-- Mobile brand header -->
      <div class="absolute top-8 left-8 lg:hidden">
        <UiLogo :size="28" show-name />
      </div>

      <div class="enter-rise w-full max-w-[340px] flex flex-col gap-7">
        <div>
          <h1 class="text-title font-semibold tracking-tight text-ink">Get started</h1>
          <p class="mt-1 text-sm text-ink-muted">Create your workspace account.</p>
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="submit">
          <label class="flex flex-col gap-1.5">
            <span class="field-label">Name</span>
            <input
              v-model="name"
              type="text"
              required
              autocomplete="name"
              placeholder="Ada Lovelace"
              class="field-input"
            />
          </label>

          <label class="flex flex-col gap-1.5">
            <span class="field-label">Email address</span>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@domain.com"
              class="field-input"
            />
          </label>
          
          <label class="flex flex-col gap-1.5">
            <span class="field-label">Password</span>
            <input
              v-model="password"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
              placeholder="At least 8 characters"
              class="field-input"
            />
          </label>

          <Transition name="fade">
            <p
              v-if="error"
              role="alert"
              class="flex items-center gap-1.5 text-xs text-danger font-medium"
            >
              <UiIcon name="x" :size="12" /> {{ error }}
            </p>
          </Transition>

          <UiButton
            variant="primary"
            type="submit"
            size="md"
            block
            :loading="busy"
            class="mt-2"
          >
            Create workspace
          </UiButton>
        </form>

        <p class="text-xs text-ink-muted">
          Already have an account?
          <NuxtLink to="/login" class="font-medium text-accent hover:underline">
            Log in
          </NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>
