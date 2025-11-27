from dataclasses import dataclass


@dataclass(frozen=True)
class GridfinityConfig:
    """Gridfinity specification constants."""

    tolerance: float = 0.25
    unit_size: float = 42.0
    height_unit: float = 7.0
    base_height: float = 4.75
    outer_fillet: float = 4
    lip_steps: tuple[tuple[float, float], ...] = (
        (-2.6, 0),
        (0.7, 0.7),
        (0, 1.8),
        (1.9, 1.9),
    )
    base_steps: tuple[tuple[float, float], ...] = (
        (-2.95, 0),
        (0.8, 0.8),
        (0, 1.8),
        (2.15, 2.15),
    )
