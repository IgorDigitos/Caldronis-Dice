import pytest

from dice.models import DiceError
from dice.parser import parse


@pytest.mark.parametrize(
    "source",
    [
        "d2",
        "d30",
        "d100000",
        "2d30+5",
        "d30+FOR",
        "d30+FOR+d4",
        "d30+FOR-CON",
        "3d6-2",
        " D20 + for + d4",
        "100d2",
        "d20-1000000000",
    ],
)
def test_valid(source):
    assert parse(source) is not None


@pytest.mark.parametrize(
    "source", ["Vou usar d30+FOR", "Ataque: d30+8", "!d30", "/r d30", "-d30", "", "d", "texto"]
)
def test_ignored(source):
    assert parse(source) is None


@pytest.mark.parametrize(
    "source",
    [
        "d1",
        "d100001",
        "101d20",
        "0d20",
        "d30+",
        "d30abc",
        "d20+FOR-CON-",
        "d20++2",
        "d20*2",
        "d20 * 2",
        "d20/2",
        "d20+2.5",
        "d20+()",
        "d20+-2",
        "d20+1000000001",
        "d20+" + "A" * 33,
        "99d20+2d4",
        "d20" + "+1" * 30,
        "d20 " + "x" * 1000,
        "d" + "9" * 500,
    ],
)
def test_invalid(source):
    with pytest.raises(DiceError):
        parse(source)


@pytest.mark.parametrize(
    "source,expression,comment",
    [
        ("d30+FOR atacar o guarda", "d30+FOR", "atacar o guarda"),
        ("  d20 teste de percepção", "d20", "teste de percepção"),
        ("d30 + FOR + d4 comentário + texto", "d30 + FOR + d4", "comentário + texto"),
    ],
)
def test_comments(source, expression, comment):
    result = parse(source)
    assert result.original == expression
    assert result.comment == comment


def test_attributes_and_subtraction_not_swallowed():
    result = parse("d30+for-con")
    assert result.attributes == {"FOR", "CON"}
    assert result.terms[-1].sign == -1


def test_attribute_with_dice_prefix_is_usable():
    assert parse("d20+D20_MOD").attributes == {"D20_MOD"}
