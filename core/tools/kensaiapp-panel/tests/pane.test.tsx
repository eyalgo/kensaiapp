import { expect, mock, test } from 'claude-code/testing'

// Every instance, project and walk below is invented.
const STARTED_AT = '2026-03-01T10:00:00+00:00'
const THREE_HOURS_LATER = Date.parse('2026-03-01T13:00:00Z')
const FIFTEEN_SECONDS = 15_000

const WAITING_ROW = {
  launcher: 'chain-change',
  project: 'widgets',
  seed: 'widgets everywhere',
  station: 'the widgets ship',
  walk: 'the first widget',
  key: 'unit-the-first-widget',
  step: 'design',
  status: 'halted',
  reason: 'the run stopped before it made a marker',
  started_at: STARTED_AT,
  step_started_at: '',
  task: 0,
  tasks: 0,
}
const RUNNING_ROW = {
  launcher: 'build-idea',
  project: 'gadgets',
  seed: '',
  station: '',
  walk: 'the gadgets sing',
  key: '',
  step: '',
  status: '',
  reason: '',
  started_at: STARTED_AT,
  step_started_at: '',
  task: 0,
  tasks: 0,
}
const BOARD = { instance: 'sample-instance', waiting: [WAITING_ROW], running: [RUNNING_ROW], routes: [] }
const EMPTY_BOARD = { instance: 'sample-instance', waiting: [], running: [], routes: [] }
const NO_INSTANCE = { instance: null, waiting: [], running: [], routes: [] }

const SURFACES = ['terminal', 'desktop'] as const

// A window taller than any board below, unless a test gives it one of its own.
const ROOMY = { offset: 0, bodyRows: 100 }
// A body wider than any line below, unless a test gives it a width of its own.
const WIDE = 200

const mountPane = ($: any, surface: (typeof SURFACES)[number], scroll = ROOMY, bodyColumns = WIDE) =>
  $.ui.mount({
    plugin: 'kensaiapp-panel',
    surface,
    component: 'Pane',
    props: { title: 'kensaiapp', isFocused: false, bodyColumns, scroll },
    requestId: 'kensaiapp-panel',
  })

type Reader = { stdout: string; exitCode: number } | 'cannot-start'

// The engine, as the plugin sees it: one instance session on one terminal, whose reader answers
// with what `reader()` returns each time it runs. Everything the plugin reaches is recorded.
type Placement = { isPlaced: true } | { isPlaced: false; reason: string }

function standIn(
  on: any,
  reader: () => Reader,
  surfaces: readonly string[] = ['terminal'],
  placement: Placement | 'refused' = { isPlaced: true },
  root: string | 'unresolved' = '/sample/instance',
) {
  const calls = {
    reads: [] as string[][],
    opened: [] as string[],
    titles: [] as (string | undefined)[],
    focuses: [] as (true | undefined)[],
    registered: [] as string[],
  }
  on('session.start', (_: unknown, e: { cwd: string }) => ({ cwd: e.cwd }))
  on('session.root', () => {
    if (root === 'unresolved') throw new Error('no project root')
    return { value: root }
  })
  on('session.surfaces', () => ({ value: surfaces }))
  on('command.register', (_: unknown, e: { name: string }) => {
    calls.registered.push(e.name)
    return { value: { command: e.name } }
  })
  on('ui.open', (_: unknown, e: { id: string; title?: string; focus?: true }) => {
    calls.opened.push(e.id)
    calls.titles.push(e.title)
    calls.focuses.push(e.focus)
    if (placement === 'refused') throw new Error('a ui.open hook refused the pane')
    return { value: placement }
  })
  on('process.run', (_: unknown, e: { argv: string[] }) => {
    calls.reads.push(e.argv)
    const answer = reader()
    if (answer === 'cannot-start') throw new Error('python3 not found')
    return { value: { exitCode: answer.exitCode, stdout: answer.stdout, stderr: '' } }
  })
  return calls
}

const prints = (board: object): Reader => ({ stdout: JSON.stringify(board), exitCode: 0 })
const startSession = ($: any) =>
  $.session.start({ cwd: '/sample/instance', surface: 'terminal', isInteractive: true })

test('the pane shows what waits on you above what runs', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    const at = (pattern: RegExp) => texts.findIndex(text => pattern.test(text))
    expect(at(/WAITING ON YOU \(1\)/)).toBeGreaterThanOrEqual(0)
    expect(at(/WAITING ON YOU \(1\)/)).toBeLessThan(at(/RUNNING NOW \(1\)/))
    expect(at(/^station: the widgets ship$/)).toBeGreaterThan(at(/WAITING ON YOU/))
    expect(at(/^widgets$/)).toBeGreaterThan(at(/WAITING ON YOU/))
    expect(at(/^widgets$/)).toBeLessThan(at(/^station: the widgets ship$/))
    expect(at(/^chain-change · halted · started 3h ago · design$/)).toBeGreaterThanOrEqual(0)
    expect(at(/the run stopped before it made a marker/)).toBeGreaterThanOrEqual(0)
    expect(at(/^walk: the gadgets sing$/)).toBeGreaterThan(at(/RUNNING NOW/))
    expect(at(/^gadgets$/)).toBeGreaterThan(at(/RUNNING NOW/))
    expect(at(/^build-idea/)).toBeGreaterThan(at(/^walk: the gadgets sing$/))
    await ui.unmount()
  }
})

