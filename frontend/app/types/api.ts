export interface User {
  id: number
  email: string
  name: string
  role: string
}

export interface TokenOut {
  access_token: string
  refresh_token: string
  token_type: string
}

export type WorkspaceRole = 'owner' | 'admin' | 'editor' | 'member' | 'viewer'

export interface Workspace {
  id: number
  name: string
  slug: string
  plan: string
  role: WorkspaceRole
}

export interface Member {
  user_id: number
  name: string
  email: string
  avatar_url: string | null
  role: WorkspaceRole
  status: string
}

export interface Invite {
  id: number
  email: string
  role: WorkspaceRole
  expires_at: string
  accepted_at: string | null
  token?: string
}

export type ProjectStatus = 'active' | 'archived'

export interface Project {
  id: number
  workspace_id: number
  name: string
  key: string | null
  description: string
  status: ProjectStatus
  color: string
  image_url: string | null
}

export type TaskStatus = 'todo' | 'in_progress' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface UserBrief {
  id: number
  name: string
  avatar_url: string | null
}

export interface Comment {
  id: number
  entity_type: string
  entity_id: number
  author: UserBrief | null
  body: string
  parent_id: number | null
  created_at: string
  edited_at: string | null
}

export interface Task {
  id: number
  project_id: number
  workspace_id: number
  number: number | null
  parent_task_id: number | null
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  position: number
  due_date: string | null
  assignees: UserBrief[]
  // Phases 2–3: populated once comments/attachments ship; cards render chips when > 0.
  comment_count?: number
  attachment_count?: number
}

export interface ProjectSummary {
  tasks: { todo: number; in_progress: number; done: number; total: number }
  snippets: number
  bookmarks: number
}

export interface Snippet {
  id: number
  project_id: number | null
  collection_id: number | null
  title: string
  language: string
  code: string
  tags: string[]
  notes: string
}

export interface Bookmark {
  id: number
  project_id: number | null
  collection_id: number | null
  url: string
  title: string
  description: string
  tags: string[]
  favicon: string
  fetched_meta: Record<string, string>
}

export interface Activity {
  id: number
  workspace_id: number
  actor_id: number | null
  actor_name: string | null
  verb: string
  entity_type: string
  entity_id: number | null
  entity_name: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface AuditLog {
  id: number
  workspace_id: number
  actor_id: number | null
  actor_name: string | null
  action: string
  target_type: string | null
  target_id: number | null
  after_state: Record<string, unknown>
  created_at: string
}

export interface ActivityPage {
  items: Activity[]
  next_cursor: number | null
}

export interface AuditPage {
  items: AuditLog[]
  next_cursor: number | null
}

export type NotificationType = 'task.assigned' | 'workspace.invite' | 'member.role_changed'

export interface Notification {
  id: number
  workspace_id: number
  type: NotificationType
  payload: Record<string, unknown>
  read_at: string | null
  created_at: string
}

export interface NotificationPage {
  items: Notification[]
  next_cursor: number | null
}

export type TemplateKind = 'project' | 'snippet'
export type TemplateVisibility = 'workspace' | 'public'

export interface Template {
  id: number
  workspace_id: number | null
  kind: TemplateKind
  name: string
  description: string
  visibility: TemplateVisibility
  created_by: number | null
  use_count: number
  created_at: string
}

export interface TemplateDetail extends Template {
  payload: Record<string, unknown>
}

export interface UseTemplateResult {
  kind: TemplateKind
  project_id?: number | null
  snippet_id?: number | null
}

export type CollectionKind = 'snippet' | 'bookmark'

export interface Collection {
  id: number
  workspace_id: number
  name: string
  kind: CollectionKind
  parent_id: number | null
}

export interface Tag {
  id: number
  name: string
  color: string
}

export type SavedFilterKind = 'snippet' | 'bookmark' | 'task' | 'project'

export interface SavedFilter {
  id: number
  name: string
  kind: SavedFilterKind
  query: Record<string, unknown>
  created_at: string
}
