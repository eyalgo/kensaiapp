import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Board, BoardRow, PaneState } from '../types'

const PANE = 'kensaiapp-panel'
const PANE_TITLE = 'kensaiapp'
const COMMAND = 'kensaiapp-panel'
const REFRESH_MS = 15_000
const READ_TIMEOUT_MS = 20_000
const MS_PER_MINUTE = 60_000
const MINUTES_PER_HOUR = 60
const HOURS_PER_DAY = 24
const HOURS_SHOWN_AS_HOURS = 48
const DETAIL_SEPARATOR = ' · '

// The fewest rows the pane's window may have for a scroll marker to share it with a line.
const MIN_ROWS_FOR_MARKERS = 3
const ROW_INDENT = 2

// Every string a person reads that is not a row's own text. Each is `change_text.md`'s, verbatim,
// but the seed, station and walk labels and the scroll markers, which came after it.
const TEXT = {
  commandMenu: "Read this instance's chains again and open the kensaiapp pane",
  empty: 'nothing',
  readFailed: 'The chains could not be read. The pane reads them again every 15 seconds.',
  opened: 'The kensaiapp pane is open.',
  openedNotShown: (reason: string) => `The kensaiapp pane is open but not shown yet: ${reason}`,
  waitingHeading: (count: number) => `WAITING ON YOU (${count})`,
  runningHeading: (count: number) => `RUNNING NOW (${count})`,
  minutesAgo: (count: number) => `${count}m ago`,
  hoursAgo: (count: number) => `${count}h ago`,
  daysAgo: (count: number) => `${count}d ago`,
  seed: (title: string) => `seed: ${title}`,
  station: (title: string) => `station: ${title}`,
  walk: (title: string) => `walk: ${title}`,
  moreAbove: (count: number) => `↑ ${count} more above`,
  moreBelow: (count: number) => `↓ ${count} more below`,
} as const

// One row of the pane: a line is wrapped to the pane's width before it is drawn, so the pane's
// height is its count of lines.
type Line = {
  readonly text: string
  readonly bold?: boolean
  readonly dimColor?: boolean
  readonly color?: 'yellow' | 'green'
  readonly indent?: number
}

// The board as the pane's lines, top to bottom.
function boardLines(board: Board, now: number): Line[] {
  const row = (one: BoardRow, isWaiting: boolean): Line[] => {
    // The row's place on the journey, each line only where the reader found it.
    const place = [
      one.seed && TEXT.seed(one.seed),
      one.station && TEXT.station(one.station),
      one.walk && TEXT.walk(one.walk),
    ].filter(Boolean)
    const detail = [one.launcher, isWaiting ? one.status : '', one.step, age(one.started_at, now)]
      .filter(Boolean)
      .join(DETAIL_SEPARATOR)
    return [
      ...place.map(text => ({ text, indent: ROW_INDENT })),
      { text: detail, dimColor: true, indent: ROW_INDENT },
      ...(isWaiting && one.reason ? [{ text: one.reason, dimColor: true, indent: ROW_INDENT }] : []),
    ]
  }

  // A section's rows under one bold heading per project, in the order the projects first appear.
  const section = (heading: string, rows: readonly BoardRow[], isWaiting: boolean): Line[] => {
    const groups = new Map<string, BoardRow[]>()
    for (const one of rows) groups.set(one.project, [...(groups.get(one.project) ?? []), one])
    const color = rows.length > 0 ? (isWaiting ? 'yellow' : 'green') : undefined
    return [
      { text: heading, bold: true, color },
      ...(rows.length === 0 ? [{ text: TEXT.empty, dimColor: true }] : []),
      ...[...groups].flatMap(([project, projectRows]) => [
        { text: project, bold: true },
        ...projectRows.flatMap(one => row(one, isWaiting)),
      ]),
    ]
  }

  return [
    { text: board.instance ?? '', bold: true },
    { text: ' ' },
    ...section(TEXT.waitingHeading(board.waiting.length), board.waiting, true),
    { text: ' ' },
    ...section(TEXT.runningHeading(board.running.length), board.running, false),
  ]
}

// A line as the rows it takes in `columns` cells: broken at spaces, and a word wider than the row
// broken where the row ends. Each row keeps the line's style and indent.
function wrapLine(line: Line, columns: number): Line[] {
  const width = columns - (line.indent ?? 0)
  if (width < 1 || line.text.length <= width) return [line]
  const rows: string[] = []
  let current = ''
  for (const word of line.text.split(' ')) {
    const joined = current === '' ? word : `${current} ${word}`
    if (joined.length <= width) {
      current = joined
      continue
    }
    if (current !== '') rows.push(current)
    let rest = word
    while (rest.length > width) {
      rows.push(rest.slice(0, width))
      rest = rest.slice(width)
    }
    current = rest
  }
  if (current !== '') rows.push(current)
  return rows.map(text => ({ ...line, text }))
}

// The lines with a marker row where the window has lines out of view: one on the window's first
// row naming those above it, one on its last naming those below. A marker takes a row of its own
// and covers no line, so every line is reached by scrolling.
function withScrollMarkers(lines: readonly Line[], offset: number, bodyRows: number): Line[] {
  if (lines.length <= bodyRows || bodyRows < MIN_ROWS_FOR_MARKERS) return [...lines]
  const above = Math.min(offset, lines.length)
  const top = above > 0 ? [{ text: TEXT.moreAbove(above), dimColor: true }] : []
  const roomBelowTop = bodyRows - top.length
  const below = lines.length - above - roomBelowTop
  if (below <= 0) return [...lines.slice(0, above), ...top, ...lines.slice(above)]
  const shown = roomBelowTop - 1
  return [
    ...lines.slice(0, above),
    ...top,
    ...lines.slice(above, above + shown),
    { text: TEXT.moreBelow(lines.length - above - shown), dimColor: true },
    ...lines.slice(above + shown),
  ]
}