test('a section names each project once, above its rows', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const running = [
    { ...RUNNING_ROW, walk: 'the first gadget' },
    { ...RUNNING_ROW, project: 'widgets', walk: 'a widget' },
    { ...RUNNING_ROW, walk: 'the second gadget' },
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
  expect(texts.filter(text => text === 'gadgets')).toHaveLength(1)
  const at = (text: string) => texts.indexOf(text)
  expect(at('gadgets')).toBeLessThan(at('walk: the first gadget'))
  expect(at('walk: the first gadget')).toBeLessThan(at('walk: the second gadget'))
  expect(at('walk: the second gadget')).toBeLessThan(at('widgets'))
  expect(at('widgets')).toBeLessThan(at('walk: a widget'))
  await ui.unmount()
})

test('an empty section says so', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(EMPTY_BOARD))
  await $.command.run({ command: 'kensaiapp-panel', args: '' })
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: /WAITING ON YOU \(0\)/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /RUNNING NOW \(0\)/ })).toBeDefined()
    expect(await ui.findAll({ type: 'Text', text: /^nothing$/ })).toHaveLength(2)
    await ui.unmount()
  }
})

test('a row shows its seed, its station and its walk, in that order, above its detail', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints({ ...EMPTY_BOARD, waiting: [WAITING_ROW] }))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    const at = (text: string) => texts.indexOf(text)
    expect(at('seed: widgets everywhere')).toBeGreaterThan(at('widgets'))
    expect(at('station: the widgets ship')).toBe(at('seed: widgets everywhere') + 1)
    expect(at('walk: the first widget')).toBe(at('station: the widgets ship') + 1)
    expect(at('chain-change · halted · started 3h ago · design')).toBe(at('walk: the first widget') + 1)
    await ui.unmount()
  }
})

// BOARD draws fourteen lines: the instance, a gap, the waiting heading, its project, a row of five,
// a gap, the running heading, its project and a row of two.
const BOARD_LINES = 14
const MARKER = /^[↑↓] \d+ more (above|below)$/
const markers = (texts: string[]) => texts.filter(text => MARKER.test(text))

const paneTexts = async ($: any, on: any, scroll: { offset: number; bodyRows: number }) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal', scroll)
  const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
  await ui.unmount()
  return texts
}

test('a pane whose lines fit its window shows no scroll marker', async ($, on) => {
  const texts = await paneTexts($, on, { offset: 0, bodyRows: BOARD_LINES })
  expect(texts).toHaveLength(BOARD_LINES)
  expect(markers(texts)).toEqual([])
})

test('a window over the top of the pane names the lines below it on its last row', async ($, on) => {
  const texts = await paneTexts($, on, { offset: 0, bodyRows: 6 })
  expect(markers(texts)).toEqual(['↓ 9 more below'])
  expect(texts.indexOf('↓ 9 more below')).toBe(5)
  expect(texts.indexOf('seed: widgets everywhere')).toBe(4)
  expect(texts).toHaveLength(BOARD_LINES + 1)
})

test('a window in the middle of the pane names the lines above and below it', async ($, on) => {
  const texts = await paneTexts($, on, { offset: 4, bodyRows: 6 })
  expect(markers(texts)).toEqual(['↑ 4 more above', '↓ 6 more below'])
  expect(texts.indexOf('↑ 4 more above')).toBe(4)
  expect(texts.indexOf('seed: widgets everywhere')).toBe(5)
  expect(texts.indexOf('↓ 6 more below')).toBe(9)
})

test('a window at the end of the pane names only the lines above it', async ($, on) => {
  const texts = await paneTexts($, on, { offset: 9, bodyRows: 6 })
  expect(markers(texts)).toEqual(['↑ 9 more above'])
  expect(texts.indexOf('↑ 9 more above')).toBe(9)
  expect(texts.at(-1)).toBe('build-idea · running total 3h')
})

test('a scroll marker covers no line: every line is still drawn', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const textsAt = async (scroll: { offset: number; bodyRows: number }): Promise<string[]> => {
    const ui = await mountPane($, 'terminal', scroll)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    await ui.unmount()
    return texts
  }

  const everyLine = await textsAt(ROOMY)
  for (const offset of [0, 4, 9]) {
    const texts = await textsAt({ offset, bodyRows: 6 })
    expect(texts.filter(text => !MARKER.test(text))).toEqual(everyLine)
  }
})

test('a window too short to share shows no scroll marker', async ($, on) => {
  const texts = await paneTexts($, on, { offset: 3, bodyRows: 2 })
  expect(markers(texts)).toEqual([])
})

