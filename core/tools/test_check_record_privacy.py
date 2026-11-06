"""Tests for `check_record_privacy.py` — a line a commit adds to a record names no machine and no
repository address.

Every case runs the checker over a real scratch repository with a staged index, and hands it a
home folder and a login name this file made up: the checker reads them off the machine only when
`main` is given none, and no test here asks the machine who it is. The repository's address is
handed in the same way, or read off a scratch repository's own `origin`, which a test sets.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import check_record_privacy

HOME = "/Users/morgan"
LOGIN = "mlovelace"

JOURNEY_RECORD = "system/projects/tracker17/journey/tobiishi/key/halt_report.md"
MOVED_RECORD = "system/projects/tracker17/journey/tobiishi/trail/key/halt_report.md"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _scratch_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "scratch"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    return repo


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, message: str = "base") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _stage(repo: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        _write(repo, relative, text)
    _git(repo, "add", "-A")


def _check(
    repo: Path, *, home: str = HOME, login: str = LOGIN
) -> int:
    return check_record_privacy.main(
        ["--staged", "--repo", str(repo)], home=home, login=login
    )


def _check_files(
    tmp_path: Path,
    files: dict[str, str],
    capsys: pytest.CaptureFixture[str],
    *,
    home: str = HOME,
    login: str = LOGIN,
) -> tuple[int, str]:
    repo = _scratch_repo(tmp_path)
    _stage(repo, files)
    status = _check(repo, home=home, login=login)
    return status, capsys.readouterr().err


def test_a_home_path_added_to_a_journey_record_is_a_hit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = f"cache read from {HOME}/.cache/uv"

    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"clean\n{line}\n"}, capsys)

    assert status == 1
    assert f"{JOURNEY_RECORD}:2: [home-path] {line}" in err


def test_the_login_as_a_word_is_a_hit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = f"ran as {LOGIN} on port 8017"

    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"{line}\n"}, capsys)

    assert status == 1
    assert f"{JOURNEY_RECORD}:1: [login] {line}" in err


@pytest.mark.parametrize(
    "line",
    [f"x{LOGIN}", f"{LOGIN}x", f"{LOGIN}_two", f"prefix{LOGIN}suffix", f"1{LOGIN}"],
)
def test_the_login_inside_a_longer_word_is_not_a_hit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], line: str
) -> None:
    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"{line}\n"}, capsys)

    assert status == 0
    assert err == ""


def test_a_line_naming_both_is_reported_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = f"{LOGIN} wrote {HOME}/notes"

    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"{line}\n"}, capsys)

    assert status == 1
    assert f"{JOURNEY_RECORD}:1: [home-path+login] {line}" in err
    assert err.count(f"{JOURNEY_RECORD}:1:") == 1


def test_a_longer_folder_name_sharing_the_home_prefix_is_not_a_hit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, err = _check_files(
        tmp_path, {JOURNEY_RECORD: f"{HOME}-two/data and {HOME}x/data\n"}, capsys
    )

    assert status == 0
    assert err == ""


@pytest.mark.parametrize(
    "record",
    ["products/tracker17/docs/trail/prd/cycle-1.md", "docs/a.md"],
)
def test_a_docs_record_anywhere_is_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], record: str
) -> None:
    status, err = _check_files(tmp_path, {record: f"see {HOME}/x\n"}, capsys)

    assert status == 1
    assert f"{record}:1: [home-path]" in err


@pytest.mark.parametrize(
    "path",
    ["core/tools/x.py", "mydocs/a.md", "README.md", "skills/a/SKILL.md"],
)
def test_a_file_that_is_no_record_is_not_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], path: str
) -> None:
    status, err = _check_files(tmp_path, {path: f"{HOME}/x and {LOGIN}\n"}, capsys)

    assert status == 0
    assert err == ""


def test_a_made_up_home_and_the_placeholders_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = "/Users/sam/tracker17/data\n<home>/.cache/uv\n<the instance>/core\n<user>\n"

    status, err = _check_files(tmp_path, {JOURNEY_RECORD: text}, capsys)

    assert status == 0
    assert err == ""


@pytest.mark.parametrize("home", ["", "/"])
def test_an_empty_or_root_home_is_not_looked_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], home: str
) -> None:
    status, err = _check_files(
        tmp_path, {JOURNEY_RECORD: "/usr/local/bin and / and a path\n"}, capsys, home=home
    )

    assert status == 0
    assert err == ""


def test_an_empty_login_is_not_looked_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, err = _check_files(
        tmp_path, {JOURNEY_RECORD: "any words at all\n\n"}, capsys, login=""
    )

    assert status == 0
    assert err == ""


def test_the_refusal_names_the_placeholders_and_the_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"{HOME}/x\n"}, capsys)

    assert status == 1
    assert "<home>/…" in err
    assert "<the instance>/…" in err
    assert "<user>" in err
    assert "<CORE>/doctrine/governance/records_name_no_machine.md" in err


def test_every_hit_is_reported_before_the_exit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = "products/tracker17/docs/a.md"

    status, err = _check_files(
        tmp_path,
        {JOURNEY_RECORD: f"{HOME}/one\n", other: f"as {LOGIN}\n"},
        capsys,
    )

    assert status == 1
    assert f"{JOURNEY_RECORD}:1: [home-path]" in err
    assert f"{other}:1: [login]" in err


def test_a_pure_move_of_a_record_holding_the_home_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _write(repo, JOURNEY_RECORD, f"one\ntwo {HOME}/x\nthree\nfour\n")
    _commit(repo)
    (repo / MOVED_RECORD).parent.mkdir(parents=True)
    _git(repo, "mv", JOURNEY_RECORD, MOVED_RECORD)

    status = _check(repo)

    assert status == 0
    assert capsys.readouterr().err == ""


def test_a_clean_line_added_to_a_record_holding_the_home_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _write(repo, JOURNEY_RECORD, f"one\ntwo {HOME}/x\nthree\n")
    _commit(repo)
    _stage(repo, {JOURNEY_RECORD: f"one\ntwo {HOME}/x\nthree\nfour is clean\n"})

    status = _check(repo)

    assert status == 0
    assert capsys.readouterr().err == ""


def test_a_line_in_a_record_renamed_and_edited_is_read_only_where_added(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _write(repo, JOURNEY_RECORD, f"one\ntwo {HOME}/old\nthree\nfour\nfive\n")
    _commit(repo)
    (repo / MOVED_RECORD).parent.mkdir(parents=True)
    _git(repo, "mv", JOURNEY_RECORD, MOVED_RECORD)
    _stage(
        repo,
        {MOVED_RECORD: f"one\ntwo {HOME}/old\nthree\nfour\nfive\nsix {HOME}/new\n"},
    )

    status = _check(repo)

    err = capsys.readouterr().err
    assert status == 1
    assert f"{MOVED_RECORD}:6: [home-path] six {HOME}/new" in err
    assert err.count(f"{MOVED_RECORD}:") == 1


def test_an_added_home_line_is_refused_from_the_index(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _write(repo, JOURNEY_RECORD, "one\ntwo\n")
    _commit(repo)
    _stage(repo, {JOURNEY_RECORD: f"one\ntwo\nthree {HOME}/x\n"})

    status = _check(repo)

    assert status == 1
    assert f"{JOURNEY_RECORD}:3: [home-path] three {HOME}/x" in capsys.readouterr().err


def test_a_folder_git_cannot_read_is_refused_with_a_message_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    not_a_repository = tmp_path / "plain-folder"
    not_a_repository.mkdir()

    status = check_record_privacy.main(
        ["--staged", "--repo", str(not_a_repository)], home=HOME, login=LOGIN
    )

    err = capsys.readouterr().err
    assert status == 1
    assert err.startswith("check_record_privacy: git could not read the staged changes in ")
    assert "Traceback" not in err


def test_lines_added_in_two_places_report_their_own_numbers_past_a_deleted_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _write(repo, JOURNEY_RECORD, "l1\nl2\nl3\nl4\nl5\nl6\n")
    _commit(repo)
    _stage(
        repo,
        {JOURNEY_RECORD: f"l1\nl3\nl4\nfirst {HOME}/a\nl5\nl6\nsecond {HOME}/b\n"},
    )

    status = _check(repo)

    err = capsys.readouterr().err
    assert status == 1
    assert f"{JOURNEY_RECORD}:4: [home-path] first {HOME}/a" in err
    assert f"{JOURNEY_RECORD}:7: [home-path] second {HOME}/b" in err


REMEDY_FROM_CHANGE_TEXT = (
    "[home-path] is this machine's home folder, written out. [login] is this machine's login name, "
    "standing as a word. [repository] is this repository's own `<owner>/<name>` address. A record "
    "ships with the repository it is committed to, so it names no one's machine and not the "
    "repository's address. Write the home folder as `<home>/…`, a path inside the instance as "
    "`<the instance>/…` or relative to its root, the login name as `<user>`, and the address as "
    "`<owner>/<repository>`. Terminal output "
    "pasted into a record, and the commands an evidence line quotes, are the cases to look at "
    "first. See <CORE>/doctrine/governance/records_name_no_machine.md.\n"
    "\n"
    "Only the lines this commit adds to a record are read, so every line named above is one this "
    "commit writes. Lines the record already held, and a record moved or renamed unchanged, are "
    "not read.\n"
)


def test_the_refusal_is_each_hit_then_one_blank_line_then_the_remedy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = f"cache read from {HOME}/.cache/uv"

    status, err = _check_files(tmp_path, {JOURNEY_RECORD: f"{line}\n"}, capsys)

    assert status == 1
    assert err == f"{JOURNEY_RECORD}:1: [home-path] {line}\n\n{REMEDY_FROM_CHANGE_TEXT}"


@pytest.mark.parametrize(
    ("key", "value"),
    [("diff.mnemonicPrefix", "true"), ("diff.noprefix", "true"), ("diff.srcPrefix", "x/"),
     ("diff.dstPrefix", "y/")],
)
def test_a_record_is_read_whatever_diff_prefix_the_repo_sets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], key: str, value: str
) -> None:
    repo = _scratch_repo(tmp_path)
    _git(repo, "config", key, value)
    _stage(repo, {JOURNEY_RECORD: f"see {HOME}/x\n"})

    status = _check(repo)

    assert status == 1
    assert f"{JOURNEY_RECORD}:1: [home-path] see {HOME}/x" in capsys.readouterr().err


def test_line_numbers_hold_when_the_repo_fuses_nearby_hunks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _scratch_repo(tmp_path)
    _git(repo, "config", "diff.interHunkContext", "5")
    _write(repo, JOURNEY_RECORD, "l1\nl2\nl3\nl4\n")
    _commit(repo)
    _stage(repo, {JOURNEY_RECORD: f"l1\nfirst {HOME}/a\nl2\nl3\nsecond {HOME}/b\nl4\n"})

    status = _check(repo)

    err = capsys.readouterr().err
    assert status == 1
    assert f"{JOURNEY_RECORD}:2: [home-path] first {HOME}/a" in err
    assert f"{JOURNEY_RECORD}:5: [home-path] second {HOME}/b" in err


@pytest.mark.parametrize(
    "record",
    ["system/projects/p/with space.md", 'system/projects/p/with"quote.md',
     "system/projects/p/with\\backslash.md", "system/projects/p/naïve.md"],
)
def test_a_record_whose_name_git_quotes_or_pads_is_named_as_it_is(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], record: str
) -> None:
    earlier = "system/projects/p/a.md"

    status, err = _check_files(
        tmp_path, {earlier: "clean\n", record: f"see {HOME}/x\n"}, capsys
    )

    assert status == 1
    assert f"{record}:1: [home-path] see {HOME}/x\n" in err
    assert f"{earlier}:" not in err


# --- the repository's own address ---------------------------------------------------------------

ADDRESS = "hollow-org/the-instance"


def _check_address(tmp_path: Path, text: str, capsys: pytest.CaptureFixture[str],
                   *, repositories: tuple[str, ...] = (ADDRESS,)) -> tuple[int, str]:
    repo = _scratch_repo(tmp_path)
    _stage(repo, {JOURNEY_RECORD: text})
    status = check_record_privacy.main(
        ["--staged", "--repo", str(repo)], home=HOME, login=LOGIN, repositories=repositories
    )
    return status, capsys.readouterr().err


def test_the_repositorys_address_in_a_command_is_a_hit(tmp_path, capsys):
    status, err = _check_address(
        tmp_path, f"`gh api repos/{ADDRESS}/dependabot/alerts` returned HTTP 403\n", capsys)

    assert status == 1
    assert f"{JOURNEY_RECORD}:1: [repository]" in err


@pytest.mark.parametrize("suffix", [".git", ".wiki"])
def test_the_address_with_a_suffix_still_names_the_repository(tmp_path, capsys, suffix):
    status, _ = _check_address(tmp_path, f"cloned from {ADDRESS}{suffix}\n", capsys)

    assert status == 1


def test_the_address_is_matched_in_any_letter_case(tmp_path, capsys):
    status, _ = _check_address(tmp_path, "the repo is Hollow-Org/The-Instance\n", capsys)

    assert status == 1


def test_a_longer_name_beginning_with_the_address_is_not_a_hit(tmp_path, capsys):
    status, _ = _check_address(tmp_path, f"see {ADDRESS}-fork and {ADDRESS}2\n", capsys)

    assert status == 0


def test_the_address_inside_a_link_is_a_hit(tmp_path, capsys):
    status, _ = _check_address(tmp_path, f"https://github.com/{ADDRESS}/security\n", capsys)

    assert status == 1


def test_the_bare_name_and_the_placeholder_pass(tmp_path, capsys):
    status, _ = _check_address(
        tmp_path, "the-instance holds it; `gh api repos/<owner>/<repository>` returned 404\n", capsys)

    assert status == 0


def test_a_repository_with_no_remote_has_no_address_to_look_for(tmp_path, capsys):
    repo = _scratch_repo(tmp_path)
    _stage(repo, {JOURNEY_RECORD: f"gh api repos/{ADDRESS}\n"})

    assert check_record_privacy.main(["--staged", "--repo", str(repo)], home=HOME, login=LOGIN) == 0


def test_only_origin_gives_the_address_another_remote_is_another_repository(tmp_path, capsys):
    repo = _scratch_repo(tmp_path)
    _git(repo, "remote", "add", "origin", f"git@github.com:{ADDRESS}.git")
    _git(repo, "remote", "add", "upstream", "https://github.com/other-org/other-repo.git")
    _stage(repo, {JOURNEY_RECORD: "forked from other-org/other-repo\n"})

    assert check_record_privacy.main(["--staged", "--repo", str(repo)], home=HOME, login=LOGIN) == 0


def test_a_local_folder_origin_gives_no_address(tmp_path, capsys):
    repo = _scratch_repo(tmp_path)
    _git(repo, "remote", "add", "origin", "../kensai/the-instance")
    _stage(repo, {JOURNEY_RECORD: "see ../kensai/the-instance/system for it\n"})

    assert check_record_privacy.main(["--staged", "--repo", str(repo)], home=HOME, login=LOGIN) == 0


def test_the_refusal_names_the_address_placeholder(tmp_path, capsys):
    _, err = _check_address(tmp_path, f"repos/{ADDRESS}\n", capsys)

    assert "[repository]" in err and "`<owner>/<repository>`" in err


@pytest.mark.parametrize("url", [
    f"git@github.com:{ADDRESS}.git",
    f"https://github.com/{ADDRESS}.git",
    f"https://github.com/{ADDRESS}",
    f"ssh://git@github.com:22/{ADDRESS}/",
], ids=["scp-like", "https", "https-no-suffix", "ssh-url"])
def test_the_address_is_read_off_every_hosting_service_form(url):
    assert check_record_privacy.remote_address(url) == ADDRESS


@pytest.mark.parametrize("url", [
    "../kensai/the-instance", "/srv/git/the-instance.git", "file:///srv/git/hollow-org/the-instance",
], ids=["relative-folder", "absolute-folder", "file-url"])
def test_a_local_remote_gives_no_address(url):
    assert check_record_privacy.remote_address(url) == ""


def test_with_no_address_given_the_check_reads_the_repositorys_own_remotes(tmp_path, capsys):
    repo = _scratch_repo(tmp_path)
    _git(repo, "remote", "add", "origin", f"git@github.com:{ADDRESS}.git")
    _stage(repo, {JOURNEY_RECORD: f"repos/{ADDRESS} says private\n"})

    status = check_record_privacy.main(["--staged", "--repo", str(repo)], home=HOME, login=LOGIN)

    assert status == 1
    assert "[repository]" in capsys.readouterr().err
