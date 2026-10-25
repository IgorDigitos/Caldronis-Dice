import secrets
from collections.abc import Callable, Mapping

from dice.models import Detail, DiceError, Expression, RollResult


def roll(
    expression: Expression,
    attributes: Mapping[str, int],
    random_source: Callable[[int], int] = secrets.randbelow,
) -> RollResult:
    # Validar tudo antes do primeiro sorteio.
    missing = expression.attributes - attributes.keys()
    if missing:
        raise DiceError("Atributo não cadastrado: " + ", ".join(sorted(missing)) + ".")
    details = []
    for term in expression.terms:
        if term.kind == "dice":
            sides = int(term.value)
            values = tuple(random_source(sides) + 1 for _ in range(term.count))
            label = f"{term.count}d{sides}"
        elif term.kind == "attribute":
            values = (attributes[str(term.value)],)
            label = str(term.value)
        else:
            values = (int(term.value),)
            label = "Constante"
        details.append(Detail(label, term.sign, values, term.sign * sum(values)))
    return RollResult(expression, tuple(details), sum(item.subtotal for item in details))


def roll_many(
    expression: Expression,
    attributes: Mapping[str, int],
    random_source: Callable[[int], int] = secrets.randbelow,
) -> tuple[RollResult, ...]:
    """Executa as repetições de uma expressão previamente validada pelo parser."""
    return tuple(
        roll(expression, attributes, random_source) for _ in range(expression.repeat_count or 1)
    )