test('a row shows only the seed, station and walk it has', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const running = [
    RUNNING_ROW,
    { ...RUNNING_ROW, project: 'widgets', station: 'the widgets ship', walk: '' },
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    expect(texts.filter(text => /^(seed|station|walk): /.test(text))).toEqual([
      'walk: the gadgets sing',
      'station: the widgets ship',
    ])
    expect(texts.filter(text => text === '')).toEqual([])
    await ui.unmount()
  }
})

test('a waiting row shows when its walk started, a running row how long it has run', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const waitingDetail = /^chain-change · halted · started 3h ago · design$/
    expect(await ui.find({ type: 'Text', text: waitingDetail })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h$/ })).toBeDefined()
    await ui.unmount()
  }
})

test('a row with no start time shows no age', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const untimed = { ...RUNNING_ROW, started_at: '' }
  standIn(on, () => prints({ ...BOARD, running: [untimed] }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /^build-idea$/ })).toBeDefined()
  await ui.unmount()
})

test('an age reads in minutes below an hour, hours below two days, and days after', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const startedBefore = (minutes: number) =>
    new Date(THREE_HOURS_LATER - minutes * 60_000).toISOString()
  const running = [
    { ...RUNNING_ROW, walk: 'minutes', started_at: startedBefore(59) },
    { ...RUNNING_ROW, walk: 'hours', started_at: startedBefore(47 * 60 + 59) },
    { ...RUNNING_ROW, walk: 'days', started_at: startedBefore(48 * 60) },
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 59m$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 47h$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 2d$/ })).toBeDefined()
  await ui.unmount()
})

test('a running row reads how long its walk has run, then its step with how long that step has run', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const stepBefore = (minutes: number) => new Date(THREE_HOURS_LATER - minutes * 60_000).toISOString()
  const running = [
    { ...RUNNING_ROW, walk: 'minutes', step: 'design', step_started_at: stepBefore(2) },
    { ...RUNNING_ROW, walk: 'hours', step: 'plan', step_started_at: stepBefore(120) },
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · design for 2m$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · plan for 2h$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^walk: minutes$/ })).toBeDefined()
    await ui.unmount()
  }
})

test('a row naming no walk still reads both ages on its detail line', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const unnamed = { ...RUNNING_ROW, walk: '', step: 'design', step_started_at: new Date(THREE_HOURS_LATER - 60_000).toISOString() }
  standIn(on, () => prints({ ...EMPTY_BOARD, running: [unnamed] }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · design for 1m$/ })).toBeDefined()
  await ui.unmount()
})

test('a step start that is missing or unreadable shows no step age', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const { step_started_at: _, ...fromAnOlderReader } = { ...RUNNING_ROW, walk: 'older', step: 'design' }
  const running = [{ ...RUNNING_ROW, walk: 'unreadable', step: 'plan', step_started_at: 'soon' }, fromAnOlderReader]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · plan$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · design$/ })).toBeDefined()
  await ui.unmount()
})

test('a running row on a task of its plan reads which task after its step age', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const stepStarted = new Date(THREE_HOURS_LATER - 3 * 60_000).toISOString()
  const running = [
    { ...RUNNING_ROW, walk: 'timed', step: 'implementation', step_started_at: stepStarted, task: 3, tasks: 7 },
    { ...RUNNING_ROW, walk: 'untimed', step: 'implementation', task: 1, tasks: 2 },
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · implementation for 3m \(Task 3 of 7\)$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · implementation \(Task 1 of 2\)$/ })).toBeDefined()
    await ui.unmount()
  }
})

test('a row with no task read, or from a reader before tasks, reads no task', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const { task: _, tasks: __, ...fromAnOlderReader } = { ...RUNNING_ROW, walk: 'older', step: 'plan' }
  const running = [
    { ...RUNNING_ROW, walk: 'none', step: 'implementation', task: 0, tasks: 0 },
    { ...RUNNING_ROW, walk: 'no-step', step: '', task: 2, tasks: 4 },
    fromAnOlderReader,
  ]
  standIn(on, () => prints({ ...EMPTY_BOARD, running }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · implementation$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^build-idea · running total 3h · plan$/ })).toBeDefined()
  expect(await ui.findAll({ type: 'Text', text: /Task/ })).toEqual([])
  await ui.unmount()
})

test('a running row shows no reason', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const noisy = { ...RUNNING_ROW, reason: 'a reason that belongs to a waiting row' }
  standIn(on, () => prints({ ...EMPTY_BOARD, running: [noisy] }))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /a reason that belongs/ })).toBeUndefined()
  await ui.unmount()
})

test('the pane re-reads every 15 seconds', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const later = { ...BOARD, waiting: [{ ...WAITING_ROW, walk: 'the second board' }] }
  let board: object = BOARD
  const calls = standIn(on, () => prints(board))
  await startSession($)
  await clock.settle()
  expect(calls.reads).toHaveLength(1)

  board = later
  await clock.advance(FIFTEEN_SECONDS)

  expect(calls.reads).toHaveLength(2)
  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: /^walk: the second board$/ })).toBeDefined()
    await ui.unmount()
  }
})

