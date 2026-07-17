"""Eden Shadow — a self-contained turn-based floor-climbing RPG.

Standard library only. Deterministic when seeded. The only file it touches
is its local JSON save. Part of the wha-spell-simulator / Shadow Garden
constellation as a purely local game slice: no network, no external writes.
"""

__version__ = "0.1.0"

from eden_shadow.game import Game, main  # noqa: F401
