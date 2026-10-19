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
  step: 'design',
  status: 'halted',
  reason: 'the run stopped before it made a marker',
  started_at: STARTED_AT,
}
const RUNNING_ROW = {
  launcher: 'build-idea',
  project: 'gadgets',
  seed: '',
  station: '',
  walk: 'the gadgets sing',
  step: '',
  status: '',
  reason: '',
  started_at: STARTED_AT,
}
const BOARD = { instance: 'sample-instance', waiting: [WAITING_ROW], running: [RUNNING_ROW] }
const EMPTY_BOARD = { instance: 'sample-instance', waiting: [], running: [] }
const NO_INSTANCE = { instance: null, waiting: [], running: [] }

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
    expect(at(/^chain-change · halted · design/)).toBeGreaterThanOrEqual(0)
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
    expect(at('chain-change · halted · design · 3h ago')).toBe(at('walk: the first widget') + 1)
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
  expect(texts.at(-1)).toBe('build-idea · 3h ago')
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

test('a row shows how long ago its walk started', async ($, on) => {
  const clock = mock.clock(on, { now: THREE_HOURS_LATER })
  standIn(on, () => prints(BOARD))
  await startSession($)
  await clock.settle()

  for (const surface of SURFACES) {
    const ui = await mountPane($, surface)
    const waitingDetail = /^chain-change · halted · design · 3h ago$/
    expect(await ui.find({ type: 'Text', text: waitingDetail })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^build-idea · 3h ago$/ })).toBeDefined()
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
  expect(await ui.find({ type: 'Text', text: /build-idea · 59m ago$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /build-idea · 47h ago$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /build-idea · 2d ago$/ })).toBeDefined()
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