const failureLine = /^The chains could not be read\. The pane reads them again every 15 seconds\.$/

test('a reader that cannot start says so in the pane', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => 'cannot-start')
  await $.command.run({ command: 'kensaiapp-panel', args: '' })
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeDefined()
    expect(await ui.findAll({ type: 'Text', text: /WAITING ON YOU|RUNNING NOW/ })).toHaveLength(0)
    await ui.unmount()
  }
})

test('a reader that exits non-zero says so in the pane', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => ({ stdout: JSON.stringify(BOARD), exitCode: 1 }))
  await $.command.run({ command: 'kensaiapp-panel', args: '' })
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeDefined()
    expect(await ui.findAll({ type: 'Text', text: /WAITING ON YOU|RUNNING NOW/ })).toHaveLength(0)
    await ui.unmount()
  }
})

test('a reader whose output does not parse says so in the pane', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => ({ stdout: 'not json', exitCode: 0 }))
  await $.command.run({ command: 'kensaiapp-panel', args: '' })
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeDefined()
    expect(await ui.findAll({ type: 'Text', text: /WAITING ON YOU|RUNNING NOW/ })).toHaveLength(0)
    await ui.unmount()
  }
})

test('a session outside any instance opens no pane and registers no command', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(NO_INSTANCE))
  await startSession($)
  await clock.settle()
  await clock.advance(FIFTEEN_SECONDS)

  expect(calls.reads.length).toBeGreaterThan(0)
  expect(calls.opened).toEqual([])
  expect(calls.registered).toEqual([])
})

test('a session drawing on no surface runs no read', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD), [])
  await startSession($)
  await clock.settle()
  await clock.advance(FIFTEEN_SECONDS)

  expect(calls.reads).toEqual([])
})

test('a session in an instance registers the command and opens the pane once', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  await clock.advance(FIFTEEN_SECONDS)
  await clock.advance(FIFTEEN_SECONDS)

  expect(calls.reads).toHaveLength(3)
  expect(new Set(calls.registered)).toEqual(new Set(['kensaiapp-panel']))
  expect(calls.opened).toEqual(['kensaiapp-panel'])
})

// A hot reload starts the session again with `$.state` kept, so the pane is already open.
test('a session started again with its pane open registers the command again', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const registeredBefore = calls.registered.length

  await startSession($)
  await clock.settle()

  expect(calls.registered.length).toBeGreaterThan(registeredBefore)
  expect(calls.opened).toEqual(['kensaiapp-panel'])
})

test('the reader is run on the instance root through the folder above the mod', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  const [python, script, root] = calls.reads[0] ?? []
  expect(python).toBe('python3')
  expect(script).toMatch(/\/\.\.\/chain_board\.py$/)
  expect(root).toBe('/sample/instance')
})

test('the pane offers no control', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.findAll({ type: 'Button' })).toHaveLength(0)
    if (surface === 'terminal') expect(await ui.findAll({ type: 'Input' })).toHaveLength(0)
    await ui.unmount()
  }
})

test('the command reads again and reopens the pane', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const readsBefore = calls.reads.length
  const openedBefore = calls.opened.length

  const reply = await $.command.run({ command: 'kensaiapp-panel', args: '' })

  expect(calls.reads).toHaveLength(readsBefore + 1)
  expect(calls.opened).toHaveLength(openedBefore + 1)
  expect(calls.opened.at(-1)).toBe('kensaiapp-panel')
  expect(reply).toEqual({ text: 'The kensaiapp pane is open.' })
})

test('the command says when the pane is open but not shown yet', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD), ['terminal'], {
    isPlaced: false,
    reason: 'the terminal is too narrow',
  })
  await clock.settle()

  const reply = await $.command.run({ command: 'kensaiapp-panel', args: '' })

  expect(reply).toEqual({
    text: 'The kensaiapp pane is open but not shown yet: the terminal is too narrow',
  })
})

test('the pane names its instance above both sections', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    const name = texts.indexOf('sample-instance')
    expect(name).toBeGreaterThanOrEqual(0)
    expect(name).toBeLessThan(texts.findIndex(text => /WAITING ON YOU/.test(text)))
    await ui.unmount()
  }
})

test('the pane opens titled kensaiapp', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  await $.command.run({ command: 'kensaiapp-panel', args: '' })

  expect(calls.titles).toEqual(['kensaiapp', 'kensaiapp'])
})

test('a failed read replaces the sections, and the next read that succeeds brings them back', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const answers: Reader[] = [prints(BOARD), 'cannot-start', prints(BOARD)]
  standIn(on, () => answers.shift() ?? prints(BOARD))
  await startSession($)
  await clock.settle()

  await clock.advance(FIFTEEN_SECONDS)
  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeDefined()
    expect(await ui.findAll({ type: 'Text', text: /WAITING ON YOU|RUNNING NOW/ })).toHaveLength(0)
    await ui.unmount()
  }

  await clock.advance(FIFTEEN_SECONDS)
  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /WAITING ON YOU \(1\)/ })).toBeDefined()
    await ui.unmount()
  }
})

