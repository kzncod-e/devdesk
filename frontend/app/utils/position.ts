export const POSITION_STEP = 1024

/**
 * Board ordering: position of a card dropped between `prev` and `next`.
 * Floats let us insert by midpoint indefinitely without reindexing.
 */
export function computePosition(prev: number | undefined, next: number | undefined): number {
  if (prev === undefined && next === undefined) return POSITION_STEP
  if (prev === undefined) return (next as number) / 2
  if (next === undefined) return prev + POSITION_STEP
  return (prev + next) / 2
}
