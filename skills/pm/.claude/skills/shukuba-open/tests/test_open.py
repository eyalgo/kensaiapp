"""open.py's checks, through its injected git runner and date — no real repo is touched."""

import datetime
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import open as opener  # noqa: E402

PROJECT = "demo"
SEED = "2026-09-01_idea"
TODAY = lambda: datetime.date(2026, 9, 15)  # noqa: E731

ROUTE = (
    "# idea\n\n## Stations — dynamic checklist\n\n"
    "- [x] first-leg — the first thing holds\n"
    "- [ ] second-leg — the second thing holds\n"
    "- [ ] third-leg — the third thing holds\n\n"
    "## Out (later / elsewhere)\n\n- [ ] not-a-station — outside the route\n"
)


class FakeGit:
    def __init__(self, status: str = ""):
        self.status = status
        self.calls: list[list[str]] = []

    def __call__(self, root: Path, args: list[str]) -> str:
        self.calls.append(args)
        if args[0] == "status":
            return self.status
        if args[0] == "mv":
            (root / args[1]).rename(root / args[2])
        return ""


def _journey(root: Path) -> Path:
    j = root / "system" / "projects" / PROJECT / "journey"
    for d in ("nemawashi/unpicked", "nemawashi/trail", "nemawashi/drop",
              "shukuba/parked", "shukuba/trail", "tobiishi/trail"):
        (j / d).mkdir(parents=True)
    (j / "nemawashi" / "README.md").write_text("readme")
    (j / "shukuba" / "README.md").write_text("readme")
    return j


def _seed(j: Path, body: str = ROUTE, name: str = SEED) -> None:
    (j / "nemawashi" / f"{name}.md").write_text(body)


def _station(number: int = 2, seed: str = f"{PROJECT} · nemawashi · {SEED}", slug: str = "second-leg",
             parts=None) -> str:
    parts = parts if parts is not None else {
        "What it is": "The second leg.",
        "Reached when": "`python3 -c 'pass'` exits 0.",
        "Guardrail": f"- **Not here:** `{PROJECT} · nemawashi · 2026-09-02_other-idea`.",
    }
    body = "".join(f"## {name}\n\n{text}\n\n" for name, text in parts.items())
    return (
        "# 宿場 Shukuba — the second thing holds\n\n"
        f"*Item {number} on the active 根回し Nemawashi `{seed}`. Slug: `{slug}`.*\n\n"
        + body
    )


def _park(j: Path, name: str = "2026-09-02_second-leg.md", seed: str = f"{PROJECT} · nemawashi · {SEED}") -> Path:
    path = j / "shukuba" / "parked" / name
    path.write_text(_station(seed=seed))
    return path


