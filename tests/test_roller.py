import pytest

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll


def test_individual_dice_and_total():
    values = iter([11, 26])
    result = roll(parse("2d30+5"), {}, lambda sides: next(values))
    assert result.details[0].values == (12, 27)
    assert result.total == 44


def test_negative_attributes_and_signs():
    result = roll(parse("d30+FOR-CON+d4-2"), {"FOR": 8, "CON": -3}, lambda sides: 0)
    assert result.total == 11
    assert result.details[2].subtotal == 3


def test_missing_attribute_before_randomness():
    def forbidden(sides):
        pytest.fail("Não deveria sortear com atributo ausente")

    with pytest.raises(DiceError, match="CON"):
        roll(parse("d30+FOR-CON"), {"FOR": 8}, forbidden)


@pytest.mark.parametrize("source,total", [("d2", 2), ("d100000", 100000), ("100d2", 200)])
def test_upper_boundary(source, total):
    assert roll(parse(source), {}, lambda sides: sides - 1).total == total
