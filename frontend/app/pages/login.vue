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
  <div
    class="relative grid min-h-screen place-items-center overflow-hidden bg-canvas px-4 text-ink"
  >
    <div
      class="bg-grid pointer-events-none absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]"
      aria-hidden="true"
    />
    <div
      class="pointer-events-none absolute left-1/2 top-1/3 h-72 w-96 -translate-x-1/2 rounded-full bg-accent-soft blur-3xl"
      aria-hidden="true"
    />

    <div class="enter-rise relative w-full max-w-sm">
      <NuxtLink to="/" class="mb-6 flex justify-center">
        <UiLogo :size="30" show-name />
      </NuxtLink>

      <div class="rounded-card border border-line bg-surface p-7 shadow-card">
        <h1 class="text-xl font-semibold tracking-tight">Welcome back</h1>
        <p class="mt-1 text-sm text-ink-muted">Log in to your workspace.</p>

        <form class="mt-6 flex flex-col gap-4" @submit.prevent="submit">
          <label class="flex flex-col gap-1.5">
            <span class="field-label">Email</span>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@dev.com"
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
              class="flex items-center gap-1.5 text-sm text-danger"
            >
              <UiIcon name="x" :size="14" /> {{ error }}
            </p>
          </Transition>
          <UiButton
            variant="primary"
            type="submit"
            size="lg"
            block
            :loading="busy"
            >Log in</UiButton
          >
        </form>
      </div>

      <p class="mt-5 text-center text-sm text-ink-muted">
        No account?
        <NuxtLink to="/register" class="font-medium text-accent hover:underline"
          >Create one</NuxtLink
        >
      </p>
    </div>
  </div>
</template>
