import asyncio
import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from dice.parser import parse
from dice.roller import roll, roll_many
from message_handler import MessageHandler, format_result, text_length


def message(content="d30", *, guild=True, bot=False, webhook=None):
    return SimpleNamespace(
        content=content,
        guild=SimpleNamespace(id=1) if guild else None,
        author=SimpleNamespace(id=10, bot=bot, display_name="Jogador"),
        webhook_id=webhook,
        reply=AsyncMock(),
    )


@pytest.mark.parametrize("source", ["Vou usar d30", "Ataque: d30", "!d30", "/r d30", "-d30"])
def test_non_roll_never_queries_database(source):
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message(source)
    asyncio.run(MessageHandler(repo).handle(msg))
    repo.attributes.assert_not_awaited()
    msg.reply.assert_not_awaited()


@pytest.mark.parametrize("options", [{"guild": False}, {"bot": True}, {"webhook": 9}])
def test_ignored_sources(options):
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message(**options)
    asyncio.run(MessageHandler(repo).handle(msg))
    repo.attributes.assert_not_awaited()
    msg.reply.assert_not_awaited()


def test_plain_roll_no_database():
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message("2d30+5")
    asyncio.run(MessageHandler(repo).handle(msg))
    repo.attributes.assert_not_awaited()
    payload = msg.reply.await_args.kwargs
    assert "⟵ [" in payload["content"]
    assert "embed" not in payload
    assert not payload["mention_author"]
    assert payload["allowed_mentions"].everyone is False


@pytest.mark.parametrize("source", ["d30+", "d1", "d100001", "101d20", "d30abc"])
def test_invalid_no_database(source):
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message(source)
    asyncio.run(MessageHandler(repo).handle(msg))
    repo.attributes.assert_not_awaited()
    assert "Não foi possível" in msg.reply.await_args.kwargs["content"]
    assert msg.reply.await_args.kwargs["delete_after"] == 15


def test_missing_attribute():
    repo = SimpleNamespace(attributes=AsyncMock(return_value={}))
    msg = message("d30+FOR")
    asyncio.run(MessageHandler(repo).handle(msg))
    repo.attributes.assert_awaited_once_with(1, 10)
    assert "FOR" in msg.reply.await_args.kwargs["content"]


@pytest.mark.parametrize("error", [sqlite3.OperationalError("sensitive"), OSError("sensitive")])
def test_database_failure_is_discreet(error):
    repo = SimpleNamespace(attributes=AsyncMock(side_effect=error))
    msg = message("d30+FOR")
    asyncio.run(MessageHandler(repo).handle(msg))
    assert "sensitive" not in msg.reply.await_args.kwargs["content"]
    assert "Banco indisponível" in msg.reply.await_args.kwargs["content"]


@pytest.mark.parametrize("source", ["d30", "d30+", "d30+FOR"])
def test_network_failure_does_not_escape(source):
    repo = SimpleNamespace(attributes=AsyncMock(return_value={}))
    msg = message(source)
    msg.reply.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "")
    asyncio.run(MessageHandler(repo).handle(msg))
    assert msg.reply.await_count == 1


def test_large_reply_and_escaping():
    source = "100d100000" + "+1000000000" * 29 + " " + "@everyone **texto** " * 20
    messages = format_result(roll(parse(source), {}, lambda sides: sides - 1))
    assert len(messages) > 1
    assert all(text_length(content) <= 1900 for content in messages)
    output = "".join(messages)
    assert "@everyone" not in output
    assert output.count("**100000**") == 100
    assert output.count("+ 1000000000") == 29


def test_matches_reference_style():
    values = iter([29, 19])
    result = roll(parse("2d30+8"), {}, lambda sides: next(values))
    assert format_result(result) == ("`\u00a058\u00a0` ⟵ [**30**, 20] 2d30 + 8",)


def test_descending_display_preserves_roll_and_total():
    values = iter([1, 29, 6, 6, 0])
    result = roll(parse("5d30+8"), {}, lambda sides: next(values))
    assert format_result(result) == ("`\u00a055\u00a0` ⟵ [**30**, 7, 7, 2, **1**] 5d30 + 8",)
    assert result.details[0].values == (2, 30, 7, 7, 1)
    assert result.total == 55


def test_descending_order_is_per_group_even_when_subtracting():
    values = iter([0, 4, 2, 1, 5])
    result = roll(parse("3d6-2d6+FOR"), {"FOR": 8}, lambda sides: next(values))
    assert format_result(result) == (
        "`\u00a09\u00a0` ⟵ [5, 3, **1**] 3d6 - [**6**, 2] 2d6 + FOR\nFOR=+8",
    )


