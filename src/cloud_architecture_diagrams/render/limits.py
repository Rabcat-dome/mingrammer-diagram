"""Render bounds (NFR-009). Callers cannot widen them, and M4-04 refines them with measurements."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Limits:
    view_entities: int = 200
    view_relationships: int = 300
    group_depth: int = 16
    wall_seconds: float = 55
    cpu_seconds: int = 45
    memory_bytes: int = 1024**3
    temporary_bytes: int = 256 * 1024**2
    file_bytes: int = 16 * 1024**2
    pixels: int = 32_000_000
    sampling_seconds: float = 0.1

    def report(self) -> dict[str, float]:
        return {key: value for key, value in asdict(self).items() if key != "sampling_seconds"}


LIMITS = Limits()
