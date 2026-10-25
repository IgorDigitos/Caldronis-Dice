import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll, roll_many
from message_handler import MessageHandler, format_batch, format_result, text_length


def test_maximum_adds_extra_die():
    values = iter([5, 3])
    result = roll(parse("d6!"), {}, lambda sides: next(values))
    assert result.total == 10
    assert result.details[0].values == (6, 4)
    assert format_result(result) == ("`\u00a010\u00a0` ⟵ [**6**, 4] d6!",)


def test_chained_maximums_continue_until_nonmaximum():
    values = iter([5, 5, 0])
    result = roll(parse("d6!"), {}, lambda sides: next(values))
    assert result.total == 13
    assert format_result(result) == ("`\u00a013\u00a0` ⟵ [**6**, **6**, **1**] d6!",)


def test_nonmaximum_does_not_roll_again():
    calls = []

    def random_source(sides):
        calls.append(sides)
        return 3

    assert roll(parse("d6!"), {}, random_source).total == 4
    assert calls == [6]


def test_only_marked_dice_explode():
    values = iter([5, 5, 3])
    result = roll(parse("d6+d6!"), {}, lambda sides: next(values))
    assert result.total == 16
    assert result.details[0].values == (6,)
    assert result.details[1].values == (6, 4)


def test_multiple_dice_attributes_and_subtracted_explosion():
    values = iter([5, 3, 1, 3, 0])
    result = roll(parse("2d6!+FOR-d4! atacar"), {"FOR": 8}, lambda sides: next(values))
    assert result.total == 15
    assert format_result(result) == (
        "`\u00a015\u00a0` ⟵ [**6**, 4, 2] 2d6! + FOR - [**4**, **1**] d4!\nFOR=+8\n> atacar",
    )


