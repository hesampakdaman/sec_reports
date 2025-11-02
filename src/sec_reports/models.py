from dataclasses import dataclass
from pathlib import Path
from typing import override


@dataclass(frozen=True)
class CIK:
    value: str

    def __post_init__(self):
        if not self.value.isdigit():
            raise ValueError(f"CIK must be numeric, got {self.value!r}")

        if len(self.value) < 10:
            raise ValueError(f"CIK must be 10 digits, got {len(self.value)}")

    @override
    def __str__(self) -> str:
        return f"{int(self.value):010d}"


@dataclass(frozen=True)
class Filing:
    cik: CIK
    url: str
    path: Path
