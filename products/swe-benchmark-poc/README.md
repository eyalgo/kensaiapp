# swe-benchmark-poc — ten issues, worked to a sealed patch

Ten issues from the public benchmark SWE-bench Verified, chosen by Eyal from those KensaiApp worked on
2026-10-10 and 2026-10-11, before any release. Each shows KensaiApp carrying a change from an issue to a
sealed patch, in a repository someone else wrote. It was given the repository as it stood before the
issue was fixed, and the issue's text. Nothing else from the benchmark was given: not its fix, not its
tests, not the issue's comments.

How the project is set up is its card, `system/projects/swe-benchmark-poc/project.md`. Each issue's
change unit is under `system/projects/swe-benchmark-poc/journey/tobiishi/trail/`: the request, the
spec, the design, the developer's instruction, each step's audit findings and the integrity report.
Three edits were made for publication: the issue's text is replaced by its link and a summary, a path
on the machine it ran on reads `<the issue's clone>`, and a pointer to the project the issue first ran
in reads as this project, whose `doctrine/ai_responsibility.md` § 1 holds the same rules.

Each folder here holds the sealed change as `patch.diff`, against the commit named below, and
`LICENSE.upstream`, the licence of the repository the patch changes. The patch is offered under that
licence.

| Issue | The issue | Base commit | Change unit |
|---|---|---|---|
| `astropy__astropy-12907` | https://github.com/astropy/astropy/issues/12906 | `d16bfe05a744909de4b27f5875fe0d4ed41ce607` | `2026-10-11_astropy-12907` |
| `django__django-10097` | https://code.djangoproject.com/ticket/29528 | `b9cf764be62e77b4777b3a75ec256f6209a57671` | `2026-10-10_django-10097` |
| `django__django-10880` | https://code.djangoproject.com/ticket/30120 | `838e432e3e5519c5383d12018e6c78f8ec7833c1` | `2026-10-11_django-10880` |
| `matplotlib__matplotlib-14623` | https://github.com/matplotlib/matplotlib/issues/14615 | `d65c9ca20ddf81ef91199e6d819f9d3506ef477c` | `2026-10-11_matplotlib-14623` |
| `psf__requests-1142` | https://github.com/psf/requests/issues/1051 | `22623bd8c265b78b161542663ee980738441c307` | `2026-10-11_requests-1142` |
| `pytest-dev__pytest-10051` | https://github.com/pytest-dev/pytest/issues/9877 | `aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a` | `2026-10-11_pytest-10051` |
| `scikit-learn__scikit-learn-10297` | https://github.com/scikit-learn/scikit-learn/issues/10284 | `b90661d6a46aa3619d3eec94d5281f5888add501` | `2026-10-10_scikit-learn-10297` |
| `sphinx-doc__sphinx-10435` | https://github.com/sphinx-doc/sphinx/issues/10434 | `f1061c012e214f16fd8790dec3c283d787e3daa8` | `2026-10-11_sphinx-10435` |
| `sympy__sympy-11618` | https://github.com/sympy/sympy/issues/11617 | `360290c4c401e386db60723ddb0109ed499c9f6e` | `2026-10-10_sympy-11618` |
| `sympy__sympy-12096` | https://github.com/sympy/sympy/issues/12092 | `d7c3045115693e887bcd03599b7ca4650ac5f2cb` | `2026-10-11_sympy-12096` |

## Working a new issue

**Which issue.** A new issue is picked by a rule that uses only an issue's `repo` and `instance_id`,
so no one picks an issue knowing how it turns out. It reads the benchmark's published copy
(`princeton-nlp/SWE-bench_Verified`, split `test`, revision
`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`), the copy the ten were picked from:

1. The repositories are ordered by how many of the 500 issues they hold, most first; a tie by name.
2. The five largest each give one issue: the first, sorted as text, that has not been worked, graded
   or had its benchmark fix read on the owner's machine.
3. They run in the order of step 1.

**Where the run works.** The card's `Product path:` names this folder of patches, but a run has to
change the issue's own repository. So for the run only, the card names a clean clone of the issue's
repository at its base commit, and `Test command:` names that issue's tests. When the change has
sealed, its patch is copied here beside the upstream licence, and the card goes back to naming this
folder. KensaiApp itself is not changed for this.

**Where it lands.** A new issue's change unit lands in `journey/tobiishi/trail/` like the ten, and is
listed here under its own heading, apart from the ten.
