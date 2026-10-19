/** One row of `chain_board.py`'s output: a walk, as the reader names it. */
export type BoardRow = {
  readonly launcher: string
  readonly project: string
  readonly seed: string
  readonly station: string
  readonly walk: string
  readonly step: string
  readonly status: string
  readonly reason: string
  readonly started_at: string
}

/** What `chain_board.py` prints. `instance` is null for a folder in no instance. */
export type Board = {
  readonly instance: string | null
  readonly waiting: readonly BoardRow[]
  readonly running: readonly BoardRow[]
}

/**
 * What the pane draws from. `board` is the last read that parsed; `hasFailed` is set while the
 * newest read did not; `isOpen` is set once the command is registered and the pane opened.
 */
export type PaneState = {
  readonly board: Board | null
  readonly hasFailed: boolean
  readonly isOpen: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'kensaiapp-panel': { pane: PaneState }
  }
}
