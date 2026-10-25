from dataclasses import dataclass
from typing import Literal


class DiceError(ValueError):
    """Erro seguro para exibição ao jogador."""


@dataclass(frozen=True)
class Term:
    sign: int
    kind: str
    value: int | str
    count: int = 0
    exploding: bool = False


@dataclass(frozen=True)
class Expression:
    original: str
    comment: str
    terms: tuple[Term, ...]
    repeat_count: int | None = None
    count_target: int | None = None
    count_operator: Literal[">>", "<<"] = ">>"

    @property
    def attributes(self) -> set[str]:
        return {str(term.value) for term in self.terms if term.kind == "attribute"}


@dataclass(frozen=True)
class Detail:
    label: str
    sign: int
    values: tuple[int, ...]
    subtotal: int


@dataclass(frozen=True)
class RollResult:
    """Total é a soma normal ou a quantidade de dados que atendem ao alvo."""

    expression: Expression
    details: tuple[Detail, ...]
    total: int
