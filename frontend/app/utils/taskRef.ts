/**
 * Human task identifier: the project key + the task's per-project number,
 * e.g. "ACME-12" (Linear-style). Falls back to the global id when either piece
 * is missing (older rows / loading), so it never renders blank.
 */
export function taskRef(
  key: string | null | undefined,
  number: number | null | undefined,
  fallbackId: number,
): string {
  return `${key || 'TASK'}-${number ?? fallbackId}`
}
