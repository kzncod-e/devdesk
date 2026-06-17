<script setup lang="ts">
const { login } = useAuth();
const email = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);

async function submit() {
  error.value = "";
  busy.value = true;
  try {
    await login(email.value, password.value);
    await navigateTo("/app");
  } catch (err: unknown) {
    const status = (err as { status?: number })?.status;
    error.value =
      status === 401
        ? "Invalid email or password."
        : "Login failed. Try again.";
  } finally {
    busy.value = false;
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
        <span class="text-eyebrow">Developer Workspace</span>
        <h2 class="text-title font-medium leading-tight">
          Handcrafted workspace built for engineering focus.
        </h2>
        <p class="text-sm text-ink-muted leading-relaxed">
          Manage your kanban boards, code snippets, project bookmarks, and reusable template systems from a single, keyboard-first environment.
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
          <h1 class="text-title font-semibold tracking-tight text-ink">Welcome back</h1>
          <p class="mt-1 text-sm text-ink-muted">Sign in to your team workspace.</p>
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="submit">
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
              autocomplete="current-password"
              placeholder="••••••••"
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
            Continue
          </UiButton>
        </form>

        <p class="text-xs text-ink-muted">
          New to DevDesk?
          <NuxtLink to="/register" class="font-medium text-accent hover:underline">
            Create an account
          </NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>
