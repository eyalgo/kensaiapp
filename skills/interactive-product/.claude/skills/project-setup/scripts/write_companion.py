#!/usr/bin/env python3
"""write_companion.py — render one round-0 companion from its template and the owner's answers.

project-setup interviews the owner, then hands each document's answers to this script, which
writes the companion `product-prd` or `project-agari` reads on its first run. The template
owns the shape, so the shape is read from it rather than copied here:

- the frontmatter and the template-metadata comment are dropped, as for any instantiated
  companion (the template says so on its own line 4);
- the title's `<product>` / `<project>` token becomes the project name;
- every `## ` bucket heading is kept, and every bucket body is dropped — the placeholder
  stanzas would otherwise read as items;
- bucket 1 receives one `### 1.N` item per answer, its slot labels taken from the template's
  own `### 1.1` stanza: `Answer` holds the owner's answer, `Why it matters` the reason the
  skill gives, and any other slot the interview's provenance line.

Usage:
    write_companion.py --template <template.md> --out <companion.md> --name <project>
                       --answers <answers.json>

answers.json is a list of {"question": str, "why": str, "answer": str}. The output must not
exist — a companion already on disk belongs to a round in progress, and is never overwritten.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROUND_ZERO = ("> **Round 0.** Written by `project-setup` from the owner's interview — every "
              "answer below is the owner's own, given before any draft existed.")
PROVENANCE = "Asked of the owner in the project-setup interview; answered there."


def _strip_metadata(text: str) -> str:
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        text = text[end + len("\n---\n"):]
    lines = text.splitlines()
    if lines and lines[0].startswith("<!-- The version above is template-file metadata"):
        lines = lines[1:]
    return "\n".join(lines).lstrip("\n")


def _slot_labels(section_one: list[str]) -> list[str]:
    labels = []
    for line in section_one:
        m = re.match(r"^- \*\*(.+?):\*\*", line)
        if m:
            labels.append(m.group(1))
        elif labels and line.startswith("#"):
            break
    if "Answer" not in labels:
        raise ValueError("the template's bucket 1 stanza has no Answer slot")
    return labels


def _item(number: int, entry: dict, labels: list[str]) -> list[str]:
    out = [f"### 1.{number} {entry['question'].strip()}"]
    for label in labels:
        if label == "Answer":
            value = entry["answer"].strip()
        elif label == "Why it matters":
            value = entry["why"].strip()
        else:
            value = PROVENANCE
        out.append(f"- **{label}:** {value}")
    return out + [""]


def render(template: str, name: str, answers: list[dict]) -> str:
    lines = _strip_metadata(template).splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts or not lines[starts[0]].startswith("## 1."):
        raise ValueError("the template has no '## 1.' bucket")
    preamble = lines[:starts[0]]
    preamble[0] = re.sub(r"<(product|project)>", name, preamble[0])
    if not preamble[0].startswith("# "):
        raise ValueError("the template does not open with its title")
    out = [preamble[0], "", ROUND_ZERO] + preamble[1:]
    bounds = starts + [len(lines)]
    for n, (start, end) in enumerate(zip(bounds, bounds[1:])):
        out += [lines[start], ""]
        if n == 0:
            labels = _slot_labels(lines[start:end])
            for number, entry in enumerate(answers, 1):
                out += _item(number, entry, labels)
    return "\n".join(out).rstrip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--answers", required=True)
    args = ap.parse_args()

    if os.path.exists(args.out):
        print(f"error: {args.out} already exists — a companion on disk belongs to a round in "
              "progress; nothing written.", file=sys.stderr)
        return 3
    with open(args.answers, encoding="utf-8") as fh:
        answers = json.load(fh)
    if not answers or not all({"question", "why", "answer"} <= set(a) for a in answers):
        print("error: answers must be a non-empty list of {question, why, answer}",
              file=sys.stderr)
        return 2
    if any(not a["answer"].strip() for a in answers):
        print("error: an answer is empty — an unanswered item is the run's to raise, not "
              "round 0's", file=sys.stderr)
        return 2
    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()
    try:
        text = render(template, args.name, answers)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
