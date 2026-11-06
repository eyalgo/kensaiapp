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


# --- the hold: an open Raised-from-downstream item on the SDD's companion ---------------------

TRIPLE = f"{PROJECT} · nemawashi · {SEED}"
SPLIT = "5.1 split tree-refresh and its checks"
PLACEHOLDER = "<the 根回し Nemawashi seed this item waits on, as `<project> · nemawashi · <seed>`>"
NEXT = opener.Next(PROJECT, SEED, 2, "second-leg", "second-leg — the second thing holds", None)
ONE_ITEM = (
    "records-owed — SDD_open_issues.md holds an open Raised from downstream item tracked by "
    f"{TRIPLE}, and no station of that seed opens until it has folded: "
)
MANY_ITEMS = (
    "records-owed — SDD_open_issues.md holds open Raised from downstream items tracked by "
    f"{TRIPLE}, and no station of that seed opens until they have folded: "
)


def _item(heading: str = SPLIT, tracked: str | None = TRIPLE, answer: str | None = None) -> str:
    lines = [f"### {heading}", "", "- **Raised by:** development-specs"]
    if tracked is not None:
        lines.append(f"- **Tracked by:** {tracked}")
    if answer is not None:
        lines.append(f"- **Answer:** {answer}")
    return "\n".join(lines) + "\n"


def _companion(raised: str = "", other: str = "") -> str:
    return (
        "# SDD open issues\n\n"
        f"## 1. Open issues\n\n{other}\n"
        f"## 5. Raised from downstream — items the cut could not fold\n\n{raised}\n"
        "## 6. Slices\n\nnothing here\n"
    )


def _product(root: Path, companion: str | None, *, sdd: bool = True, card: str | None = None,
             where: str = "products/demo") -> Path:
    """The project's card and a product under `root`, with the SDD and companion it is given."""
    card_dir = root / "system" / "projects" / PROJECT
    card_dir.mkdir(parents=True, exist_ok=True)
    default_card = f"# Project Context\n\n**Product path:** {where}\n**Type:** software\n"
    (card_dir / "project.md").write_text(card if card is not None else default_card)
    docs = root / where / "docs" if not where.startswith("/") else Path(where) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    if sdd:
        (docs / "SDD.md").write_text("# SDD\n")
    if companion is not None:
        (docs / "SDD_open_issues.md").write_text(companion)
    return docs


def _hold(root: Path, home: str = "/nonexistent-home") -> None:
    opener.hold(root, NEXT, files=opener.Files(), home=home)


def _refusal(root: Path, home: str = "/nonexistent-home") -> str:
    with pytest.raises(opener.Refused) as refused:
        _hold(root, home)
    return str(refused.value)


def test_hold_refuses_with_the_records_owed_reason_naming_the_heading(tmp_path):
    _product(tmp_path, _companion(_item()))
    assert _refusal(tmp_path) == ONE_ITEM + SPLIT


def test_hold_lists_every_open_item_in_file_order(tmp_path):
    _product(tmp_path, _companion(_item() + "\n" + _item("5.2 untracked", tracked=None) + "\n"
                                  + _item("5.3 move the gate")))
    assert _refusal(tmp_path) == MANY_ITEMS + f"{SPLIT}; 5.3 move the gate"


def test_hold_counts_a_tracked_by_value_in_backticks(tmp_path):
    _product(tmp_path, _companion(_item(tracked=f"`{TRIPLE}`")))
    assert _refusal(tmp_path) == ONE_ITEM + SPLIT


def test_hold_counts_an_item_whose_answer_is_filled_in_and_still_present(tmp_path):
    _product(tmp_path, _companion(_item(answer="cut it at the tree refresh")))
    assert _refusal(tmp_path) == ONE_ITEM + SPLIT


def test_hold_ignores_an_item_tracked_by_a_longer_seed_name(tmp_path):
    _product(tmp_path, _companion(_item(tracked=f"{TRIPLE}-two")))
    _hold(tmp_path)


def test_hold_ignores_an_item_tracked_by_another_seed(tmp_path):
    other_seed = f"{PROJECT} · nemawashi · 2026-07-23_another-idea"
    _product(tmp_path, _companion(_item(tracked=other_seed)))
    _hold(tmp_path)


def test_hold_ignores_a_tracked_item_outside_the_raised_from_downstream_section(tmp_path):
    _product(tmp_path, _companion(other=_item()))
    _hold(tmp_path)


def test_hold_ignores_a_tracked_item_in_a_section_after_the_raised_from_downstream_one(tmp_path):
    _product(tmp_path, _companion() + "\n" + _item())
    _hold(tmp_path)


def test_hold_ignores_a_tracked_by_value_wholly_inside_angle_brackets(tmp_path):
    _product(tmp_path, _companion(_item(tracked=f"<{TRIPLE}>")))
    _hold(tmp_path)


