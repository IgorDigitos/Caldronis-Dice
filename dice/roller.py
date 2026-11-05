import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from operator import ge, le

from dice.limits import MAX_EXPLOSIONS
from dice.models import Detail, DiceError, Expression, RollResult


@dataclass
class _RollBudget:
    """Dados iniciais já são limitados pelo parser; aqui só se controlam os extras."""

    extra_remaining: int = MAX_EXPLOSIONS

    def draw(self, sides: int, random_source: Callable[[int], int], extra: bool = False) -> int:
        if extra:
            if self.extra_remaining == 0:
                raise DiceError(
                    f"As explosões exigiram mais de {MAX_EXPLOSIONS} sorteios extras, "
                    "contando todas as repetições. Nenhum resultado parcial foi exibido; "
                    "use menos dados explosivos ou repetições."
                )
            self.extra_remaining -= 1
        return random_source(sides) + 1


def _roll(
    expression: Expression,
    attributes: Mapping[str, int],
    random_source: Callable[[int], int],
    budget: _RollBudget,
) -> RollResult:
    # Validar tudo antes do primeiro sorteio.
    missing = expression.attributes - attributes.keys()
    if missing:
        raise DiceError("Atributo não cadastrado: " + ", ".join(sorted(missing)) + ".")
    details = []
    for term in expression.terms:
        if term.kind == "dice":
            sides = int(term.value)
            draws = []
            explodes = term.exploding and expression.count_target is None
            for _ in range(term.count):
                value = budget.draw(sides, random_source)
                draws.append(value)
                while explodes and value == sides:
                    value = budget.draw(sides, random_source, extra=True)
                    draws.append(value)
            values = tuple(draws)
            label = f"{term.count}d{sides}" + ("!" if term.exploding else "")
        elif term.kind == "attribute":
            values = (attributes[str(term.value)],)
            label = str(term.value)
        else:
            values = (int(term.value),)
            label = "Constante"
        details.append(Detail(label, term.sign, values, term.sign * sum(values)))
    if expression.count_target is not None:
        compare = ge if expression.count_operator == ">>" else le
        total = 0
        for term, item in zip(expression.terms, details, strict=True):
            critical = term.value if expression.count_operator == ">>" else 1
            total += sum(
                2 if term.exploding and value == critical else 1
                for value in item.values
                if compare(value, expression.count_target)
            )
    else:
        total = sum(item.subtotal for item in details)
        if expression.per_die_bonus is not None:
            total += len(details[0].values) * expression.per_die_bonus
    return RollResult(expression, tuple(details), total)


def roll(
    expression: Expression,
    attributes: Mapping[str, int],
    random_source: Callable[[int], int] = secrets.randbelow,
) -> RollResult:
    return _roll(expression, attributes, random_source, _RollBudget())


def roll_many(
    expression: Expression,
    attributes: Mapping[str, int],
    random_source: Callable[[int], int] = secrets.randbelow,
) -> tuple[RollResult, ...]:
    """Executa um conjunto validado, com orçamento global incluindo as explosões."""
    budget = _RollBudget()
    return tuple(
        _roll(expression, attributes, random_source, budget)
        for _ in range(expression.repeat_count or 1)
    )