test('a reader that cannot start for want of a project root says so in the pane', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD), ['terminal'], { isPlaced: true }, 'unresolved')
  await $.command.run({ command: 'kensaiapp-panel', args: '' })
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    expect(await ui.find({ type: 'Text', text: failureLine })).toBeDefined()
    await ui.unmount()
  }
})

test('a refused pane leaves the session reading every 15 seconds', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD), ['terminal'], 'refused')
  await startSession($)
  await clock.settle()
  await clock.advance(FIFTEEN_SECONDS)

  expect(calls.opened).toEqual(['kensaiapp-panel'])
  expect(calls.reads).toHaveLength(2)
})

test('the command hands the pane the keyboard; the timed open does not', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const calls = standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  await $.command.run({ command: 'kensaiapp-panel', args: '' })

  expect(calls.focuses).toEqual([undefined, true])
})

// The waiting row's reason, `the run stopped before it made a marker`, in a body 20 cells wide: its
// indent of 2 leaves 18 for the text.
const NARROW = 20

const textsAtWidth = async ($: any, on: any, bodyColumns: number, scroll = ROOMY) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal', scroll, bodyColumns)
  const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
  await ui.unmount()
  return texts
}

test('a line wider than the pane wraps at its spaces onto rows of its own', async ($, on) => {
  const texts = await textsAtWidth($, on, NARROW)
  const first = texts.indexOf('the run stopped')
  expect(texts.slice(first, first + 3)).toEqual(['the run stopped', 'before it made a', 'marker'])
})

test('a word wider than the pane is broken where its row ends', async ($, on) => {
  const long = 'x'.repeat(NARROW * 2)
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints({ ...BOARD, waiting: [{ ...WAITING_ROW, reason: long }] }))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal', ROOMY, NARROW)
  const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
  await ui.unmount()
  const row = 'x'.repeat(NARROW - 2)
  const first = texts.indexOf(row)
  expect(texts.slice(first, first + 3)).toEqual([row, row, 'xxxx'])
})

test('a line that fits the pane is drawn whole on one row', async ($, on) => {
  const texts = await textsAtWidth($, on, WIDE)
  expect(texts).toContain('the run stopped before it made a marker')
})

test('a scroll marker counts wrapped rows, not lines', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()
  const textsAt = async (bodyColumns: number, scroll = ROOMY): Promise<string[]> => {
    const ui = await mountPane($, 'terminal', scroll, bodyColumns)
    const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
    await ui.unmount()
    return texts
  }

  const wide = await textsAt(WIDE)
  const narrow = await textsAt(NARROW)
  const below = await textsAt(NARROW, { offset: 0, bodyRows: 6 })
  expect(narrow.length).toBeGreaterThan(wide.length)
  expect(markers(below)).toEqual([`↓ ${narrow.length - 5} more below`])
})

// --- the route: a project's seed, its checklist, and its stations' walks ------------------------

const OPEN_WALK = { name: 'the-first-widget', key: 'unit-the-first-widget', state: 'open' }
const ROUTE = {
  project: 'widgets',
  seed: 'widgets everywhere',
  stations: [
    { name: 'the-widgets-exist', state: 'reached', depth: 0, walks: [] },
    {
      name: 'the-widgets-ship',
      state: 'current',
      depth: 0,
      walks: [{ name: 'an-earlier-try', key: 'unit-an-earlier-try', state: 'dropped' },
        { name: 'the-boxes', key: 'unit-the-boxes', state: 'sealed' }, OPEN_WALK],
    },
    { name: '2↳. a-nested-step', state: 'ahead', depth: 1, walks: [] },
    { name: 'the-widgets-sing', state: 'ahead', depth: 0, walks: [] },
  ],
}

const routeTexts = async ($: any, on: any, board: object) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(board))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal')
  const texts = (await ui.findAll({ type: 'Text' })).map((found: any) => found.text as string)
  await ui.unmount()
  return texts
}

test('a project with a route shows its seed and each station in checklist order, marked', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [ROUTE] })
  const from = texts.indexOf('widgets')
  expect(texts.slice(from, from + 6)).toEqual([
    'widgets',
    'seed: widgets everywhere',
    '✓ the-widgets-exist',
    '▸ the-widgets-ship',
    '✗ an-earlier-try · dropped',
    '✓ the-boxes · sealed',
  ])
  expect(texts.slice(from + 6, from + 10)).toEqual([
    '● the-first-widget · chain-change · halted · started 3h ago · design',
    'the run stopped before it made a marker',
    '○ 2↳. a-nested-step',
    '○ the-widgets-sing',
  ])
})

test('a row walking the open walk names no seed, station or walk of its own', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [ROUTE] })
  expect(texts.filter((text: string) => /^(seed|station|walk): /.test(text))).toEqual(['seed: widgets everywhere'])
})

