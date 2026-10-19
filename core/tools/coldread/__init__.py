"""coldread — the stack manifest parser.

One responsibility now: parse and validate a skill's `stack.json` (`manifest.py`) — the ordered
set of substance files a cold read is run over. `<CORE>/launchers/cold-read/launcher.sh` reads it
to decide how many blind readers to open and what each one's subject is.

The package was three modules while kaizen step 2 was an automated chain: `outcome.py` typed a
per-link sentinel and `chain.py` sequenced the links. Step 2 is four owner-driven moves now
(`<CORE>/doctrine/kaizen/skills.md` § Running the cold-read), with no link to sequence and no
outcome to advance on, so both are retired and the manifest is what survives them. stdlib only —
no third-party import in this package.
"""

__version__ = "2.0.1"
