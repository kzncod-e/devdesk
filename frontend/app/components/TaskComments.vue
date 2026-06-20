<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import type { Comment, UserBrief } from '~/types/api'

const props = defineProps<{ taskId: number; users?: UserBrief[] }>()

const { api, user } = useAuth()
const queryClient = useQueryClient()
const { success, error } = useToast()
const { confirm } = useConfirm()

const key = computed(() => ['comments', 'task', props.taskId])

const { data: comments, isPending } = useQuery({
  queryKey: key,
  queryFn: () =>
    api<Comment[]>(`/api/v1/comments?entity_type=task&entity_id=${props.taskId}`),
  enabled: computed(() => !isNaN(props.taskId)),
})

// ── Composer + @mention autocomplete ─────────────────────────────────────────
const draft = ref('')
const taRef = ref<HTMLTextAreaElement | null>(null)
const mention = ref<{ active: boolean; query: string; from: number }>({
  active: false,
  query: '',
  from: 0,
})

function onInput(e: Event) {
  const ta = e.target as HTMLTextAreaElement
  draft.value = ta.value
  const caret = ta.selectionStart ?? ta.value.length
  const m = ta.value.slice(0, caret).match(/@([^\s@]*)$/)
  mention.value = m
    ? { active: true, query: m[1] ?? '', from: caret - m[0].length }
    : { active: false, query: '', from: 0 }
}

const mentionMatches = computed(() => {
  if (!mention.value.active) return []
  const q = mention.value.query.toLowerCase()
  return (props.users ?? []).filter((u) => u.name.toLowerCase().includes(q)).slice(0, 6)
})

function pickMention(u: UserBrief) {
  const ta = taRef.value
  const caret = ta?.selectionStart ?? draft.value.length
  draft.value = `${draft.value.slice(0, mention.value.from)}@${u.name} ${draft.value.slice(caret)}`
  mention.value = { active: false, query: '', from: 0 }
  nextTick(() => taRef.value?.focus())
}

function mentionIdsIn(text: string): number[] {
  return (props.users ?? []).filter((u) => text.includes(`@${u.name}`)).map((u) => u.id)
}

const createMut = useMutation({
  mutationFn: (body: string) =>
    api<Comment>('/api/v1/comments', {
      method: 'POST',
      body: {
        entity_type: 'task',
        entity_id: props.taskId,
        body,
        mention_ids: mentionIdsIn(body),
      },
    }),
  onSuccess: () => {
    draft.value = ''
    queryClient.invalidateQueries({ queryKey: key.value })
  },
  onError: () => error('Could not post comment'),
})

function submit() {
  const body = draft.value.trim()
  if (!body || createMut.isPending.value) return
  createMut.mutate(body)
}

// Cmd/Ctrl+Enter to send.
function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault()
    submit()
  }
}

// ── Edit / delete ─────────────────────────────────────────────────────────────
const editingId = ref<number | null>(null)
const editDraft = ref('')

function startEdit(c: Comment) {
  editingId.value = c.id
  editDraft.value = c.body
}

const editMut = useMutation({
  mutationFn: (vars: { id: number; body: string }) =>
    api<Comment>(`/api/v1/comments/${vars.id}`, { method: 'PATCH', body: { body: vars.body } }),
  onSuccess: () => {
    editingId.value = null
    queryClient.invalidateQueries({ queryKey: key.value })
  },
  onError: () => error('Could not save edit'),
})

function saveEdit() {
  const body = editDraft.value.trim()
  if (!body || editingId.value == null) return
  editMut.mutate({ id: editingId.value, body })
}

async function remove(c: Comment) {
  const ok = await confirm({
    title: 'Delete comment?',
    message: 'This cannot be undone.',
    confirmLabel: 'Delete',
    danger: true,
  })
  if (!ok) return
  try {
    await api(`/api/v1/comments/${c.id}`, { method: 'DELETE' })
    queryClient.invalidateQueries({ queryKey: key.value })
    success('Comment deleted')
  } catch {
    error('Could not delete comment')
  }
}