def test_repetitions_separate_and_sorted():
    values = iter([5, 3, 1])
    results = roll_many(parse("2#d6!"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [10, 2]
    output = format_batch(results)
    assert len(output) == 1
    lines = output[0].splitlines()
    assert [line.split("`")[1].strip() for line in lines] == ["10", "2"]
    assert lines[0].endswith("[**6**, 4] 1d6!")
    assert lines[1].endswith("[2] 1d6!")


@pytest.mark.parametrize("source", ["d6!", "2D30!", "  2#d6! + FOR", "d6!+d4! comentário"])
def test_parser_accepts_explosion_suffix(source):
    expression = parse(source)
    assert expression.terms[0].exploding
    assert expression.terms[0].kind == "dice"


@pytest.mark.parametrize(
    "source",
    [
        "d6!!",
        "d6!5",
        "d6 !",
        "d6! !",
        "d6!+",
        "d1!",
        "101d6!",
        "d6!abc",
        "d6!+FOR!",
        "d6>>4!",
        "d6>>4 !",
        "d6!+d4!!",
        "d6!+2!",
    ],
)
def test_invalid_explosion_never_rolls(source, monkeypatch):
    def forbidden(*args):
        pytest.fail("Não deve executar uma expressão inválida")

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


def test_detection_still_anchored():
    assert parse("!d6") is None
    assert parse("Vou usar d6!") is None
    assert parse("Ataque: 2#d6!") is None


def test_attribute_resolution_precedes_any_draw():
    def forbidden(sides):
        pytest.fail("Não deve sortear com atributo ausente")

    with pytest.raises(DiceError, match="FOR"):
        roll_many(parse("2#d6!+FOR"), {}, forbidden)


def test_exactly_hundred_draws_can_complete():
    values = iter([5] * 99 + [0])
    result = roll(parse("d6!"), {}, lambda sides: next(values))
    assert result.total == 595
    assert len(result.details[0].values) == 100


def test_budget_shared_across_repetitions():
    values = iter([5] * 98 + [0, 0])
    results = roll_many(parse("2#d6!"), {}, lambda sides: next(values))
    assert [len(result.details[0].values) for result in results] == [99, 1]
    assert [result.total for result in results] == [589, 1]


def test_exhausted_budget_is_not_reset_for_next_repetition():
    values = iter([5] * 99 + [0])
    with pytest.raises(DiceError, match="100 sorteios"):
        roll_many(parse("2#d6!"), {}, lambda sides: next(values))


def test_exhausted_budget_is_not_reset_for_next_term():
    values = iter([5] * 98 + [0, 3])
    with pytest.raises(DiceError, match="100 sorteios"):
        roll(parse("d6!+d4!"), {}, lambda sides: next(values))


def test_infinite_maximums_stop_at_hundred_and_reply_only_error(monkeypatch):
    calls = []

    def random_source(sides):
        calls.append(sides)
        return sides - 1

    monkeypatch.setattr(
        "message_handler.roll_many",
        lambda expression, attributes: roll_many(expression, attributes, random_source),
    )
    repo = SimpleNamespace(attributes=AsyncMock())
    message = SimpleNamespace(
        content="2#d6!",
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(bot=False),
        webhook_id=None,
        reply=AsyncMock(),
    )
    asyncio.run(MessageHandler(repo).handle(message))
    assert len(calls) == 100
    message.reply.assert_awaited_once()
    output = message.reply.await_args.kwargs["content"]
    assert "100 sorteios" in output
    assert "⟵" not in output
    repo.attributes.assert_not_awaited()


def test_long_explosion_preserves_every_value_and_comment():
    values = iter([99999] * 99 + [0])
    result = roll(parse("d100000! " + "😀" * 900), {}, lambda sides: next(values))
    output = format_result(result)
    assert all(text_length(message) <= 1900 for message in output)
    assert "".join(output).count("**100000**") == 99
    assert "".join(output).count("**1**") == 1
    assert "".join(output).count("😀") == 900


def test_attribute_names_starting_with_dice_are_preserved():
    result = roll(parse("d6!+D20_MOD"), {"D20_MOD": 3}, lambda sides: 0)
    assert result.total == 4
    assert "d6! + D20_MOD" in format_result(result)[0]


@pytest.mark.parametrize(
    "expression,draw,expected",
    [
        ("d6!>>4", 6, 2),
        ("d6!>>4", 4, 1),
        ("d6!>>4", 1, 0),
        ("d6!<<3", 1, 2),
        ("d6!<<3", 3, 1),
        ("d6!<<3", 6, 0),
        ("d6!>>7", 6, 0),
        ("d6!<<0", 1, 0),
        ("d6>>4", 6, 1),
        ("d6<<3", 1, 1),
    ],
)
def test_counting_critical_weights_without_any_extra_die(expression, draw, expected):
    calls = []

    def random_source(sides):
        calls.append(sides)
        return draw - 1

    result = roll(parse(expression), {}, random_source)
    assert result.total == expected
    assert result.details[0].values == (draw,)
    assert calls == [6]
    output = format_result(result)[0]
    assert "sucesso" not in output and "fracasso" not in output


@pytest.mark.parametrize("operator,expected", [(">>", 4), ("<<", 3)])
def test_mixed_pool_weighted_at_correct_extreme(operator, expected):
    values = iter([5, 4, 3, 1, 0])
    target = 4 if operator == ">>" else 3
    result = roll(parse(f"5d6!{operator}{target}"), {}, lambda sides: next(values))
    assert result.total == expected
    assert result.details[0].values == (6, 5, 4, 2, 1)
    assert format_result(result)[0].endswith(f"[**6**, 5, 4, 2, **1**] 5d6! {operator} {target}")


def test_weighted_count_repetitions_are_independent_and_no_extras():
    values = iter([5, 3, 0, 5])
    results = roll_many(parse("2#2d6!>>4 atacar"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [3, 2]
    assert format_batch(results) == (
        "`\u00a03\u00a0` ⟵ [**6**, 4] 2d6! >> 4\n"
        "`\u00a02\u00a0` ⟵ [**6**, **1**] 2d6! >> 4\n> atacar",
    )


@pytest.mark.parametrize("expression,raw", [("100d6!>>6", 5), ("100d6!<<1", 0)])
def test_hundred_critical_count_dice_return_two_hundred(expression, raw):
    calls = []

    def random_source(sides):
        calls.append(sides)
        return raw

    result = roll(parse(expression), {}, random_source)
    assert result.total == 200
    assert len(result.details[0].values) == 100
    assert len(calls) == 100


def test_hundred_weighted_repetitions_use_exactly_hundred_draws():
    calls = []

    def random_source(sides):
        calls.append(sides)
        return 5

    results = roll_many(parse("100#d6!>>6"), {}, random_source)
    assert len(results) == 100
    assert all(result.total == 2 for result in results)
    assert len(calls) == 100
    output = format_batch(results)
    assert all(text_length(message) <= 1900 for message in output)
    assert "".join(output).count("[**6**] 1d6! >> 6") == 100
