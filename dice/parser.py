"""[N#] expressão [comentário]; contagem: um grupo de dados >> ou << alvo inteiro."""

import re

from dice.limits import (
    MAX_ATTRIBUTE_NAME,
    MAX_BATCH_TERMS,
    MAX_DICE,
    MAX_INPUT,
    MAX_INTEGER,
    MAX_REPETITIONS,
    MAX_TERMS,
)
from dice.models import DiceError, Expression, Term

START = re.compile(r"(?:[0-9]+#|#\s*[0-9]*d[0-9]+|[0-9]*d[0-9]+)", re.IGNORECASE | re.ASCII)
REPEAT = re.compile(r"([0-9]+)#", re.ASCII)
DIE = re.compile(r"([0-9]*)d([0-9]+)(!)?", re.IGNORECASE | re.ASCII)
INTEGER = re.compile(r"[0-9]+", re.ASCII)
ATTRIBUTE = re.compile(r"[A-Za-z][A-Za-z0-9_]*", re.ASCII)


def _starts_operator(text: str) -> bool:
    # Não confundir menções/links/emoji do Discord (<@...>, <https:...>) com comparação.
    return text[0] in "+-*/%=^()#>!" or re.match(r"<(?:[<=]|\s|[0-9+-]|$)", text) is not None


def _parse_count(
    source: str, position: int, terms: list[Term], repeat_count: int | None
) -> Expression:
    if len(terms) != 1 or terms[0].kind != "dice":
        raise DiceError("Na contagem, use um único grupo sem somas ou atributos. Exemplo: 5d6!>>4.")
    count_operator = ">>" if source.startswith(">>", position) else "<<"
    position += 2
    while position < len(source) and source[position].isspace():
        position += 1
    match = INTEGER.match(source, position)
    if not match or len(match.group()) > 10 or int(match.group()) > MAX_INTEGER:
        raise DiceError(f"Depois de {count_operator}, use um alvo inteiro de 0 a 1.000.000.000.")
    end = match.end()
    if end < len(source) and not source[end].isspace():
        raise DiceError("Após o alvo, use somente um comentário separado por espaço.")
    comment = source[end:].strip()
    if comment and _starts_operator(comment):
        raise DiceError("A contagem termina no alvo; não acrescente operadores depois dele.")
    return Expression(
        source[:end], comment, tuple(terms), repeat_count, int(match.group()), count_operator
    )


def is_candidate(content: str) -> bool:
    # Não percorrer uma mensagem arbitrariamente grande antes do limite.
    return START.match(content[: MAX_INPUT + 1].lstrip()) is not None


def parse(content: str) -> Expression | None:
    if not is_candidate(content):
        return None
    if len(content) > MAX_INPUT:
        raise DiceError(f"Mensagem excede {MAX_INPUT} caracteres.")
    source = content.lstrip()
    repeat_count = None
    if "#" in source.split(maxsplit=1)[0]:
        repeat = REPEAT.match(source)
        if not repeat or len(repeat.group(1)) > 3:
            raise DiceError("Use N#expressão. Exemplo: 3#d20+5 para três rolagens separadas.")
        repeat_count = int(repeat.group(1))
        if not 1 <= repeat_count <= MAX_REPETITIONS:
            raise DiceError("Use de 1 a 100 repetições; o conjunto pode sortear até 100 dados.")
        source = source[repeat.end() :].lstrip()
        if not DIE.match(source):
            raise DiceError("Depois de #, comece por um dado. Exemplo: 3#d20+5.")
    terms: list[Term] = []
    position = 0
    sign = 1
    dice_count = 0
    while True:
        match = DIE.match(source, position)
        if (
            match
            and terms
            and match.end() < len(source)
            and (source[match.end()].isalpha() or source[match.end()] == "_")
        ):
            match = None
        if match:
            count_text, sides_text, bang = match.groups()
            # Limitar dígitos antes de converter inteiros vindos do chat.
            if len(count_text) > 3 or len(sides_text) > 6:
                raise DiceError("Quantidade ou lados fora dos limites.")
            count, sides = int(count_text or "1"), int(sides_text)
            if not 1 <= count <= MAX_DICE or not 2 <= sides <= 100_000:
                raise DiceError("Use 1 a 100 dados e 2 a 100.000 lados.")
            dice_count += count
            if dice_count * (repeat_count or 1) > MAX_DICE:
                raise DiceError("Máximo de 100 dados no total, contando todas as repetições.")
            term = Term(sign, "dice", sides, count, bool(bang))
        else:
            match = INTEGER.match(source, position)
            if match:
                raw = match.group()
                if len(raw) > 10 or int(raw) > MAX_INTEGER:
                    raise DiceError("Inteiro excede o limite de 1.000.000.000.")
                term = Term(sign, "integer", int(raw))
            else:
                match = ATTRIBUTE.match(source, position)
                if not match or len(match.group()) > MAX_ATTRIBUTE_NAME:
                    raise DiceError("Esperado dado, inteiro ou atributo de até 32 caracteres.")
                term = Term(sign, "attribute", match.group().upper())
        terms.append(term)
        if len(terms) > MAX_TERMS:
            raise DiceError(f"Máximo de {MAX_TERMS} termos por expressão.")
        if len(terms) * (repeat_count or 1) > MAX_BATCH_TERMS:
            raise DiceError("Máximo de 100 termos no conjunto de repetições.")
        position = match.end()
        expression_end = position
        while position < len(source) and source[position].isspace():
            position += 1
        if position == len(source):
            return Expression(source[:expression_end], "", tuple(terms), repeat_count)
        char = source[position]
        if source.startswith((">>", "<<"), position):
            return _parse_count(source, position, terms, repeat_count)
        if char in "+-":
            sign = 1 if char == "+" else -1
            position += 1
            while position < len(source) and source[position].isspace():
                position += 1
            continue
        if position > expression_end:
            # Operadores não suportados nunca viram comentário silenciosamente.
            if _starts_operator(source[position:]):
                raise DiceError("Operador não suportado. Use +, -, dados>>alvo ou dados<<alvo.")
            return Expression(
                source[:expression_end], source[position:], tuple(terms), repeat_count
            )
        raise DiceError("Token inválido; separe o comentário com um espaço.")