test('a current station with no open walk says the next walk is not opened yet', async ($, on) => {
  const [reached, current, ...ahead] = ROUTE.stations
  const sealedOnly = { ...current!, walks: current!.walks.filter(walk => walk.state !== 'open') }
  const route = { ...ROUTE, stations: [reached, sealedOnly, ...ahead] }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [{ ...RUNNING_ROW, project: 'widgets' }], routes: [route] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('○ next walk — not opened yet')).toBe(at('✓ the-boxes · sealed') + 1)
  expect(at('○ 2↳. a-nested-step')).toBe(at('○ next walk — not opened yet') + 1)
})

test("a row on no open walk is drawn below its project's route, naming only its walk", async ($, on) => {
  const other = { ...RUNNING_ROW, project: 'widgets', walk: 'the widgets sweep', key: '' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [other], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('walk: the widgets sweep')).toBe(at('○ the-widgets-sing') + 1)
  expect(at('build-idea · running total 3h')).toBe(at('walk: the widgets sweep') + 1)
  expect(texts).not.toContain('station: the widgets ship')
})

test("a route is drawn only under its own project", async ($, on) => {
  const texts = await routeTexts($, on, { ...BOARD, routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('walk: the gadgets sing')).toBe(at('gadgets') + 1)
  expect(texts.filter((text: string) => text === 'seed: widgets everywhere')).toHaveLength(1)
})

test('a reader output with no routes is a failed read', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  const { routes: _, ...withoutRoutes } = BOARD
  standIn(on, () => prints(withoutRoutes))
  await startSession($)
  await clock.settle()

  const ui = await mountPane($, 'terminal')
  expect(await ui.find({ type: 'Text', text: /could not be read/ })).toBeDefined()
  await ui.unmount()
})

test('a route is drawn once, under the section where its project first appears', async ($, on) => {
  const sweep = { ...RUNNING_ROW, project: 'widgets', walk: 'the widgets sweep', key: '' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [sweep], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(texts.filter((text: string) => text === 'seed: widgets everywhere')).toHaveLength(1)
  expect(at('seed: widgets everywhere')).toBeLessThan(at('RUNNING NOW (1)'))
  expect(at('walk: the widgets sweep')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(texts).not.toContain('station: the widgets ship')
})

test('a row keeps its station when the route has no current station', async ($, on) => {
  const between = { ...ROUTE, stations: ROUTE.stations.map(stop => ({ ...stop, state: stop.state === 'current' ? 'ahead' : stop.state, walks: [] })) }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [between] })
  expect(texts).toContain('station: the widgets ship')
  expect(texts).toContain('walk: the first widget')
  expect(texts).not.toContain('○ next walk — not opened yet')
  expect(texts.filter((text: string) => text === 'seed: widgets everywhere')).toHaveLength(1)
})

test('a walk line on the route carries its step age too', async ($, on) => {
  const stepStarted = new Date(THREE_HOURS_LATER - 5 * 60_000).toISOString()
  const walking = { ...RUNNING_ROW, project: 'widgets', key: 'unit-the-first-widget', step: 'implementation', step_started_at: stepStarted }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [walking], routes: [ROUTE] })
  expect(texts).toContain('● the-first-widget · running total 3h · implementation for 5m')
})

test('an open walk no row is walking reads alone', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [{ ...RUNNING_ROW, project: 'widgets' }], routes: [ROUTE] })
  expect(texts).toContain('● the-first-widget')
  expect(texts).not.toContain('○ next walk — not opened yet')
})

test('the route is drawn where the row walking its open walk is, even when another row waits', async ($, on) => {
  const owed = { ...WAITING_ROW, walk: 'an older idea', key: '' }
  const walking = { ...RUNNING_ROW, project: 'widgets', key: 'unit-the-first-widget', step: 'implementation' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [owed], running: [walking], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(texts).toContain('● the-first-widget · running total 3h · implementation')
  expect(at('● the-first-widget · running total 3h · implementation')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(at('walk: an older idea')).toBeLessThan(at('RUNNING NOW (1)'))
  expect(texts.filter((text: string) => text === 'seed: widgets everywhere')).toHaveLength(1)
  expect(texts).not.toContain('walk: the first widget')
})

test('a parked station reads with its own mark and says it is parked', async ($, on) => {
  const stations = ROUTE.stations.map(stop => (stop.name === 'the-widgets-sing' ? { ...stop, state: 'parked' } : stop))
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [{ ...ROUTE, stations }] })
  expect(texts).toContain('‖ the-widgets-sing · parked')
})

test('with no station open the route says the next station is not opened yet, before the first unreached', async ($, on) => {
  const between = { ...ROUTE, stations: ROUTE.stations.map(stop => ({ ...stop, state: stop.state === 'current' ? 'ahead' : stop.state, walks: [] })) }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [between] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('○ next station — not opened yet')).toBe(at('✓ the-widgets-exist') + 1)
  expect(at('○ the-widgets-ship')).toBe(at('○ next station — not opened yet') + 1)
})

test('a route every item of which is reached says no station is owed', async ($, on) => {
  const walked = { ...ROUTE, stations: ROUTE.stations.map(stop => ({ ...stop, state: 'reached', walks: [] })) }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], routes: [walked] })
  expect(texts).not.toContain('○ next station — not opened yet')
})