const UNREAD: PaneState = { board: null, hasFailed: false, isOpen: false }
// The pane's own state lives in `$.state`, because a hot reload loses a module's variables.
const pane = atom({ plugin: 'kensaiapp-panel', key: 'pane' } as const, UNREAD)

function age(startedAt: string, now: number): string {
  const elapsedMs = now - Date.parse(startedAt)
  if (!Number.isFinite(elapsedMs) || elapsedMs < 0) return ''
  const minutes = Math.floor(elapsedMs / MS_PER_MINUTE)
  if (minutes < MINUTES_PER_HOUR) return TEXT.minutesAgo(minutes)
  const hours = Math.floor(minutes / MINUTES_PER_HOUR)
  if (hours < HOURS_SHOWN_AS_HOURS) return TEXT.hoursAgo(hours)
  return TEXT.daysAgo(Math.floor(hours / HOURS_PER_DAY))
}

function parseBoard(stdout: string): Board | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(stdout)
  } catch {
    // A read that does not parse is a failed read, which the pane says (CP-503); the pane's line
    // names no cause because the three causes cannot be told apart to the person.
    return null
  }
  if (typeof parsed !== 'object' || parsed === null) return null
  const { instance, waiting, running } = parsed as Record<string, unknown>
  if (!Array.isArray(waiting) || !Array.isArray(running)) return null
  if (typeof instance !== 'string' && instance !== null) return null
  return { instance, waiting, running } as Board
}

// `$.process.run` resolves on any exit code, so a failed read is a rejection, a non-zero exit, or
// output that does not parse: all three come back as null. The project root is resolved inside the
// same guard, because a reader with no root to read cannot start either.
async function runReader($: EngineInterface): Promise<Board | null> {
  try {
    const root = await $.session.root()
    const result = await $.process.run(['python3', `${$.plugin.root}/../chain_board.py`, root], {
      timeoutMs: READ_TIMEOUT_MS,
    })
    return result.exitCode === 0 ? parseBoard(result.stdout) : null
  } catch {
    // The rejection is the failure the pane reports; there is no sink here to log it to.
    return null
  }
}

async function readChains($: EngineInterface): Promise<Board | null> {
  const board = await runReader($)
  await update($, pane, state => ({
    ...state,
    board: board ?? state.board,
    hasFailed: board === null,
  }))
  return board
}

// The person's command hands the pane the keyboard, so its arrows scroll it; the timed open does
// not, so a session's start never takes the keys from the prompt.
async function openPane($: EngineInterface, isAsked: boolean) {
  await update($, pane, state => ({ ...state, isOpen: true }))
  return $.ui.open({ id: PANE, title: PANE_TITLE, ...(isAsked ? { focus: true } : {}) })
}

// One timed read. A session that draws on no surface (a `claude -p` run) reads nothing; a read that
// finds no instance leaves the pane closed and registers nothing; every read that finds one
// registers the command, and the first opens the pane. The command is registered again on each
// read because a hot reload drops it while `$.state` keeps the pane open; a second registration
// replaces the first.
async function refresh($: EngineInterface): Promise<void> {
  if ((await $.session.surfaces()).length === 0) return
  const board = await readChains($)
  if (board === null || board.instance === null) return
  await $.command.register({ name: COMMAND, description: TEXT.commandMenu })
  if ((await read($, pane)).isOpen) return
  await openPane($, false)
}

// A timed read is awaited by nobody: the session's start must not wait on it, and the clock drops
// what its callback returns. So its rejection is handled here rather than left floating. Going on
// is safe: a failed read already shows in the pane, the next tick reads again, and a refused pane
// opens with `/kensaiapp-panel`. The line goes to the debug log alone, as the error states it.
function refreshInBackground($: EngineInterface): void {
  refresh($).catch((error: unknown) => {
    $.ui.log(error instanceof Error ? error.message : String(error), { to: 'debug' })
  })
}

export const register: Register = on => {
  // The tick starts first and the first read is not awaited, so the reader never holds the
  // session's start.
  on('session.start', async ($, e, next) => {
    $.clock.every(REFRESH_MS, () => refreshInBackground($))
    refreshInBackground($)

    return next(e)
  })

  on('command.run', { command: COMMAND }, async $ => {
    await readChains($)
    const opened = await openPane($, true)

    return { text: opened.isPlaced ? TEXT.opened : TEXT.openedNotShown(opened.reason) }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const { board, hasFailed } = await read($, pane)
    const now = await $.clock.now()

    if (hasFailed) return <Text dimColor>{TEXT.readFailed}</Text>
    if (board === null) return <Box />

    const { offset, bodyRows } = e.props.scroll
    const rows = boardLines(board, now).flatMap(line => wrapLine(line, e.props.bodyColumns))
    const lines = withScrollMarkers(rows, offset, bodyRows)

    return (
      <Box flexDirection="column">
        {lines.map(({ text, indent, ...style }, index) => (
          <Box key={`${index}`} paddingLeft={indent ?? 0}>
            <Text {...style} wrap="truncate-end">
              {text}
            </Text>
          </Box>
        ))}
      </Box>
    )
  })
}