def test_hold_ignores_a_tracked_by_placeholder(tmp_path):
    _product(tmp_path, _companion(_item(tracked=PLACEHOLDER)))
    _hold(tmp_path)


def test_hold_ignores_an_item_with_no_tracked_by_line(tmp_path):
    _product(tmp_path, _companion(_item(tracked=None)))
    _hold(tmp_path)


def test_hold_ignores_a_commented_out_item(tmp_path):
    _product(tmp_path, _companion(f"<!--\n{_item()}-->\n"))
    _hold(tmp_path)


def test_hold_ignores_a_companion_with_no_raised_from_downstream_section(tmp_path):
    _product(tmp_path, f"# SDD open issues\n\n## 1. Open issues\n\n{_item()}\n## 6. Slices\n")
    _hold(tmp_path)


def test_hold_returns_when_there_is_no_companion_file(tmp_path):
    _product(tmp_path, None)
    _hold(tmp_path)


def test_hold_returns_when_the_product_has_no_sdd_though_a_companion_exists(tmp_path):
    _product(tmp_path, _companion(_item()), sdd=False)
    _hold(tmp_path)


BLANK_CARD = "# Project Context\n\n**Product path:** <blank>   <!-- none -->\n"


@pytest.mark.parametrize("card", [None, BLANK_CARD], ids=["no card", "blank path"])
def test_hold_returns_when_there_is_no_card_or_the_product_path_is_blank(tmp_path, card):
    _product(tmp_path, _companion(_item()))
    project_md = tmp_path / "system" / "projects" / PROJECT / "project.md"
    if card is None:
        project_md.unlink()
    else:
        project_md.write_text(card)
    _hold(tmp_path)


@pytest.mark.parametrize(
    "value",
    ["../prod", "~prod", "products/demo <!-- a note --> and then more"],
    ids=["leaves the instance", "stray tilde", "comment that does not end the line"],
)
def test_hold_returns_when_the_product_path_is_one_the_parser_refuses(tmp_path, value):
    # a product the value would reach if it were read, so a refusal here could only be the hold's
    instance = tmp_path / "instance"
    (tmp_path / "prod").mkdir()
    _product(tmp_path, _companion(_item()), where="prod")
    card = f"**Product path:** {value}\n"
    _product(instance, _companion(_item()), where="products/demo", card=card)
    _hold(instance, home=str(tmp_path))


def test_hold_ignores_an_sdd_that_is_a_directory(tmp_path):
    docs = _product(tmp_path, _companion(_item()), sdd=False)
    (docs / "SDD.md").mkdir()
    _hold(tmp_path)


def test_hold_reads_the_product_past_a_trailing_comment_on_the_card_field(tmp_path):
    _product(tmp_path, _companion(_item()),
             card="**Product path:** products/demo   <!-- the product's code and docs -->\n")
    assert _refusal(tmp_path) == ONE_ITEM + SPLIT


def test_hold_reads_an_absolute_product_path(tmp_path):
    instance = tmp_path / "instance"
    product = tmp_path / "elsewhere" / "demo"
    _product(instance, None, card=f"**Product path:** {product}\n")
    (product / "docs").mkdir(parents=True)
    (product / "docs" / "SDD.md").write_text("# SDD\n")
    (product / "docs" / "SDD_open_issues.md").write_text(_companion(_item()))
    assert _refusal(instance) == ONE_ITEM + SPLIT


def test_hold_expands_a_leading_home_prefix_against_the_home_it_is_given(tmp_path):
    instance = tmp_path / "instance"
    home = tmp_path / "home"
    _product(instance, None, card="**Product path:** ~/products/demo\n")
    (home / "products" / "demo" / "docs").mkdir(parents=True)
    (home / "products" / "demo" / "docs" / "SDD.md").write_text("# SDD\n")
    (home / "products" / "demo" / "docs" / "SDD_open_issues.md").write_text(_companion(_item()))
    assert _refusal(instance, home=str(home)) == ONE_ITEM + SPLIT


@pytest.mark.parametrize("companion", [_companion(_item()), _companion()],
                         ids=["refused", "returned"])
def test_hold_writes_nothing(tmp_path, companion):
    docs = _product(tmp_path, companion)
    before = {p: p.read_bytes() for p in (docs / "SDD.md", docs / "SDD_open_issues.md")}
    try:
        _hold(tmp_path)
    except opener.Refused:
        pass
    assert {p: p.read_bytes() for p in before} == before
    assert sorted(p.name for p in docs.iterdir()) == ["SDD.md", "SDD_open_issues.md"]


# --- the hold, driven through main() ----------------------------------------------------------