// --- a skill run: the fix of a walk waiting on you, or a row of its own ------------------------

const SKILL_ROW = {
  ...RUNNING_ROW,
  launcher: 'skill',
  project: 'widgets',
  seed: 'widgets everywhere',
  station: 'the widgets ship',
  walk: 'widget-implementation',
}

test('a skill run on the station of a walk waiting on you reads under that walk as its fix', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('↳ fixing: widget-implementation · skill · running total 3h'))
    .toBe(at('the run stopped before it made a marker') + 1)
  expect(texts.filter((text: string) => text === 'widgets')).toHaveLength(1)
})

test('a walk with a skill run fixing it is live work: it reads under Running now, still halted', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(texts).toContain('WAITING ON YOU (0)')
  expect(texts).toContain('RUNNING NOW (1)')
  expect(at('widgets')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(at('● the-first-widget · chain-change · halted · started 3h ago · design'))
    .toBe(at('the run stopped before it made a marker') - 1)
})

test('a walk with a skill run fixing it, and no route, reads under Running now, still halted', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW] })
  const at = (text: string) => texts.indexOf(text)
  expect(texts).toContain('RUNNING NOW (1)')
  expect(at('walk: the first widget')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(at('chain-change · halted · started 3h ago · design')).toBe(at('walk: the first widget') + 1)
})

test('a fixed walk moves to Running now alone: another walk waiting on you keeps its place', async ($, on) => {
  const other = { ...WAITING_ROW, project: 'gizmos', station: 'the gizmos ship', walk: 'the first gizmo', key: 'unit-the-first-gizmo' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW, other], running: [SKILL_ROW] })
  const at = (text: string) => texts.indexOf(text)
  expect(texts).toContain('WAITING ON YOU (1)')
  expect(texts).toContain('RUNNING NOW (1)')
  expect(at('gizmos')).toBeLessThan(at('RUNNING NOW (1)'))
  expect(at('widgets')).toBeGreaterThan(at('RUNNING NOW (1)'))
})

test('a fixed walk takes its fix\'s place in Running now, which reads newest first', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [RUNNING_ROW, SKILL_ROW] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('gadgets')).toBeGreaterThan(at('RUNNING NOW (2)'))
  expect(at('widgets')).toBeGreaterThan(at('gadgets'))
  expect(texts.filter((text: string) => text.startsWith('↳ fixing'))).toHaveLength(1)
})

test('a fixed walk whose fix is newest reads first in Running now', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW, RUNNING_ROW] })
  expect(texts.indexOf('gadgets')).toBeGreaterThan(texts.indexOf('widgets'))
})

test('a skill run fixing a walk reads at full brightness, under the dimmed reason the walk waits', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints({ ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW], routes: [ROUTE] }))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal')
  const found = (await ui.findAll({ type: 'Text' })) as any[]
  await ui.unmount()
  const dim = (text: string) => found.find(one => one.text === text)?.props.dimColor
  expect(dim('↳ fixing: widget-implementation · skill · running total 3h')).toBeFalsy()
  expect(dim('the run stopped before it made a marker')).toBe(true)
})

test('a skill run reads its fix under a walk waiting with no route too', async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [SKILL_ROW] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('↳ fixing: widget-implementation · skill · running total 3h'))
    .toBe(at('the run stopped before it made a marker') + 1)
})

test('a skill run on no waiting walk is a running row named as a skill', async ($, on) => {
  const elsewhere = { ...SKILL_ROW, station: 'the widgets sing' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [WAITING_ROW], running: [elsewhere] })
  expect(texts).toContain('RUNNING NOW (1)')
  expect(texts).toContain('skill: widget-implementation')
  expect(texts.indexOf('running total 3h')).toBe(texts.indexOf('skill: widget-implementation') + 1)
  expect(texts.some((text: string) => text.startsWith('walk: widget') || text.startsWith('↳ fixing'))).toBe(false)
})

test('a skill run with no start time draws no empty detail line', async ($, on) => {
  const untimed = { ...SKILL_ROW, station: 'the widgets sing', started_at: '' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [untimed] })
  expect(texts.at(-1)).toBe('skill: widget-implementation')
  expect(texts).not.toContain('')
})

test('a second row on one walk reads beneath the walk line with its own ages', async ($, on) => {
  const stepStarted = new Date(THREE_HOURS_LATER - 5 * 60_000).toISOString()
  const walking = { ...RUNNING_ROW, launcher: 'chain-change', project: 'widgets', key: OPEN_WALK.key, step: 'implementation', step_started_at: stepStarted }
  const alongside = { ...RUNNING_ROW, project: 'widgets', key: OPEN_WALK.key, started_at: new Date(THREE_HOURS_LATER - 60 * 60_000).toISOString(), step: 'readme-status', step_started_at: new Date(THREE_HOURS_LATER - 2 * 60_000).toISOString() }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [walking, alongside], routes: [ROUTE] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('build-idea · running total 1h · readme-status for 2m')).toBe(at('● the-first-widget · running total 3h · implementation for 5m') + 1)
})