// ── Rendering helpers ─────────────────────────────────────────────────────────
function timeAgo(iso: string): string {
  const s = Math.max(1, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

// Split a body into plain / @mention segments so mentions render highlighted (no v-html).
function segments(body: string): { t: string; mention: boolean }[] {
  const names = (props.users ?? []).map((u) => u.name).sort((a, b) => b.length - a.length)
  const out: { t: string; mention: boolean }[] = []
  let i = 0
  while (i < body.length) {
    if (body[i] === '@') {
      const rest = body.slice(i + 1)
      const hit = names.find((n) => n && rest.startsWith(n))
      if (hit) {
        out.push({ t: `@${hit}`, mention: true })
        i += 1 + hit.length
        continue
      }
    }
    const last = out[out.length - 1]
    if (last && !last.mention) last.t += body[i]
    else out.push({ t: body[i]!, mention: false })
    i++
  }
  return out
}
</script>

<template>
  <section class="space-y-4">
    <h2 class="text-heading">
      Comments
      <span v-if="comments?.length" class="ml-1 text-sm font-normal text-ink-subtle tabular">
        {{ comments.length }}
      </span>
    </h2>

    <!-- Composer -->
    <div class="relative">
      <div class="flex gap-3">
        <UiAvatar v-if="user" :user="user" :size="28" class="mt-0.5 shrink-0" />
        <div class="min-w-0 flex-1">
          <div class="relative">
            <textarea
              ref="taRef"
              :value="draft"
              rows="3"
              placeholder="Leave a comment… use @ to mention"
              class="field-input resize-none"
              @input="onInput"
              @keydown="onKeydown"
            />
            <!-- @mention dropdown -->
            <ul
              v-if="mentionMatches.length"
              class="absolute z-20 mt-1 w-60 overflow-hidden rounded-card border border-line bg-surface p-1 shadow-pop"
            >
              <li v-for="u in mentionMatches" :key="u.id">
                <button
                  type="button"
                  class="flex w-full items-center gap-2 rounded-control px-2 py-1.5 text-left text-sm hover:bg-surface-2"
                  @click="pickMention(u)"
                >
                  <UiAvatar :user="u" :size="18" />
                  <span class="truncate text-ink">{{ u.name }}</span>
                </button>
              </li>
            </ul>
          </div>
          <div class="mt-2 flex items-center justify-between">
            <span class="text-meta">Cmd/Ctrl + Enter to send</span>
            <UiButton
              variant="primary"
              size="sm"
              :loading="createMut.isPending.value"
              :disabled="!draft.trim()"
              @click="submit"
            >
              Comment
            </UiButton>
          </div>
        </div>
      </div>
    </div>

    <!-- List -->
    <div v-if="isPending" class="space-y-3">
      <div v-for="i in 2" :key="i" class="flex gap-3">
        <UiSkeleton class="size-7 shrink-0 rounded-full" />
        <div class="flex-1 space-y-2">
          <UiSkeleton class="h-3 w-32" />
          <UiSkeleton class="h-3 w-full" />
        </div>
      </div>
    </div>

    <p v-else-if="!comments?.length" class="py-6 text-center text-sm text-ink-subtle">
      No comments yet. Start the conversation.
    </p>

    <ul v-else class="space-y-4">
      <li v-for="c in comments" :key="c.id" class="group flex gap-3">
        <UiAvatar :user="c.author ?? { id: 0, name: '?', avatar_url: null }" :size="28" class="mt-0.5 shrink-0" />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-ink">{{ c.author?.name ?? 'Unknown' }}</span>
            <span class="text-meta">{{ timeAgo(c.created_at) }}</span>
            <span v-if="c.edited_at" class="text-meta">· edited</span>

            <div
              v-if="c.author?.id === user?.id && editingId !== c.id"
              class="ml-auto flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100"
            >
              <button type="button" class="icon-btn" aria-label="Edit comment" @click="startEdit(c)">
                <UiIcon name="edit" :size="14" />
              </button>
              <button type="button" class="icon-btn icon-btn-danger" aria-label="Delete comment" @click="remove(c)">
                <UiIcon name="trash" :size="14" />
              </button>
            </div>
          </div>

          <!-- Edit mode -->
          <div v-if="editingId === c.id" class="mt-1.5">
            <textarea v-model="editDraft" rows="3" class="field-input resize-none" />
            <div class="mt-2 flex gap-2">
              <UiButton variant="primary" size="sm" :loading="editMut.isPending.value" :disabled="!editDraft.trim()" @click="saveEdit">
                Save
              </UiButton>
              <UiButton variant="ghost" size="sm" @click="editingId = null">Cancel</UiButton>
            </div>
          </div>

          <!-- Body with highlighted @mentions -->
          <p v-else class="mt-0.5 whitespace-pre-wrap break-words text-sm leading-relaxed text-ink-muted">
            <template v-for="(seg, idx) in segments(c.body)" :key="idx"><span
              v-if="seg.mention"
              class="rounded bg-surface-3 px-1 font-medium text-ink"
            >{{ seg.t }}</span><template v-else>{{ seg.t }}</template></template>
          </p>
        </div>
      </li>
    </ul>
  </section>
</template>
