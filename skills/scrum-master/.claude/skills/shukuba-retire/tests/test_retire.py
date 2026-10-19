"""retire.py's resolve, over a real journey under `tmp_path` — the station a close acts on is
whatever this prints, so every refusal is a case here."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import retire  # noqa: E402

PROJECT = "demo"
STATION = "2026-10-12_the-first-leg"
OTHER = "2026-10-13_the-second-leg"


def _shukuba(root: Path) -> Path:
    shukuba = root / "system" / "projects" / PROJECT / "journey" / "shukuba"
    for folder in (shukuba / "trail", shukuba / "parked"):
        folder.mkdir(parents=True)
    (shukuba / "README.md").write_text("# shukuba\n")
    return shukuba


def _station(folder: Path, stem: str) -> Path:
    path = folder / f"{stem}.md"
    path.write_text(f"# {stem}\n")
    return path


def _refusal(tmp_path: Path, station: str = "") -> str:
    with pytest.raises(retire.Refused) as refused:
        retire.resolve(tmp_path, PROJECT, station)
    return str(refused.value)


def test_the_one_station_at_the_root_is_found_from_the_project_alone(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)
    _station(shukuba / "trail", OTHER)

    assert retire.resolve(tmp_path, PROJECT) == shukuba / f"{STATION}.md"


def test_a_named_station_at_the_root_is_found(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)

    assert retire.resolve(tmp_path, PROJECT, STATION) == shukuba / f"{STATION}.md"


def test_a_named_station_may_carry_its_md_suffix(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)

    assert retire.resolve(tmp_path, PROJECT, f"{STATION}.md") == shukuba / f"{STATION}.md"


def test_an_empty_root_refuses_naming_the_folder_it_listed(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba / "trail", STATION)

    refusal = _refusal(tmp_path)

    assert "no station is open" in refusal
    assert str(shukuba) in refusal


def test_two_stations_at_the_root_refuse_naming_both(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)
    _station(shukuba, OTHER)

    refusal = _refusal(tmp_path)

    assert "more than one station" in refusal
    assert f"{STATION}.md" in refusal and f"{OTHER}.md" in refusal


def test_two_stations_at_the_root_refuse_even_when_one_is_named(tmp_path):
    """A root holds one station; two is a journey nobody may close from by choosing one."""
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)
    _station(shukuba, OTHER)

    refusal = _refusal(tmp_path, STATION)

    assert "more than one station" in refusal
    assert f"{STATION}.md" in refusal and f"{OTHER}.md" in refusal


def test_a_named_name_that_is_not_a_dated_stem_refuses(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)

    assert "a station's dated stem" in _refusal(tmp_path, "the-first-leg")


def test_a_named_station_already_in_trail_refuses_saying_it_is_closed(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba / "trail", STATION)

    assert "already closed" in _refusal(tmp_path, STATION)


def test_a_named_station_in_parked_refuses_saying_it_is_parked(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba / "parked", STATION)

    assert "parked" in _refusal(tmp_path, STATION)


def test_a_named_station_not_on_disk_refuses_naming_what_the_root_holds(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, OTHER)

    refusal = _refusal(tmp_path, STATION)

    assert f"no station {STATION}" in refusal
    assert f"{OTHER}.md" in refusal


def test_a_named_station_that_is_a_path_refuses(tmp_path):
    shukuba = _shukuba(tmp_path)
    _station(shukuba / "trail", STATION)

    assert "a station's dated stem" in _refusal(tmp_path, f"trail/{STATION}")


def test_a_project_with_no_shukuba_refuses(tmp_path):
    assert "no shukuba" in _refusal(tmp_path)


def test_main_prints_the_path_from_the_root_and_exits_zero(tmp_path, capsys):
    shukuba = _shukuba(tmp_path)
    _station(shukuba, STATION)

    code = retire.main(["--root", str(tmp_path), "--project", PROJECT, "resolve"])

    assert code == 0
    assert capsys.readouterr().out == (
        f"system/projects/{PROJECT}/journey/shukuba/{STATION}.md\n")


def test_main_prints_a_refusal_and_exits_one(tmp_path, capsys):
    _shukuba(tmp_path)

    code = retire.main(["--root", str(tmp_path), "--project", PROJECT, "resolve",
                        "--station", STATION])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert captured.err.startswith("REFUSED: ")