test('a row on a sealed walk of the current station reads on that walk line, not as a line of its own', async ($, on) => {
  const [reached, current, ...ahead] = ROUTE.stations
  const sealed = { ...OPEN_WALK, state: 'sealed' }
  const closing = { ...current!, walks: [sealed] }
  const route = { ...ROUTE, stations: [reached, closing, ...ahead] }
  const row = { ...RUNNING_ROW, project: 'widgets', key: OPEN_WALK.key, walk: 'the first widget', step: 'close the reached station' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [row], routes: [route] })
  expect(texts).toContain('✓ the-first-widget · sealed · running total 3h · close the reached station')
  expect(texts).not.toContain('walk: the first widget')
})

// --- a closed station: its walks hidden, but for one a row is still on ---------------------------

// The route after its station closed: the item reached, its walk sealed, no station open.
const CLOSED_ROUTE = {
  ...ROUTE,
  stations: ROUTE.stations.map(stop =>
    stop.state === 'current'
      ? { ...stop, state: 'reached', walks: stop.walks.map(walk => ({ ...walk, state: walk.state === 'open' ? 'sealed' : walk.state })) }
      : stop),
}
const CLOSING_ROW = { ...RUNNING_ROW, project: 'widgets', station: 'the widgets ship', walk: 'the first widget', key: OPEN_WALK.key, step: 'readme-status' }

// The cells a walk sits further in than its station.
const WALK_INDENT = 4

// Each row of the pane as its indent and its text.
const indentedAt = async ($: any, on: any, board: object) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(board))
  await startSession($)
  await clock.settle()
  const ui = await mountPane($, 'terminal')
  const boxes = (await ui.findAll({ type: 'Box' })) as any[]
  await ui.unmount()
  return boxes.filter(box => box.props.paddingLeft !== undefined).map(box => [box.props.paddingLeft, box.text] as const)
}

test('a row still on the walk of a closed station reads on that walk, under the station as a tree', async ($, on) => {
  const rows = await indentedAt($, on, { ...EMPTY_BOARD, running: [CLOSING_ROW], routes: [CLOSED_ROUTE] })
  const station = rows.find(([, text]) => text === '✓ the-widgets-ship')
  const walk = rows.find(([, text]) => text === '✓ the-first-widget · sealed · running total 3h · readme-status')
  expect(station).toBeDefined()
  expect(rows.indexOf(walk ?? [0, ''])).toBe(rows.indexOf(station ?? [0, '']) + 1)
  expect(walk?.[0]).toBe((station?.[0] ?? 0) + WALK_INDENT)
  expect(rows.some(([, text]) => /^(station|walk): /.test(text))).toBe(false)
})

test("a closed station's other walks stay hidden while a row is on one of them", async ($, on) => {
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [CLOSING_ROW], routes: [CLOSED_ROUTE] })
  expect(texts).not.toContain('✗ an-earlier-try · dropped')
  expect(texts).not.toContain('✓ the-boxes · sealed')
})

test('a closed station no row is on shows none of its walks', async ($, on) => {
  const elsewhere = { ...RUNNING_ROW, project: 'widgets', key: '' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [elsewhere], routes: [CLOSED_ROUTE] })
  expect(texts).toContain('✓ the-widgets-ship')
  expect(texts.some((text: string) => text.includes('the-first-widget') || text.includes('the-boxes'))).toBe(false)
})

test('a row on the walk of a parked station reads under it too', async ($, on) => {
  const parked = { ...CLOSED_ROUTE, stations: CLOSED_ROUTE.stations.map(stop => stop.name === 'the-widgets-ship' ? { ...stop, state: 'parked' } : stop) }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, running: [CLOSING_ROW], routes: [parked] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('✓ the-first-widget · sealed · running total 3h · readme-status')).toBe(at('‖ the-widgets-ship · parked') + 1)
})

test("a running row on the current station's walk keeps the tree over a waiting row on a closed station's walk", async ($, on) => {
  const [reached, current, ...ahead] = ROUTE.stations
  const route = { ...ROUTE, stations: [{ ...reached!, walks: [{ name: 'made-the-first', key: 'unit-made-the-first', state: 'sealed' }] }, current, ...ahead] }
  const owed = { ...WAITING_ROW, launcher: 'build-idea', key: 'unit-made-the-first', walk: 'made the first', status: 'owner-owed' }
  const walking = { ...RUNNING_ROW, launcher: 'chain-change', project: 'widgets', key: OPEN_WALK.key, step: 'implementation' }
  const texts = await routeTexts($, on, { ...EMPTY_BOARD, waiting: [owed], running: [walking], routes: [route] })
  const at = (text: string) => texts.indexOf(text)
  expect(at('● the-first-widget · running total 3h · implementation')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(at('▸ the-widgets-ship')).toBeGreaterThan(at('RUNNING NOW (1)'))
  expect(texts).not.toContain('walk: the first widget')
})