def test_check_reads_only_the_projects_journey(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    git = FakeGit()
    opener.check(tmp_path, PROJECT, git)
    assert [c for c in git.calls if c[0] == "status"] == [
        ["status", "--porcelain", "--", str(Path("system") / "projects" / PROJECT / "journey")]]


def test_check_ignores_another_projects_edit_in_a_real_checkout(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    other = tmp_path / "products" / "other"
    other.mkdir(parents=True)
    (other / "notes.md").write_text("x")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True)
    (other / "notes.md").write_text("edited by another project's walk")
    assert opener.check(tmp_path, PROJECT, opener.run_git).slug
    (j / "nemawashi" / f"{SEED}.md").write_text(ROUTE + "\nedited\n")
    with pytest.raises(opener.Refused, match="not clean"):
        opener.check(tmp_path, PROJECT, opener.run_git)


def test_check_names_the_next_unticked_item_on_the_route(tmp_path):
    _seed(_journey(tmp_path))
    nxt = opener.check(tmp_path, PROJECT, FakeGit())
    assert (nxt.seed, nxt.number, nxt.slug, nxt.parked) == (SEED, 2, "second-leg", None)


def test_check_counts_an_indented_item(tmp_path):
    _seed(_journey(tmp_path), "## Stations\n\n  - [x] a — done\n  - [ ] b — next\n")
    assert opener.check(tmp_path, PROJECT, FakeGit()).slug == "b"


def test_check_reads_a_folder_seed(tmp_path):
    j = _journey(tmp_path)
    (j / "nemawashi" / SEED).mkdir()
    (j / "nemawashi" / SEED / "seed.md").write_text(ROUTE)
    assert opener.check(tmp_path, PROJECT, FakeGit()).number == 2


def test_check_names_a_parked_station_of_this_seed_for_the_item(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    assert opener.check(tmp_path, PROJECT, FakeGit()).parked is None
    parked = _park(j)
    assert opener.check(tmp_path, PROJECT, FakeGit()).parked == parked


@pytest.mark.parametrize("seed", ["2026-07-23_another-idea", f"{PROJECT} · nemawashi · {SEED}-two"])
def test_check_ignores_a_parked_station_of_another_seed(tmp_path, seed):
    j = _journey(tmp_path)
    _seed(j)
    _park(j, seed=seed)
    assert opener.check(tmp_path, PROJECT, FakeGit()).parked is None


def test_check_allows_a_slug_already_used_in_trail(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    (j / "shukuba" / "trail" / "2026-07-11_second-leg.md").write_text("an earlier station, same slug")
    assert opener.check(tmp_path, PROJECT, FakeGit()).slug == "second-leg"


def test_check_opens_the_next_item_with_tobiishi_trail_and_drop_only(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    (j / "tobiishi" / "drop" / "2026-09-19_x").mkdir(parents=True)
    assert opener.check(tmp_path, PROJECT, FakeGit()).slug == "second-leg"


def test_check_refuses_an_open_unit_beside_tobiishi_drop(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    (j / "tobiishi" / "drop" / "2026-09-19_x").mkdir(parents=True)
    (j / "tobiishi" / "2026-09-19_x").mkdir()
    with pytest.raises(opener.Refused, match="a change unit is open: 2026-09-19_x"):
        opener.check(tmp_path, PROJECT, FakeGit())


@pytest.mark.parametrize(
    "arrange, status, reason",
    [
        (lambda j: None, "", "no seed is active"),
        (lambda j: (_seed(j), _seed(j, name="2026-09-02_other")), "", "more than one seed"),
        (lambda j: (_seed(j), (j / "shukuba" / "2026-09-03_open.md").write_text("")), "", "already open"),
        (lambda j: (_seed(j), (j / "tobiishi" / "2026-09-03_unit").mkdir()), "", "change unit is open"),
        (lambda j: _seed(j, "# idea\n\n- [ ] loose — no route heading\n"), "", "no route section"),
        (lambda j: _seed(j, "## Stations\n\nprose only\n"), "", "lists no station"),
        (lambda j: _seed(j, "## Stations\n\n- [x] a — done\n\n## Out\n\n- [ ] b — not route\n"), "",
         "every item on the route is ticked"),
        (lambda j: _seed(j, "## Stations\n\n- [ ] 1. **product-prd** — author the PRD\n"), "",
         "names no station slug — stations-from-seed first"),
        (lambda j: (_seed(j), _park(j), _park(j, name="2026-09-04_second-leg.md")), "", "more than one parked"),
        (lambda j: _seed(j), " M somefile\n", "not clean"),
    ],
)
def test_check_refuses_a_journey_not_ready(tmp_path, arrange, status, reason):
    arrange(_journey(tmp_path))
    with pytest.raises(opener.Refused, match=reason):
        opener.check(tmp_path, PROJECT, FakeGit(status))


def test_check_refuses_an_unknown_project(tmp_path):
    with pytest.raises(opener.Refused, match="no shukuba"):
        opener.check(tmp_path, PROJECT, FakeGit())


def test_apply_lands_the_station_under_todays_date(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    git = FakeGit()
    path = opener.apply(tmp_path, PROJECT, _station(), git, TODAY)
    assert path == Path("system/projects/demo/journey/shukuba/2026-09-15_second-leg.md")
    assert (tmp_path / path).read_text() == _station()
    assert not any(c[0] == "mv" for c in git.calls)


@pytest.mark.parametrize(
    "station, reason",
    [
        (_station(number=3), "item 2"),
        (_station().replace("*Item", "Item"), "item 2"),
        (_station(seed=SEED), "name the seed as"),
        (_station(seed=f"{PROJECT} · nemawashi · {SEED}-two"), "name the seed as"),
        (_station(seed=f"other · nemawashi · {SEED}"), "name the seed as"),
        (_station(slug="third-leg"), "slug `second-leg`"),
        (_station(parts={"What it is": "w", "Guardrail": "g"}), "`## Reached when` exactly once"),
        (_station(parts={"What it is": "w", "Reached when": "", "Guardrail": "g"}), "`## Reached when` is empty"),
        (_station(parts={"What it is": "w", "Reached when": "<!-- the bar -->", "Guardrail": "g"}),
         "`## Reached when` is empty"),
        (_station(parts={"What it is": "<The work of this leg, in a few sentences.>", "Reached when": "r",
                         "Guardrail": "g"}), "`## What it is` is empty or still the template's placeholder"),
        (_station() + "## Guardrail\n\nagain\n", "`## Guardrail` exactly once"),
    ],
)
def test_apply_refuses_a_station_not_in_shape(tmp_path, station, reason):
    j = _journey(tmp_path)
    _seed(j)
    with pytest.raises(opener.Refused, match=reason):
        opener.apply(tmp_path, PROJECT, station, FakeGit(), TODAY)
    assert _station_files(j) == []


def test_apply_refuses_when_a_parked_station_carries_the_item(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    _park(j)
    with pytest.raises(opener.Refused, match="take it up"):
        opener.apply(tmp_path, PROJECT, _station(), FakeGit(), TODAY)
    assert _station_files(j) == []


def test_take_up_moves_the_parked_station_whole(tmp_path):
    j = _journey(tmp_path)
    _seed(j)
    parked = _park(j)
    content = parked.read_text()
    git = FakeGit()
    old, new = opener.take_up(tmp_path, PROJECT, git)
    assert new == Path("system/projects/demo/journey/shukuba/2026-09-02_second-leg.md")
    assert (tmp_path / new).read_text() == content and not (tmp_path / old).exists()
    assert [c[0] for c in git.calls].count("mv") == 1


def test_take_up_refuses_with_nothing_parked(tmp_path):
    _seed(_journey(tmp_path))
    git = FakeGit()
    with pytest.raises(opener.Refused, match="write one"):
        opener.take_up(tmp_path, PROJECT, git)
    assert not any(c[0] == "mv" for c in git.calls)


def test_main_prints_a_refusal_and_exits_1(tmp_path, capsys):
    _journey(tmp_path)
    assert opener.main(["--root", str(tmp_path), "--project", PROJECT, "check"], git=FakeGit()) == 1
    assert "REFUSED" in capsys.readouterr().err


def test_main_check_prints_the_item(tmp_path, capsys):
    _seed(_journey(tmp_path))
    assert opener.main(["--root", str(tmp_path), "--project", PROJECT, "check"], git=FakeGit()) == 0
    assert capsys.readouterr().out.splitlines()[:3] == [f"Seed: {SEED}", "Item: 2", "Slug: second-leg"]


def _station_files(j: Path) -> list[str]:
    return [p.name for p in (j / "shukuba").iterdir() if p.suffix == ".md" and p.name != "README.md"]