HELD_LINE = f"REFUSED: {ONE_ITEM}{SPLIT}\n"


def _run(root: Path, *command: str, git: FakeGit | None = None) -> int:
    argv = ["--root", str(root), "--project", PROJECT, *command]
    return opener.main(argv, git=git or FakeGit(), today=TODAY)


def _held(root: Path) -> Path:
    """A journey whose next item is 2, and a product whose companion holds 5.1 for the seed."""
    j = _journey(root)
    _seed(j)
    _product(root, _companion(_item()))
    return j


def _record_bytes(root: Path, j: Path) -> dict[Path, bytes]:
    paths = [root / "products/demo/docs/SDD.md", root / "products/demo/docs/SDD_open_issues.md",
             j / "nemawashi" / f"{SEED}.md"]
    return {path: path.read_bytes() for path in paths}


def _fold_by_removing_the_item(root: Path) -> None:
    (root / "products/demo/docs/SDD_open_issues.md").write_text(_companion())


def _fold_by_deleting_the_companion(root: Path) -> None:
    (root / "products/demo/docs/SDD_open_issues.md").unlink()


FOLDS = [_fold_by_removing_the_item, _fold_by_deleting_the_companion]
FOLD_IDS = ["item removed", "companion deleted"]


def test_check_is_refused_while_the_split_item_is_open(tmp_path, capsys):
    _held(tmp_path)
    assert _run(tmp_path, "check") == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", HELD_LINE)


def test_apply_is_refused_while_the_split_item_is_open(tmp_path, capsys):
    j = _held(tmp_path)
    station = tmp_path / "station.md"
    station.write_text(_station())
    assert _run(tmp_path, "apply", "--station", str(station)) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", HELD_LINE)
    assert _station_files(j) == [] and station.read_text() == _station()


@pytest.mark.parametrize("fold", FOLDS, ids=FOLD_IDS)
def test_the_station_opens_once_the_split_item_is_removed(tmp_path, capsys, fold):
    j = _held(tmp_path)
    station = tmp_path / "station.md"
    station.write_text(_station())
    assert _run(tmp_path, "check") == 1
    capsys.readouterr()
    fold(tmp_path)
    assert _run(tmp_path, "check") == 0
    assert capsys.readouterr().out.splitlines() == [
        f"Seed: {SEED}", "Item: 2", "Slug: second-leg", "Line: second-leg — the second thing holds"]
    assert _run(tmp_path, "apply", "--station", str(station)) == 0
    landed = "system/projects/demo/journey/shukuba/2026-09-15_second-leg.md"
    assert capsys.readouterr().out == landed + "\n"
    assert _station_files(j) == ["2026-09-15_second-leg.md"]


def test_a_parked_station_is_held_and_check_prints_no_parked_line(tmp_path, capsys):
    j = _held(tmp_path)
    _park(j)
    assert _run(tmp_path, "check") == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", HELD_LINE)
    assert "Parked:" not in captured.out


def test_take_up_is_refused_and_the_parked_station_stays(tmp_path, capsys):
    j = _held(tmp_path)
    parked = _park(j)
    content = parked.read_bytes()
    git = FakeGit()
    assert _run(tmp_path, "take-up", git=git) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", HELD_LINE)
    assert parked.read_bytes() == content
    assert not any(call[0] == "mv" for call in git.calls)


@pytest.mark.parametrize("fold", FOLDS, ids=FOLD_IDS)
def test_a_parked_station_is_taken_up_once_the_item_folds(tmp_path, capsys, fold):
    j = _held(tmp_path)
    _park(j)
    fold(tmp_path)
    assert _run(tmp_path, "take-up") == 0
    assert capsys.readouterr().out.splitlines() == [
        "system/projects/demo/journey/shukuba/parked/2026-09-02_second-leg.md",
        "system/projects/demo/journey/shukuba/2026-09-02_second-leg.md"]


def test_an_open_station_is_reported_before_the_hold(tmp_path, capsys):
    j = _held(tmp_path)
    (j / "shukuba" / "2026-09-03_open.md").write_text("")
    assert _run(tmp_path, "check") == 1
    err = capsys.readouterr().err
    assert err == "REFUSED: a station is already open: 2026-09-03_open.md\n"
    assert "records-owed" not in err


def test_the_hold_comes_before_apply_sees_a_parked_station(tmp_path, capsys):
    j = _held(tmp_path)
    _park(j)
    station = tmp_path / "station.md"
    station.write_text(_station())
    assert _run(tmp_path, "apply", "--station", str(station)) == 1
    err = capsys.readouterr().err
    assert err == HELD_LINE and "take it up" not in err


