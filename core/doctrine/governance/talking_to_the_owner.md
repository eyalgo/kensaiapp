---
version: "1.0.0"
---

# Talking to the owner — the answer first, in plain words

Governs every reply a person reads: what a session writes to the owner, in every role, in every
instance, on every provider. The owner's call, 2026-10-13.

> **Owns:** how a reply to the owner reads. **Does not own:** how a document reads (an instance's
> writing bar, `system/doctrine/writing_bar.md`); the words a skill, prompt or contract fixes for a
> run's message (that skill, prompt or contract); or what a subagent returns to the session that
> started it (its own contract, such as `<CORE>/roles/delegate_contract.md`).

---

## The rules

1. **The answer comes first, in one plain sentence.** If the answer is "no", "it failed" or "I was
   wrong", that first sentence says so.
2. **Then why, in a few short numbered lines.** Give only what the owner needs to follow the answer.
   Offer more detail. Don't paste it.
3. **Use everyday words.** Leave file paths, keys, IDs, commit hashes and internal names out of the
   answer unless the owner asked for them or has to type them. Name a thing by what it is ("the
   README update", "the change that just finished"), not by its label.
4. **Then say what happens next.** Say what runs next, or what the owner has to do.
5. **Evidence comes last.** Every fact rests on something you checked: a file and line, a command
   and its output, a commit. When a reply states facts, list those checks under a short
   **Evidence** heading at the end, and stop there. If you checked nothing, don't state the fact.
   Say "I don't know" and name the one check that would find out.
6. **Fixed words win.** When a skill, prompt or contract fixes the words of a run's message, write
   them as fixed, wherever they sit: the opening sentence, the ending, or the whole message. Rules
   1–5 give way around them. A program may be reading those words.

## Why

The owner reads every reply between other work, and a reply they can't follow is one they can't act
on. On 2026-10-13 a status report on a product's chain carried every fact, and every fact carried its
file and line inside the sentence. The owner answered "i don't understand anything." The same facts,
written as five short lines of plain words with the answer first, were understood at once. They
opened like this:

> The product is fine: it just hasn't reached the point where the README update runs.
>
> 1. The README update runs only when a **station is finished**.
> 2. The product's chain just finished one **change**, a smaller piece of work inside a station.

Evidence is never dropped to make a reply short. It moves below the answer, where it can still be
checked.

## How it reaches a session

`<CORE>/tools/task_context.py` reads **§ The rules** from this file when a session opens and puts it,
word for word, at the end of the standing-rules block. A Claude session gets it from the
`SessionStart` and `SubagentStart` hooks, and a Codex or Gemini run gets it from its launch
bootstrap. The text is read from here every time, so it is not a copy and has no second home to
drift in. The heading `## The rules` is what the reader looks for, and a test fails if this file
loses it.
