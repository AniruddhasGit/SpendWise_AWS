"""The error envelope, the closed registry, and the precedence chain.

All pure — no database. These assert against `contract.json` directly rather
than against constants copied into the test, so a change to the spec of record
fails here before it can reach a client.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.errors import (
    ApiError, Violation, code_messages, codes, envelope, precedence, rules,
    validation_error,
)

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[1] / "docs" / "03 PRD" / "api" / "contract.json")
    .read_text("utf-8"))


# ── the registry is closed ─────────────────────────────────────────────────
def test_every_contract_code_is_loadable_and_nothing_extra_exists() -> None:
    assert set(codes()) == {c["code"] for c in CONTRACT["error_codes"]["codes"]}


def test_every_code_has_a_message() -> None:
    """A code with no stated sentence is a binary acceptance criterion nobody
    can write — the argument `SW-ADR-140` used, applied to the whole list.

    `VALIDATION_ERROR` is the one exception, and deliberately: its message comes
    from the RULE that fired, one of fourteen, each with its own sentence. A
    single message keyed on the code would be wrong for all fourteen.
    """
    missing = sorted(set(codes()) - set(code_messages()) - {"VALIDATION_ERROR"})
    assert not missing, f"codes with no message: {missing}"
    assert "VALIDATION_ERROR" not in code_messages(), (
        "VALIDATION_ERROR gained a by-code message; its sentence must come from "
        "the rule, or thirteen specific messages collapse into one vague one")


def test_an_unlisted_code_cannot_be_constructed() -> None:
    """A closed list is only closed if the closure is enforced in code."""
    with pytest.raises(ValueError, match="CLOSED"):
        ApiError("TEAPOT")


@pytest.mark.parametrize("code,status", [("VALIDATION_ERROR", 422), ("NOT_FOUND", 404),
                                         ("UNAUTHENTICATED", 401), ("SESSION_INVALID", 401),
                                         ("ACCOUNT_DEACTIVATED", 401), ("FORBIDDEN", 403),
                                         ("CONFLICT", 409), ("RATE_LIMITED", 429),
                                         ("BAD_REQUEST", 400), ("INTERNAL", 500)])
def test_status_codes(code: str, status: int) -> None:
    assert ApiError(code).status == status


def test_session_invalid_gives_one_sentence_for_every_cause() -> None:
    """Distinguishing expiry from a bad signature tells an attacker which they
    hit. One sentence, by rule."""
    msg = code_messages()["SESSION_INVALID"]
    for leak in ("expired", "revoked", "signature", "rotated", "idle"):
        assert leak not in msg.lower(), f"the message leaks the cause: {msg!r}"


def test_internal_never_carries_detail() -> None:
    body = envelope(ApiError("INTERNAL"))["error"]
    assert "field" not in body
    assert len(body["message"]) < 60, "a generic message that long is carrying detail"


# ── the envelope ───────────────────────────────────────────────────────────
def test_envelope_shape() -> None:
    body = envelope(ApiError("VALIDATION_ERROR", field="amount", message="Nope."))
    assert body == {"error": {"code": "VALIDATION_ERROR", "message": "Nope.", "field": "amount"}}


def test_field_is_omitted_when_there_is_none() -> None:
    assert "field" not in envelope(ApiError("NOT_FOUND"))["error"]


def test_field_carries_the_clients_name_never_the_columns() -> None:
    """`amount`, never `amount_paise` — the client never sent `amount_paise`
    and cannot act on a name it has not seen."""
    for r in rules().values():
        assert "paise" not in str(r["field"]), r


# ── precedence: the whole point ────────────────────────────────────────────
def test_precedence_is_presence_then_type_then_value() -> None:
    order = precedence()
    assert order[0] == "field.required"
    assert order[1] == "field.type"
    assert order.index("category.not_owned") == len(order) - 1, (
        "the database raises category.not_owned after every in-process rule has "
        "passed, so it must be last")


@pytest.mark.parametrize("broken,winner", [
    (["field.type", "field.required"], "field.required"),
    (["amount.bounds", "amount.grammar"], "amount.grammar"),
    (["amount.scale", "field.type"], "field.type"),
    (["spent_on.window", "amount.scale"], "amount.scale"),
    (["category.not_owned", "description.length"], "description.length"),
    (["range.span", "range.order"], "range.order"),
    (["range.floor", "range.span"], "range.span"),
])
def test_the_first_rule_in_the_order_wins(broken: list[str], winner: str) -> None:
    """A body that breaks two rules has ONE answer, and it is the contract's.

    Without this, two engineers implement opposite orders and both pass the
    negative suite — every case there varies exactly one input.
    """
    err = validation_error([Violation(r, "amount") for r in broken])
    # Compare against the RENDERED sentence of the expected winner, not its raw
    # template — placeholders are substituted at render time and the rendered
    # form is what a client sees and a test asserts on.
    _, expected = Violation(winner, "amount").render()
    assert err.message == expected


def test_a_doubly_invalid_body_reports_exactly_one_field() -> None:
    err = validation_error([Violation("field.required", "amount"),
                            Violation("field.type", "spent_on")])
    body = envelope(err)["error"]
    assert body["field"] == "amount"
    assert body["message"] == "amount is required."


def test_placeholders_are_substituted_in_the_rendered_sentence() -> None:
    """`{field}`/`{expected}`/`{example}` are part of the contract, because the
    RENDERED sentence is what a test asserts on."""
    _, msg = Violation("field.type", "spent_on").render()
    assert "{" not in msg, f"an unsubstituted placeholder reached the client: {msg!r}"
    assert "spent_on" in msg and "date" in msg


def test_every_precedence_rule_has_a_message() -> None:
    """A rule that can fire and has no sentence is the gap `SW-ADR-141` closed
    for `field.required`/`field.type`. Assert it for the whole chain."""
    missing = [r for r in precedence() if r not in rules()]
    assert not missing, f"rules in the precedence order with no message: {missing}"


def test_no_rule_is_unreachable() -> None:
    """The mirror image: a message for a rule the order never consults is dead
    text — which is what `amount.scale` became when the grammar pattern also
    capped decimal places and ran first."""
    orphans = [r for r in rules() if r not in precedence()]
    assert not orphans, f"rules with a message but no place in the order: {orphans}"
