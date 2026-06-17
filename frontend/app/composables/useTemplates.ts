import type {
  Template,
  TemplateDetail,
  TemplateKind,
  TemplateVisibility,
  UseTemplateResult,
} from '~/types/api'

export interface CaptureInput {
  kind: TemplateKind
  source_id: number
  name: string
  description?: string
  visibility?: TemplateVisibility
}

/** Thin wrapper over the /templates API. Pages own their own useQuery/useMutation. */
export function useTemplates() {
  const { api } = useAuth()

  const list = (kind?: TemplateKind) =>
    api<Template[]>(`/api/v1/templates${kind ? `?kind=${kind}` : ''}`)

  const get = (id: number) => api<TemplateDetail>(`/api/v1/templates/${id}`)

  const capture = (body: CaptureInput) =>
    api<TemplateDetail>('/api/v1/templates/capture', { method: 'POST', body })

  const use = (id: number) =>
    api<UseTemplateResult>(`/api/v1/templates/${id}/use`, { method: 'POST' })

  const remove = (id: number) =>
    api(`/api/v1/templates/${id}`, { method: 'DELETE' })

  return { list, get, capture, use, remove }
}

/** Path to the entity created by `use`, for post-use navigation. */
export function useTemplateResultPath(r: UseTemplateResult): string {
  if (r.kind === 'project' && r.project_id) return `/app/projects/${r.project_id}`
  return '/app/snippets'
}
