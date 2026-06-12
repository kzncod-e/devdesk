export interface User {
  id: number
  email: string
  name: string
}

export interface TokenOut {
  access_token: string
  refresh_token: string
  token_type: string
}

export type ProjectStatus = 'active' | 'archived'

export interface Project {
  id: number
  name: string
  description: string
  status: ProjectStatus
  color: string
}

export type TaskStatus = 'todo' | 'in_progress' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface Task {
  id: number
  project_id: number
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  position: number
  due_date: string | null
}

export interface ProjectSummary {
  tasks: { todo: number; in_progress: number; done: number; total: number }
  snippets: number
  bookmarks: number
}