def test_multiple_groups_and_attribute_values():
    values = iter([17, 2])
    result = roll(
        parse("d30+for-CON+d4-2 atacar o guarda"), {"FOR": 8, "CON": -3}, lambda sides: next(values)
    )
    assert format_result(result) == (
        "`\u00a030\u00a0` ⟵ [18] d30 + for - CON + [3] d4 - 2\nFOR=+8 · CON=-3\n> atacar o guarda",
    )


def test_attribute_that_looks_like_dice():
    result = roll(parse("d20+D20_MOD"), {"D20_MOD": 3}, lambda sides: 0)
    assert format_result(result) == ("`\u00a04\u00a0` ⟵ [**1**] d20 + D20_MOD\nD20_MOD=+3",)


def test_single_digit_total_is_centered_like_reference():
    result = roll(parse("d4"), {}, lambda sides: 1)
    assert format_result(result) == ("`\u00a02\u00a0` ⟵ [2] d4",)


@pytest.mark.parametrize("sides", [2, 4, 30, 100000])
@pytest.mark.parametrize("maximum", [False, True])
def test_natural_critical_and_failure_before_modifiers(sides, maximum):
    natural = sides if maximum else 1
    result = roll(parse(f"d{sides}+8"), {}, lambda size: natural - 1)
    output = "".join(format_result(result))
    assert f"[**{natural}**]" in output
    assert result.total == natural + 8
    assert output.split("`")[1].strip() == str(natural + 8)


def test_only_natural_dice_receive_critical_highlight():
    result = roll(parse("d4+4+FOR"), {"FOR": 1}, lambda sides: 1)
    output = "".join(format_result(result))
    assert result.total == 7
    assert "[2]" in output
    assert "**" not in output  # Constante 4 e atributo 1 não são resultados naturais.


def test_maximum_and_one_bold_in_same_group():
    values = iter([0, 3])
    result = roll(parse("2d4"), {}, lambda sides: next(values))
    assert format_result(result) == ("`\u00a05\u00a0` ⟵ [**4**, **1**] 2d4",)


def test_unicode_comment_and_markdown_are_bounded():
    messages = format_result(roll(parse("d20 " + "😀" * 990), {}, lambda sides: 0))
    assert all(text_length(content) <= 1900 for content in messages)
    assert "".join(messages).count("😀") == 990
    for comment in ["@everyone **texto**", "<@123456789012345678>", "`código`"]:
        output = "".join(format_result(roll(parse("d20 " + comment), {}, lambda sides: 0)))
        assert discord.utils.escape_mentions(comment) != comment or "\\" in output


@pytest.mark.parametrize("source", ["d30+FOR atacar o guarda", "2#d30+FOR atacar o guarda"])
def test_saved_attribute_updated_in_message_path(tmp_path, monkeypatch, source):
    from profiles.repository import Repository
    from profiles.service import Actor, ProfileService

    monkeypatch.setattr(
        "message_handler.roll_many",
        lambda expression, attributes: roll_many(expression, attributes, lambda sides: 0),
    )

    async def scenario():
        repo = Repository(tmp_path / "integration.sqlite3")
        await repo.initialize()
        service = ProfileService(repo)
        for value in [8, 10]:
            await service.define(Actor(1, 10), 10, "FOR", value)
            msg = message(source)
            await MessageHandler(Repository(repo.path)).handle(msg)
            output = msg.reply.await_args.kwargs["content"]
            assert output.split("`")[1].strip() == str(value + 1)
            assert f"FOR=+{value}" in output
            assert "atacar o guarda" in output

    asyncio.run(scenario())


def test_stop_sending_continuations_after_failure():
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message("100d100000" + "+1000000000" * 29 + " " + "😀" * 650)
    msg.reply.side_effect = OSError("offline")
    asyncio.run(MessageHandler(repo).handle(msg))
    assert msg.reply.await_count == 1


def test_large_reply_does_not_roll_again(monkeypatch):
    values = iter([99999] * 100)
    calls = []

    def random_source(sides):
        calls.append(sides)
        return next(values)

    monkeypatch.setattr(
        "message_handler.roll_many",
        lambda expression, attributes: roll_many(expression, attributes, random_source),
    )
    repo = SimpleNamespace(attributes=AsyncMock())
    msg = message("100d100000" + "+1000000000" * 29 + " " + "😀" * 650)
    asyncio.run(MessageHandler(repo).handle(msg))
    assert len(calls) == 100
    assert msg.reply.await_count > 1
    assert all(text_length(call.kwargs["content"]) <= 1900 for call in msg.reply.await_args_list)
    assert all(
        call.kwargs["allowed_mentions"].everyone is False for call in msg.reply.await_args_list
    )
