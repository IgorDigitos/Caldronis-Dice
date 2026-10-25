from dataclasses import dataclass


class DiceError(ValueError):
    """Erro seguro para exibição ao jogador."""


@dataclass(frozen=True)
class Term:
    sign: int
    kind: str
    value: int | str
    count: int = 0


@dataclass(frozen=True)
class Expression:
    original: str
    comment: str
    terms: tuple[Term, ...]
    repeat_count: int | None = None

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
    expression: Expression
    details: tuple[Detail, ...]
    total: int