@pytest.mark.parametrize("command", [("check",), ("apply", "--station", "STATION"), ("take-up",)])
def test_a_held_run_leaves_sdd_companion_and_seed_byte_identical(tmp_path, command):
    j = _held(tmp_path)
    _park(j)
    (tmp_path / "station.md").write_text(_station())
    before = _record_bytes(tmp_path, j)
    argv = tuple(str(tmp_path / "station.md") if word == "STATION" else word for word in command)
    assert _run(tmp_path, *argv) == 1
    assert _record_bytes(tmp_path, j) == before


def test_a_product_with_no_sdd_opens_as_before(tmp_path, capsys):
    j = _journey(tmp_path)
    _seed(j)
    _product(tmp_path, _companion(_item()), sdd=False)
    assert _run(tmp_path, "check") == 0
    shown = capsys.readouterr().out.splitlines()
    assert shown[:3] == [f"Seed: {SEED}", "Item: 2", "Slug: second-leg"]


# --- code integrity: the intent's cases the cases above leave unasserted -----------------------

COMPANION_TEMPLATE = (Path(__file__).resolve().parents[6]
                      / "core/templates/product-templates/sdd_open_issues_template.md")
TEMPLATE_TRACKED_BY = (
    "<the 根回し Nemawashi seed watching this item, by its triple — "
    "`<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>"
)


@pytest.mark.parametrize(
    "card",
    ["# Project Context\n\n**Type:** software\n", "# Project Context\n\n**Product path:**\n",
     "# Project Context\n\n**Product path:**    <!-- not filled -->\n"],
    ids=["no field", "empty value", "only a comment"],
)
def test_hold_returns_when_the_card_names_no_product_path(tmp_path, card):
    # CP-869: a card whose Product path: is missing or empty names no product, so nothing holds
    _product(tmp_path, _companion(_item()), card=card)
    _hold(tmp_path)


def test_hold_reads_the_companion_templates_own_shape(tmp_path):
    # CP-870 on the real template: as stamped, its § 5.1 placeholder holds nothing; once that
    # item's Tracked by: names the seed, the item holds, under the heading the template gives it
    template = COMPANION_TEMPLATE.read_text(encoding="utf-8")
    assert TEMPLATE_TRACKED_BY in template
    docs = _product(tmp_path, template)
    _hold(tmp_path)
    (docs / "SDD_open_issues.md").write_text(template.replace(TEMPLATE_TRACKED_BY, f"`{TRIPLE}`"))
    assert _refusal(tmp_path) == (
        ONE_ITEM + "5.1 <what the SDD is missing, or what it cannot fill, in one line>")


@pytest.mark.parametrize("fold", FOLDS, ids=FOLD_IDS)
def test_check_prints_the_parked_line_once_the_item_folds(tmp_path, capsys, fold):
    # CP-877: after the fold, check prints Parked: where a parked station carries the item
    j = _held(tmp_path)
    _park(j)
    fold(tmp_path)
    assert _run(tmp_path, "check") == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "Parked: system/projects/demo/journey/shukuba/parked/2026-09-02_second-leg.md")


@pytest.mark.parametrize(
    "arrange, status, line",
    [
        (lambda j: _seed(j, name="2026-09-02_other"), "",
         f"more than one seed at the seedbed root: {SEED}.md, 2026-09-02_other.md"),
        (lambda j: (j / "tobiishi" / "2026-09-03_unit").mkdir(), "",
         "a change unit is open: 2026-09-03_unit"),
        (lambda j: _park(j, name="2026-09-04_second-leg.md") and _park(j), "",
         "more than one parked station carries 'second-leg': "
         "2026-09-02_second-leg.md, 2026-09-04_second-leg.md"),
        (lambda j: None, " M somefile\n", "the working tree is not clean"),
    ],
    ids=["two seeds", "unit open", "two parked", "not clean"],
)
@pytest.mark.parametrize("command", ["check", "take-up"])
def test_a_base_refusal_is_printed_before_the_hold(tmp_path, capsys, arrange, status, line,
                                                   command):
    # CP-875: with an open item tracked by the seed, a journey check() refuses prints that
    # refusal exactly as at the base, and no records-owed line
    arrange(_held(tmp_path))
    assert _run(tmp_path, command, git=FakeGit(status)) == 1
    assert capsys.readouterr().err == f"REFUSED: {line}\n"


def test_the_seed_whose_route_is_all_ticked_is_refused_as_at_the_base(tmp_path, capsys):
    # CP-875: a fully ticked route keeps its own refusal on a held product
    j = _journey(tmp_path)
    _seed(j, "## Stations\n\n- [x] first-leg — done\n")
    _product(tmp_path, _companion(_item()))
    assert _run(tmp_path, "check") == 1
    err = capsys.readouterr().err
    assert err.startswith("REFUSED: every item on the route is ticked")
    assert "records-owed" not in err
