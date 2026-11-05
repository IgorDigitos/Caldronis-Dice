import asyncio
from itertools import product
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll, roll_many
from message_handler import MessageHandler, format_batch, format_result, text_length


def test_image_example_and_single_bonus_regression():
    def example(source):
        values = iter([14, 8])
        return roll(parse(source), {}, lambda sides: next(values))

    result = example("2d30++5")
    assert result.total == 34
    assert result.details[0].values == (15, 9)
    assert format_result(result) == ("`\u00a034\u00a0` ⟵ [20, 14] ⟵ [15, 9] 2d30 ++ 5",)
    assert example("2d30+5").total == 29


def test_repetitions_are_independent_and_criticals_only_natural():
    values = iter([0, 5, 2, 1])
    results = roll_many(parse("2#2d6++5 ataque"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [17, 15]
    assert format_batch(results) == (
        "`\u00a017\u00a0` ⟵ [11, 6] ⟵ [**6**, **1**] 2d6 ++ 5\n"
        "`\u00a015\u00a0` ⟵ [8, 7] ⟵ [3, 2] 2d6 ++ 5\n> ataque",
    )


@pytest.mark.parametrize("source", ["  2D30 ++ 005 teste", "2d30++5 teste"])
def test_spaces_case_and_comment(source):
    expression = parse(source)
    assert expression.per_die_bonus == 5
    assert expression.comment == "teste"
    assert expression.attributes == set()


def test_arithmetic_for_all_two_d6_outcomes():
    for first, second, bonus in product(range(1, 7), range(1, 7), [0, 1, 1000000000]):
        values = iter([first - 1, second - 1])
        result = roll(parse(f"2d6++{bonus}"), {}, lambda sides, draws=values: next(draws))
        assert result.total == first + second + 2 * bonus
        assert result.details[0].values == (first, second)


@pytest.mark.parametrize(
    "source",
    [
        "d6++",
        "d6+++5",
        "d6++-5",
        "d6++FOR",
        "d6++d4",
        "d6++1.5",
        "d6++1000000001",
        "d6++" + "9" * 500,
        "d6++5abc",
        "d6++5+2",
        "d6++5 + 2",
        "d6++5>>4",
        "d6++5 << 3",
        "d6!++5",
        "d6++5!",
        "d6+2++5",
        "d6+d4++5",
        "101d6++5",
        "51#2d6++5",
        "d6++5 ++ 2",
    ],
)
def test_invalid_syntax_rejected_entirely(source):
    with pytest.raises(DiceError):
        parse(source)


@pytest.mark.parametrize("source,valid", [("2d30++5", True), ("2d30++5 >>4", False)])
def test_handler_validates_before_draw_and_never_loads_profiles(source, valid, monkeypatch):
    calls = []

    def controlled(expression, attributes):
        calls.append(expression)
        values = iter([14, 8])
        return roll_many(expression, attributes, lambda sides: next(values))

    monkeypatch.setattr("message_handler.roll_many", controlled)
    repository = SimpleNamespace(attributes=AsyncMock())
    message = SimpleNamespace(
        content=source,
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(bot=False),
        webhook_id=None,
        reply=AsyncMock(),
    )
    asyncio.run(MessageHandler(repository).handle(message))
    repository.attributes.assert_not_awaited()
    message.reply.assert_awaited_once()
    output = message.reply.await_args.kwargs["content"]
    assert bool(calls) is valid
    assert ("34" in output) if valid else ("Não foi possível rolar" in output)


@pytest.mark.parametrize("source", ["100d100000++1000000000", "100#d100000++1000000000"])
def test_large_outputs_preserve_values_and_limits(source):
    calls = []

    def draw(sides):
        calls.append(sides)
        return sides - 1

    output = format_batch(roll_many(parse(source + " " + "😀" * 850), {}, draw))
    assert len(calls) == 100
    assert all(text_length(message) <= 1900 for message in output)
    assert "".join(output).count("1000100000") >= 100
    assert "".join(output).count("**100000**") == 100
    assert "".join(output).count("😀") == 850
