from __future__ import annotations

import sys

from behave import given, then, when
from behave.runner import Context
from command_way_in import run_program


@given('a program that prints "{text}" and exits with status {status:d}')
def a_program_that_prints_and_exits(context: Context, text: str, status: int) -> None:
    context.program = [sys.executable, "-c", f"import sys; print({text!r}); sys.exit({status})"]


@when("the program is run through the command way in")
def the_program_is_run_through_the_command_way_in(context: Context) -> None:
    context.command_result = run_program(context.program)


@then("the exit status is {status:d}")
def the_exit_status_is(context: Context, status: int) -> None:
    assert context.command_result.exit_status == status, context.command_result


@then('the output is "{text}"')
def the_output_is(context: Context, text: str) -> None:
    assert context.command_result.output.strip() == text, context.command_result
