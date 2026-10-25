import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Board, BoardRow, PaneState, Route, RouteStop, RouteWalk } from '../types'

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
// The launcher a single skill run is listed under; its row's walk names the skill.
const SKILL_LAUNCHER = 'skill'

// The fewest rows the pane's window may have for a scroll marker to share it with a line.
const MIN_ROWS_FOR_MARKERS = 3
const ROW_INDENT = 2
// A station sits under its seed, a nested item one step further, and a walk under its station.
const STATION_INDENT = 4
const DEPTH_INDENT = 2
const WALK_INDENT = 4

// Every string a person reads that is not a row's own text. Each is `change_text.md`'s, verbatim,
// but the seed, station, walk and skill labels, the scroll markers, the route's marks, the fix
// line, the ages and the task, which came after it: a running walk reads `running total 33m` and
// its step `implementation for 2m (Task 3 of 7)`, a waiting walk `started 3h ago`, where
// `change_text.md` had one `{n}m ago` at the line's end.
const TEXT = {
  commandMenu: "Read this instance's chains again and open the kensaiapp pane",
  empty: 'nothing',
  readFailed: 'The chains could not be read. The pane reads them again every 15 seconds.',
  opened: 'The kensaiapp pane is open.',
  openedNotShown: (reason: string) => `The kensaiapp pane is open but not shown yet: ${reason}`,
  waitingHeading: (count: number) => `WAITING ON YOU (${count})`,
  runningHeading: (count: number) => `RUNNING NOW (${count})`,
  minutes: (count: number) => `${count}m`,
  hours: (count: number) => `${count}h`,
  days: (count: number) => `${count}d`,
  runningTotal: (elapsed: string) => `running total ${elapsed}`,
  started: (elapsed: string) => `started ${elapsed} ago`,
  stepFor: (step: string, elapsed: string) => `${step} for ${elapsed}`,
  onTask: (step: string, task: number, tasks: number) => `${step} (Task ${task} of ${tasks})`,
  seed: (title: string) => `seed: ${title}`,
  station: (title: string) => `station: ${title}`,
  walk: (title: string) => `walk: ${title}`,
  skill: (name: string) => `skill: ${name}`,
  fixing: (name: string) => `↳ fixing: ${name}`,
  moreAbove: (count: number) => `↑ ${count} more above`,
  moreBelow: (count: number) => `↓ ${count} more below`,
  stop: { reached: '✓', current: '▸', parked: '‖', ahead: '○' },
  parked: 'parked',
  walkMark: { sealed: '✓', dropped: '✗', open: '●' },
  walkState: { sealed: 'sealed', dropped: 'dropped', open: '' },
  nextWalk: '○ next walk — not opened yet',
  nextStation: '○ next station — not opened yet',
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
  // A skill run on the station of a walk waiting on you is that walk's fix: it reads under the
  // walk, not as a running row of its own, and while it runs the walk is live work, so it reads
  // under Running now rather than Waiting on you — still halted, with why and when it started.
  const isSkill = (one: BoardRow) => one.launcher === SKILL_LAUNCHER
  const fixTarget = (one: BoardRow): BoardRow | undefined =>
    isSkill(one) && one.station
      ? board.waiting.find(walker => walker.key && walker.project === one.project && walker.station === one.station)
      : undefined
  const fixesOf = (one: BoardRow) => board.running.filter(fix => fixTarget(fix) === one)
  const waiting = board.waiting.filter(one => fixesOf(one).length === 0)
  // A fixed walk takes the place of its first fix, so Running now keeps the reader's newest-first order.
  const running = board.running.flatMap(one => {
    const walker = fixTarget(one)
    if (walker === undefined) return [one]
    return fixesOf(walker)[0] === one ? [walker] : []
  })
  const halted = (one: BoardRow) => board.waiting.includes(one)

  // What the row is doing: its launcher, why it waits, how long its walk has run (or, halted, when
  // it started), and its step with how long that step has run and, where the reader names one, the
  // task of its plan the run is on. Both ages count to now.
  const doing = (one: BoardRow, withLauncher: boolean): string[] => {
    const walkAge = elapsed(one.started_at, now)
    const stepAge = elapsed(one.step_started_at, now)
    const step = one.step && stepAge ? TEXT.stepFor(one.step, stepAge) : one.step
    return [
      withLauncher ? one.launcher : '',
      halted(one) ? one.status : '',
      walkAge && (halted(one) ? TEXT.started(walkAge) : TEXT.runningTotal(walkAge)),
      step && one.task && one.tasks ? TEXT.onTask(step, one.task, one.tasks) : step,
    ].filter(Boolean)
  }
  // Under a halted row: why it waits, dimmed, then each skill run fixing it — live work, so not.
  const waitLines = (one: BoardRow, indent: number): Line[] =>
    halted(one)
      ? [
          ...(one.reason ? [{ text: one.reason, dimColor: true, indent }] : []),
          ...fixesOf(one).map(fix => ({
            text: [TEXT.fixing(fix.walk), ...doing(fix, true)].join(DETAIL_SEPARATOR),
            indent,
          })),
        ]
      : []

  // The row's place on the journey, each line only where the reader found it. A project with a
  // route has its seed named there, so the row never repeats it; where the route also has a
  // current station, the row names only its walk.
  const row = (one: BoardRow, hasRoute: boolean, routeNamesStation: boolean): Line[] => {
    const place = [
      hasRoute ? '' : one.seed && TEXT.seed(one.seed),
      routeNamesStation ? '' : one.station && TEXT.station(one.station),
      one.walk && (isSkill(one) ? TEXT.skill(one.walk) : TEXT.walk(one.walk)),
    ].filter(Boolean)
    const detail = doing(one, !isSkill(one)).join(DETAIL_SEPARATOR)
    return [
      ...place.map(text => ({ text, indent: ROW_INDENT })),
      ...(detail ? [{ text: detail, dimColor: true, indent: ROW_INDENT }] : []),
      ...waitLines(one, ROW_INDENT),
    ]
  }

  // The seed, its checklist, and under the current station its walks; under any other station only
  // a walk a row is still on, as after its station has closed. A walk a row is on, open or already
  // sealed or dropped, reads on one line with what that row is doing, the launcher named when it
  // is halted; a second row on it follows beneath. Without an open walk the current station
  // shows that the next walk is owed, and with no station open the route shows, before its first
  // unreached item, that the next station is.
  const routeLines = (route: Route, rows: readonly BoardRow[]): Line[] => {
    const walkLines = (walk: RouteWalk, indent: number): Line[] => {
      const [first, ...more] = rows.filter(one => one.key === walk.key)
      const head = [`${TEXT.walkMark[walk.state]} ${walk.name}`, TEXT.walkState[walk.state],
        ...(first ? doing(first, halted(first)) : [])]
      return [
        { text: head.filter(Boolean).join(DETAIL_SEPARATOR), dimColor: walk.state !== 'open' && !first, indent },
        ...(first ? waitLines(first, indent + ROW_INDENT) : []),
        ...more.flatMap(one => [
          { text: doing(one, true).join(DETAIL_SEPARATOR), dimColor: true, indent: indent + ROW_INDENT },
          ...waitLines(one, indent + ROW_INDENT),
        ]),
      ]
    }
    const stopLines = (stop: RouteStop): Line[] => {
      const indent = STATION_INDENT + stop.depth * DEPTH_INDENT
      const isCurrent = stop.state === 'current'
      const hasOpenWalk = stop.walks.some(walk => walk.state === 'open')
      const text = [`${TEXT.stop[stop.state]} ${stop.name}`, stop.state === 'parked' ? TEXT.parked : '']
        .filter(Boolean)
        .join(DETAIL_SEPARATOR)
      return [
        { text, bold: isCurrent, dimColor: stop.state === 'ahead' || stop.state === 'parked', indent },
        ...stop.walks
          .filter(walk => isCurrent || rows.some(one => one.key === walk.key))
          .flatMap(walk => walkLines(walk, indent + WALK_INDENT)),
        ...(isCurrent && !hasOpenWalk ? [{ text: TEXT.nextWalk, dimColor: true, indent: indent + WALK_INDENT }] : []),
      ]
    }
    const isBetween = !route.stations.some(stop => stop.state === 'current')
    const firstUnreached = route.stations.findIndex(stop => stop.state !== 'reached')
    return [
      ...(route.seed ? [{ text: TEXT.seed(route.seed), indent: ROW_INDENT }] : []),
      ...route.stations.flatMap((stop, index) => [
        ...(isBetween && index === firstUnreached
          ? [{ text: TEXT.nextStation, dimColor: true, indent: STATION_INDENT }]
          : []),
        ...stopLines(stop),
      ]),
    ]
  }

  // Which section draws a project's route: the one holding a row on the current station's walk,
  // waiting before running; else the one holding a row on a closed station's walk; else the
  // section where the project first appears. The route is drawn there once, and the project's rows
  // in the other section are rows alone, so the live walk keeps its place in the tree over a walk
  // whose station has closed.
  const drawnKeysOf = (route: Route) =>
    new Set(route.stations.flatMap(stop => stop.walks.map(walk => walk.key)))
  const currentKeysOf = (route: Route) =>
    new Set(route.stations.filter(stop => stop.state === 'current').flatMap(stop => stop.walks.map(walk => walk.key)))
  const drawsRouteIn = (route: Route): boolean => {
    const walking = (rows: readonly BoardRow[], keys: ReadonlySet<string>) =>
      rows.some(one => one.project === route.project && keys.has(one.key))
    for (const keys of [currentKeysOf(route), drawnKeysOf(route)]) {
      if (walking(waiting, keys)) return true
      if (walking(running, keys)) return false
    }
    return waiting.some(one => one.project === route.project)
  }

  // A project's rows: in the section that draws its route, the route, with each row on one of its
  // walks on that walk's line and every other row below it; elsewhere, rows alone.
  const projectLines = (project: string, rows: readonly BoardRow[], isWaiting: boolean): Line[] => {
    const route = board.routes.find(one => one.project === project)
    if (route === undefined) return rows.flatMap(one => row(one, false, false))
    const namesPlace = route.stations.some(stop => stop.state === 'current')
    if (drawsRouteIn(route) !== isWaiting) return rows.flatMap(one => row(one, true, namesPlace))
    const drawnKeys = drawnKeysOf(route)
    return [
      ...routeLines(route, rows),
      ...rows.filter(one => !drawnKeys.has(one.key)).flatMap(one => row(one, true, namesPlace)),
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
        ...projectLines(project, projectRows, isWaiting),
      ]),
    ]
  }

  return [
    { text: board.instance ?? '', bold: true },
    { text: ' ' },
    ...section(TEXT.waitingHeading(waiting.length), waiting, true),
    { text: ' ' },
    ...section(TEXT.runningHeading(running.length), running, false),
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

// How long since `startedAt`, or '' where it is missing, unreadable or still ahead.
function elapsed(startedAt: string | undefined, now: number): string {
  const elapsedMs = now - Date.parse(startedAt ?? '')
  if (!Number.isFinite(elapsedMs) || elapsedMs < 0) return ''
  const minutes = Math.floor(elapsedMs / MS_PER_MINUTE)
  if (minutes < MINUTES_PER_HOUR) return TEXT.minutes(minutes)
  const hours = Math.floor(minutes / MINUTES_PER_HOUR)
  if (hours < HOURS_SHOWN_AS_HOURS) return TEXT.hours(hours)
  return TEXT.days(Math.floor(hours / HOURS_PER_DAY))
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
  const { instance, waiting, running, routes } = parsed as Record<string, unknown>
  if (!Array.isArray(waiting) || !Array.isArray(running)) return null
  if (typeof instance !== 'string' && instance !== null) return null
  if (!Array.isArray(routes)) return null
  return { instance, waiting, running, routes } as Board
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
