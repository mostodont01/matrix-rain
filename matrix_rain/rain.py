"""Digital rain simulation, independent of the terminal (easy to test)."""

from __future__ import annotations

import random
from dataclasses import dataclass

# Half-width katakana, digits and a few symbols; all one terminal cell wide.
GLYPHS = (
    [chr(c) for c in range(0xFF66, 0xFF9E)]
    + list("0123456789")
    + list(":.=*+-<>|¦_\"")
)
ASCII_GLYPHS = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:.=*+-<>|_")

# Brightness levels of a cell: HEAD is the falling tip, then the trail fades.
HEAD, BRIGHT, NORMAL, DIM = 0, 1, 2, 3


@dataclass
class Drop:
    x: int
    y: float  # row of the head (may be above or below the screen)
    speed: float  # rows per tick
    length: int


class Rain:
    def __init__(
        self,
        width: int,
        height: int,
        density: float = 0.7,
        ascii_only: bool = False,
        rng: random.Random | None = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.glyphs = ASCII_GLYPHS if ascii_only else GLYPHS
        self.density = density
        self.spawning = True
        self.drops: list[Drop] = []
        self.width = self.height = 0
        self.chars: list[list[str]] = []
        self.resize(width, height)

    # -- setup -------------------------------------------------------------
    def resize(self, width: int, height: int) -> None:
        self.width, self.height = max(1, width), max(1, height)
        self.chars = [
            [self.rng.choice(self.glyphs) for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.drops = [d for d in self.drops if d.x < self.width]

    def _new_drop(self, x: int, y: float | None = None) -> Drop:
        length = self.rng.randint(max(4, self.height // 4), max(6, self.height))
        if y is None:
            y = -self.rng.uniform(0, self.height / 2)
        return Drop(x, y, self.rng.uniform(0.3, 1.0), length)

    def seed_screen(self) -> None:
        """Start with rain already falling, so the screen isn't empty at first."""
        for x in range(self.width):
            if self.rng.random() < self.density * 0.6:
                self.drops.append(self._new_drop(x, self.rng.uniform(0, self.height)))

    # -- simulation --------------------------------------------------------
    def step(self) -> None:
        for d in self.drops:
            d.y += d.speed
        self.drops = [d for d in self.drops if d.y - d.length < self.height]

        if self.spawning:
            busy = {d.x for d in self.drops if d.y - d.length < 2}
            for x in range(self.width):
                if x not in busy and self.rng.random() < self.density * 0.04:
                    self.drops.append(self._new_drop(x))

        # A few glyphs flicker to other symbols every tick.
        for _ in range(max(1, self.width * self.height // 60)):
            r = self.rng.randrange(self.height)
            c = self.rng.randrange(self.width)
            self.chars[r][c] = self.rng.choice(self.glyphs)

    def stop(self) -> None:
        """Stop new drops; the ones on screen keep falling until they're gone."""
        self.spawning = False

    @property
    def finished(self) -> bool:
        return not self.spawning and not self.drops

    def cells(self) -> dict[tuple[int, int], tuple[str, int]]:
        """Visible cells: (row, col) -> (glyph, brightness level)."""
        out: dict[tuple[int, int], tuple[str, int]] = {}
        for d in self.drops:
            head = int(d.y)
            for i in range(d.length):
                row = head - i
                if row < 0:
                    break
                if row >= self.height:
                    continue
                if i == 0:
                    level = HEAD
                elif i < d.length * 0.25:
                    level = BRIGHT
                elif i < d.length * 0.65:
                    level = NORMAL
                else:
                    level = DIM
                key = (row, d.x)
                # Overlapping drops: keep the brighter one.
                if key not in out or level < out[key][1]:
                    out[key] = (self.chars[row][d.x], level)
        return out
