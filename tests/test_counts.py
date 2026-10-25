import asyncio
from itertools import product
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll, roll_many
from message_handler import MessageHandler, format_batch, format_result, text_length


def test_exact_chosen_example():
    values = iter([5, 4, 3, 1, 0])
    result = roll(parse("5d6>>4"), {}, lambda sides: next(values))
    assert result.total == 3
    assert result.details[0].values == (6, 5, 4, 2, 1)
    assert format_result(result) == ("`\u00a03\u00a0` ⟵ [**6**, 5, 4, 2, **1**] 5d6 >> 4",)


@pytest.mark.parametrize(
    "source,repeat,target,comment",
    [
        ("5d6 >> 4", None, 4, ""),
        ("  5D6>>4 atacar o guarda", None, 4, "atacar o guarda"),
        ("3#5d6>>4", 3, 4, ""),
        ("2# 5d6 >> 04 teste", 2, 4, "teste"),
        ("d6>>0", None, 0, ""),
        ("d6>>1000000000", None, 1000000000, ""),
    ],
)
def test_parser(source, repeat, target, comment):
    expression = parse(source)
    assert expression.repeat_count == repeat
    assert expression.count_target == target
    assert expression.count_operator == ">>"
    assert expression.comment == comment
    assert expression.attributes == set()
    assert len(expression.terms) == 1


@pytest.mark.parametrize(
    "source,total",
    [
        ("3d6>>0", 3),
        ("3d6>>1", 3),
        ("3d6>>6", 0),
        ("3d6>>7", 0),
        ("100d100000>>1", 100),
        ("100#d6>>1", 1),
    ],
)
def test_boundaries(source, total):
    results = roll_many(parse(source), {}, lambda sides: 0)
    assert all(result.total == total for result in results)


def test_one_does_not_cancel_and_maximum_does_not_double_success():
    values = iter([0, 5])
    result = roll(parse("2d6>>4"), {}, lambda sides: next(values))
    assert result.total == 1
    assert format_result(result) == ("`\u00a01\u00a0` ⟵ [**6**, **1**] 2d6 >> 4",)


def test_zero_successes_explicitly_shown():
    result = roll(parse("3d6>>7"), {}, lambda sides: 5)
    assert result.total == 0
    assert "`\u00a00\u00a0`" in format_result(result)[0]
    assert format_result(result)[0].endswith("3d6 >> 7")


