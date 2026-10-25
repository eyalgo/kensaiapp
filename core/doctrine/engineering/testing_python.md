---
version: "2.3.0"
name: testing-python
description: Python implementation of testing_doctrine.md. Tooling and file conventions for layers 1–6. Layer 7 is answered elsewhere.
---

# Testing Doctrine — Python

Implements [testing_doctrine.md](testing_doctrine.md). Python-specific tooling and layout.

---

## Layers 1–5

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 1 — Unit | pytest | `tests/test_<domain>.py` | `pytest tests/` |
| 2 — Integration | pytest + `tmp_path` / real adapter | `tests/test_<persistence>.py` | `pytest tests/` |
| 3 — Application | pytest | `tests/test_<application>.py` | `pytest tests/` |
| 4 — UI | no standing tool — see the rule below | `tests/ui/` | `pytest tests/` |
| 5 — End-to-End | pytest | `tests/e2e/` | `pytest tests/e2e/` |

Layers 1–4 share a single `pytest tests/` invocation (excluding `e2e/`). Layer 5 runs separately.

---

## Rules

- **Layer 5 lives in `tests/e2e/`.** Separate invocation so layers 1–4 can run fast without full-system overhead.
- **Layer 4 has no standing Python tool.** Most Python products in this system are CLIs and omit the layer entirely with rationale in `docs/nfdr.md`, per `testing_doctrine.md`. A Python product that *does* have a UI records its component-test tool in `docs/nfdr.md` § 9 — this overlay does not pick one, because there is no single Python answer to pick.
- **The seam is a hand-written fake passed to the constructor — not `monkeypatch.setattr` on the module under test.** `testing_doctrine.md` § *Layers 1–5* states the rule; in Python it reads: one plain class per port, each recording what it received, wired through the unit's constructor by a small helper, and asserted on by that record. `<CORE>/tools/test_chain.py` is the worked file — the fakes at `:24-116`, the wiring helper `build()` at `:164`, and `:206`, `assert processes.launched == [producer("product-fdr")]`, on the exact ordered `argv` the injected process port received. Its own header states the rule and why it is possible (`:11-12`, *"Nothing here monkeypatches the module under test. Every collaborator the engine uses is handed to it through its constructor"*). The shape that makes it possible is `languages/python/conventions.md` § *Constructs*, not this file's.
- **A test that needs a normal user skips when it runs as root.** A gate's container runs the suite as root, as the official `python` image and a CI's container jobs do (`languages/python/environment.md` § Provisioning). Root reads a file whatever its mode, so a test whose subject is a file it cannot open or a folder it cannot list skips that part when `os.geteuid() == 0`, with a reason saying so, and runs it in full anywhere else. A fake uid passed to the code under test does not count: the check reads the real process's user.
- **Measured 2026-09-01, that file is the exception rather than the corpus's habit**, which is why the rule above is stated rather than assumed: `grep -rE 'monkeypatch\.(setattr|setenv|delenv|delattr|chdir|syspath_prepend)' core/tools/ core/launchers/ .claude/hooks/ | wc -l` returns **104** call sites, **93** of them `setattr`, spread over ten of the **52** test files under those roots plus `core/tools/conftest.py`. `monkeypatch.setenv` for the environment a process inherits is not what this rule is about; `monkeypatch.setattr` standing in for a seam the unit does not offer is.

---

## Layer 6 — Architecture

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 6 — Architecture | pytest | `tests/architecture/test_<property>.py` | `pytest tests/architecture` |

**pytest, and no new dependency — the packet author's call, 2026-08-30.** A layer-6 rule asserts a
property over *every* module rather than the behaviour of one, and that is an assertion like any
other: it walks the tree, reads what it finds, and fails with the site it found. `assert` and the
standard library carry it, so naming an architecture-testing library here would push a dependency
decision into every Python product, which `toolchain.md` § *Adding one* makes the product's call and
not this packet's. Same reasoning the JavaScript packet gives for answering layer 6 with `node:test`.

**Read off the repo rather than reasoned.** This instance's own layer-6 tests are exactly this shape
— `core/tools/test_keep_awake_binding.py` and `core/tools/test_agent_id_handover.py` are plain pytest
asserting a property over every file on disk. The shell packet cites them as *its* layer 6 because
their **subject** is shell; their **tool** is this one.

**Enumerate from disk, never from a list.** `test_keep_awake_binding.py` states the reason in its own
header: *"a list of nine is a list that goes stale the first time a tenth launcher is written by
copying a ninth. Every check here walks the tree, so a new site is held to the rule the day it lands
and nobody has to remember to add it here."* A layer-6 test that reads a hardcoded list is a layer-1
test wearing layer 6's name.

**Where the rule itself lives.** The *content* of a layer-6 rule — which module may import which — is
the product's, in `docs/nfdr.md` § 1.2, and the entry there names this layer in its `verified by:`
tail. This table says only what runs it. A product that wants a dedicated contract library instead
(import-linter and pytest-archon are the standing options) records that in `docs/nfdr.md` § 9 as a
toolchain decision, and its § 1.2 entries are unaffected.

## Layer 7 — Specification

**Not answered here.** Layer 7 is BDD scenarios derived from a product's FDR, and **nothing in this
system produces them yet** — what will is the foundation tier's, not this packet's. A Python product
writing them today records its runner in `docs/nfdr.md` § 9.
