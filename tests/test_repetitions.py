import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll_many
from message_handler import MessageHandler, format_batch, text_length
from profiles.service import normalize_name


@pytest.mark.parametrize(
    "source,count",
    [
        ("2#d30", 2),
        ("3#2d20+FOR atacar", 3),
        ("  2#D30", 2),
        ("2# d30 + FOR", 2),
        ("1#d6", 1),
        ("100#d2", 100),
        ("50#2d6", 50),
    ],
)
def test_repeat_parser(source, count):
    expression = parse(source)
    assert expression.repeat_count == count
    assert not expression.original.startswith(str(count) + "#")
    assert expression.terms[0].kind == "dice"


@pytest.mark.parametrize(
    "source",
    [
        "Vou usar 2#d30",
        "Ataque: 2#d30",
        "!2#d30",
        "/r 2#d30",
        "-2#d30",
        "# título",
    ],
)
def test_repeat_not_at_start_ignored(source):
    assert parse(source) is None


@pytest.mark.parametrize(
    "source",
    [
        "0#d30",
        "101#d30",
        "9999999999999999999#d30",
        "#d30",
        "2#",
        "2##d30",
        "2#FOR",
        "2#10",
        "2#-d30",
        "2#d30+",
        "2#d1",
        "2#d100001",
        "2#d30abc",
        "2#d30#2",
        "2#d30 #2",
        "2#2#d30",
        "51#2d6",
        "2#50d6+d2",
        "100#d6+1",
        "4#d6" + "+1" * 25,
    ],
)
def test_invalid_repetition_no_partial_roll_or_database(source, monkeypatch):
    def forbidden(*args):
        pytest.fail("Expressão inválida não pode executar sorteios")

    monkeypatch.setattr("message_handler.roll_many", forbidden)
    repo = SimpleNamespace(attributes=AsyncMock())
    message = SimpleNamespace(
        content=source,
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(bot=False),
        webhook_id=None,
        reply=AsyncMock(),
    )
    asyncio.run(MessageHandler(repo).handle(message))
    repo.attributes.assert_not_awaited()
    assert "Não foi possível rolar" in message.reply.await_args.kwargs["content"]


def test_reference_image_two_lines_no_header_or_grand_total():
    values = iter([11, 14])
    results = roll_many(parse("2#d30"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [12, 15]
    assert format_batch(results) == ("`\u00a012\u00a0` ⟵ [12] 1d30\n`\u00a015\u00a0` ⟵ [15] 1d30",)


def test_repeats_preserve_dice_and_line_order():
    values = iter([1, 5, 2, 4, 0, 3])
    results = roll_many(parse("2#3d6"), {}, lambda sides: next(values))
    assert format_batch(results) == (
        "`\u00a011\u00a0` ⟵ [2, **6**, 3] 3d6\n`\u00a010\u00a0` ⟵ [5, **1**, 4] 3d6",
    )


def test_even_one_explicit_repeat_preserves_order():
    values = iter([1, 5, 2])
    assert format_batch(roll_many(parse("1#3d6"), {}, lambda sides: next(values))) == (
        "`\u00a011\u00a0` ⟵ [2, **6**, 3] 3d6",
    )


def test_attributes_comment_and_subtraction_shared_once():
    values = iter([3, 1, 5, 2])
    results = roll_many(
        parse("2#d6-d4+FOR-CON ataque"), {"FOR": 8, "CON": -2}, lambda sides: next(values)
    )
    assert format_batch(results) == (
        "`\u00a012\u00a0` ⟵ [4] 1d6 - [2] 1d4 + FOR - CON\n"
        "`\u00a013\u00a0` ⟵ [**6**] 1d6 - [3] 1d4 + FOR - CON\nFOR=+8 · CON=-2\n> ataque",
    )


def test_missing_attribute_prevents_all_repetitions():
    def forbidden(sides):
        pytest.fail("Não pode sortear antes de validar atributos")

    with pytest.raises(DiceError, match="FOR"):
        roll_many(parse("3#d30+FOR"), {}, forbidden)


def test_database_read_once_per_batch(monkeypatch):
    calls = []

    def random_source(sides):
        calls.append(sides)
        return 0

    monkeypatch.setattr(
        "message_handler.roll_many",
        lambda expression, attributes: roll_many(expression, attributes, random_source),
    )
    repo = SimpleNamespace(attributes=AsyncMock(return_value={"FOR": 8}))
    message = SimpleNamespace(
        content="3#d30+FOR",
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(bot=False, id=10),
        webhook_id=None,
        reply=AsyncMock(),
    )
    asyncio.run(MessageHandler(repo).handle(message))
    repo.attributes.assert_awaited_once_with(1, 10)
    assert calls == [30, 30, 30]
    assert message.reply.await_args.kwargs["content"].count("`\u00a09\u00a0` ⟵") == 3


def test_hundred_repeats_bounded_without_hidden_rolls():
    calls = []

    def random_source(sides):
        calls.append(sides)
        return sides - 1

    results = roll_many(parse("100#d100000 " + "😀" * 900), {}, random_source)
    messages = format_batch(results)
    output = "".join(messages)
    assert len(calls) == 100
    assert len(messages) > 1
    assert all(text_length(text) <= 1900 for text in messages)
    assert output.count("`\u00a0100000\u00a0` ⟵") == 100
    assert output.count("**100000**") == 100
    assert output.count("😀") == 900


def test_totals_aligned_with_negative_zero_and_large_numbers():
    values = iter([0, 1, 99999])
    results = roll_many(parse("3#d100000-2"), {}, lambda sides: next(values))
    totals = [line.split("`")[1] for line in format_batch(results)[0].splitlines()]
    assert [number.strip() for number in totals] == ["-1", "0", "99998"]
    assert len({len(number) for number in totals}) == 1
    assert all(number.startswith("\u00a0") and number.endswith("\u00a0") for number in totals)
    for number in totals:
        left = len(number) - len(number.lstrip("\u00a0"))
        right = len(number) - len(number.rstrip("\u00a0"))
        assert abs(left - right) <= 1


@pytest.mark.parametrize(
    "source",
    ["2d20kh1", "2d20kl1", "4d6dh1", "4d6dl1", "4d6k3", "4d6d1", "3#2d20kh1", "d20+2d20kh1"],
)
def test_removed_modifiers_not_supported(source):
    with pytest.raises(DiceError):
        parse(source)


def test_removed_selection_name_restriction():
    assert normalize_name("D20KH1") == "D20KH1"
    assert parse("d20+D20KH1").attributes == {"D20KH1"}
