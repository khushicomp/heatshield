"""Shared Phase 3 input provenance and validation; no measured defaults."""
from dataclasses import dataclass
from enum import Enum
import math


class InputKind(str, Enum):
    SYNTHETIC = 'synthetic'
    USER_SUPPLIED = 'user_supplied_unvalidated'


def identifier(value: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError('Identifiers must be nonempty strings without boundary whitespace')


def finite(value: float, name: str, minimum: float | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f'{name} must be a finite number')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (minimum is not None and value < minimum):
        raise ValueError(f'{name} must be finite' + (f' and >= {minimum}' if minimum is not None else ''))


def integer(value: int, name: str, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')


@dataclass(frozen=True)
class Provenance:
    kind: InputKind
    description: str

    def __post_init__(self):
        if not isinstance(self.kind, InputKind):
            raise ValueError('Explicit InputKind required')
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError('A source or assumption description is required')

    def to_dict(self):
        return {'kind': self.kind.value, 'description': self.description}


def provenance(value: Provenance) -> None:
    if not isinstance(value, Provenance):
        raise ValueError('Explicit Provenance required')
