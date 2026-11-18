import random

import pytest

from matrix_rain.cli import parse_args
from matrix_rain.rain import ASCII_GLYPHS, DIM, HEAD, Rain


def make(w=40, h=20, **kw):
    return Rain(w, h, rng=random.Random(1), **kw)


def test_cells_stay_on_screen():
    rain = make()
    rain.seed_screen()
    for _ in range(200):
        rain.step()
        for (y, x), (ch, level) in rain.cells().items():
            assert 0 <= y < rain.height and 0 <= x < rain.width
            assert HEAD <= level <= DIM
            assert len(ch) == 1


def test_rain_keeps_falling_while_spawning():
    rain = make()
    for _ in range(300):
        rain.step()
    assert rain.drops
    assert not rain.finished


def test_drains_after_stop():
    rain = make()
    rain.seed_screen()
    for _ in range(50):
        rain.step()
    rain.stop()
    for _ in range(1000):
        if rain.finished:
            break
        rain.step()
    assert rain.finished
    assert rain.cells() == {}


def test_each_drop_has_one_head():
    rain = make(w=10, h=30)
    rain.drops.clear()
    rain.drops.append(rain._new_drop(3, y=15))
    heads = [k for k, (_, lvl) in rain.cells().items() if lvl == HEAD]
    assert heads == [(15, 3)]


def test_ascii_mode():
    rain = make(ascii_only=True)
    assert all(ch in ASCII_GLYPHS for row in rain.chars for ch in row)


def test_resize_drops_offscreen_columns():
    rain = make(w=40)
    rain.seed_screen()
    rain.resize(10, 5)
    assert all(d.x < 10 for d in rain.drops)
    assert len(rain.chars) == 5 and len(rain.chars[0]) == 10
    rain.step()
    rain.cells()


def test_parse_args_defaults_and_limits():
    a = parse_args([])
    assert a.duration == 6.0 and not a.forever and not a.cancellable
    assert parse_args(["--density", "50"]).density == 2.0
    with pytest.raises(SystemExit):
        parse_args(["--speed", "0"])