def test_repeated_successes_preserve_order_and_comment():
    values = iter([0, 3, 5, 2, 1, 0])
    results = roll_many(parse("2#3d6>>4 atacar"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [2, 0]
    assert format_batch(results) == (
        "`\u00a02\u00a0` ⟵ [**6**, 4, **1**] 3d6 >> 4\n"
        "`\u00a00\u00a0` ⟵ [3, 2, **1**] 3d6 >> 4\n> atacar",
    )


@pytest.mark.parametrize("operator", [">>", "<<"])
def test_exhaustive_two_dice_count_individual_values_not_sum(operator):
    for first, second in product(range(1, 7), repeat=2):
        for target in range(0, 8):
            values = iter([first - 1, second - 1])
            result = roll(
                parse(f"2d6{operator}{target}"), {}, lambda sides, source=values: next(source)
            )
            expected = (
                (first >= target) + (second >= target)
                if operator == ">>"
                else (first <= target) + (second <= target)
            )
            assert result.total == expected


@pytest.mark.parametrize(
    "source",
    [
        "5d6>>",
        "5d6 >> ",
        "5d6>>>4",
        "5d6> >4",
        "5d6>4",
        "5d6 > 4",
        "5d6 >> FOR",
        "5d6>>-1",
        "5d6>>4.5",
        "5d6>>4abc",
        "5d6>>4+1",
        "5d6>>4 + 1",
        "5d6>>4>>2",
        "5d6>>4 >> 2",
        "5d6+FOR>>4",
        "5d6+1>>4",
        "5d6+d4>>4",
        "5d6-d4>>4",
        "5d6>>1000000001",
        "5d6>>" + "9" * 500,
        "101d6>>4",
        "21#5d6>>4",
        "5d1>>1",
        "2d20kh1>>4",
        "5d6<<",
        "5d6 << ",
        "5d6<<<3",
        "5d6< <3",
        "5d6<3",
        "5d6 < 3",
        "5d6 << FOR",
        "5d6<<-1",
        "5d6<<3.5",
        "5d6<<3abc",
        "5d6<<3+1",
        "5d6<<3 + 1",
        "5d6<<3<<2",
        "5d6<<3 >> 2",
        "5d6+FOR<<3",
        "5d6+1<<3",
        "5d6+d4<<3",
        "5d6-d4<<3",
        "5d6<<1000000001",
        "21#5d6<<3",
    ],
)
def test_invalid_count_no_database_or_randomness(source, monkeypatch):
    def forbidden(*args):
        pytest.fail("Expressão inválida não deve sortear")

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


@pytest.mark.parametrize("expression,expected", [("5d6>>4", 3), ("5d6<<3", 2)])
def test_handler_counts_with_no_database(monkeypatch, expression, expected):
    values = iter([5, 4, 3, 1, 0])
    monkeypatch.setattr(
        "message_handler.roll_many",
        lambda expression, attributes: roll_many(
            expression, attributes, lambda sides: next(values)
        ),
    )
    repo = SimpleNamespace(attributes=AsyncMock())
    message = SimpleNamespace(
        content=expression,
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(bot=False),
        webhook_id=None,
        reply=AsyncMock(),
    )
    asyncio.run(MessageHandler(repo).handle(message))
    repo.attributes.assert_not_awaited()
    assert message.reply.await_args.kwargs["content"].startswith(f"`\u00a0{expected}\u00a0` ⟵")
    assert message.reply.await_args.kwargs["allowed_mentions"].everyone is False


def test_hundred_results_and_emoji_comment_bounded():
    calls = []

    def random_source(sides):
        calls.append(sides)
        return sides - 1

    results = roll_many(parse("100#d100000>>4 " + "😀" * 900), {}, random_source)
    messages = format_batch(results)
    output = "".join(messages)
    assert len(calls) == 100
    assert all(text_length(message) <= 1900 for message in messages)
    assert output.count(">> 4") == 100
    assert "sucesso" not in output and "fracasso" not in output
    assert output.count("**100000**") == 100
    assert output.count("😀") == 900


def test_non_roll_and_normal_comments_unchanged():
    assert parse("Vou usar 5d6>>4") is None
    expression = parse("d20 comentário sobre 5d6>>4")
    assert expression.count_target is None
    assert expression.comment == "comentário sobre 5d6>>4"


def test_simple_comparison_is_not_silently_treated_as_comment():
    with pytest.raises(DiceError):
        parse("d20 >= 15")


def test_discord_mention_comment_not_confused_with_comparison():
    expression = parse("5d6>>4 <@123456789012345678>")
    assert expression.count_target == 4
    assert expression.comment == "<@123456789012345678>"
    result = roll(expression, {}, lambda sides: 0)
    assert "<@123456789012345678>" not in "".join(format_result(result))


def test_lower_count_exact_example_without_labels():
    values = iter([5, 4, 2, 1, 0])
    result = roll(parse("5d6<<3"), {}, lambda sides: next(values))
    assert result.total == 3
    assert format_result(result) == ("`\u00a03\u00a0` ⟵ [**6**, 5, 3, 2, **1**] 5d6 << 3",)


@pytest.mark.parametrize(
    "source,expected",
    [
        ("3d6<<0", 0),
        ("3d6<<1", 3),
        ("3d6<<6", 3),
        ("3d6<<7", 3),
        ("3d6<<1000000000", 3),
        ("100d100000<<1", 100),
        ("100#d6<<1", 1),
    ],
)
def test_lower_count_boundaries(source, expected):
    results = roll_many(parse(source), {}, lambda sides: 0)
    assert all(result.total == expected for result in results)


def test_lower_parser_spaces_case_and_comment():
    expression = parse("  2#5D6 << 03 teste")
    assert expression.repeat_count == 2
    assert expression.count_operator == "<<"
    assert expression.count_target == 3
    assert expression.comment == "teste"
    assert expression.attributes == set()


def test_lower_repetitions_preserve_order():
    values = iter([0, 3, 5, 2, 1, 0])
    results = roll_many(parse("2#3d6<<3 atacar"), {}, lambda sides: next(values))
    assert [result.total for result in results] == [1, 3]
    assert format_batch(results) == (
        "`\u00a01\u00a0` ⟵ [**6**, 4, **1**] 3d6 << 3\n"
        "`\u00a03\u00a0` ⟵ [3, 2, **1**] 3d6 << 3\n> atacar",
    )


@pytest.mark.parametrize("operator", [">>", "<<"])
@pytest.mark.parametrize("raw", [0, 5])
def test_no_automatic_success_or_failure_labels(operator, raw):
    result = roll(parse(f"d6{operator}3"), {}, lambda sides: raw)
    output = "".join(format_result(result))
    assert "sucesso" not in output
    assert "fracasso" not in output
    assert "·" not in output
    assert output.endswith(f"d6 {operator} 3")


def test_user_comment_kept_even_if_it_contains_label_words():
    result = roll(parse("d6<<3 sucesso ou fracasso"), {}, lambda sides: 0)
    assert format_result(result)[0].endswith("\n> sucesso ou fracasso")
