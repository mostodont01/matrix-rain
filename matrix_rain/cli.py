"""`matrix`: digital rain in the terminal, sl style.

Like `sl`, it plays for a few seconds and ignores Ctrl+C. Use -c to allow
interrupting, or -f to let it rain until you press q.
"""

from __future__ import annotations

import argparse
import curses
import locale
import signal
import time

from . import __version__
from .rain import BRIGHT, DIM, HEAD, NORMAL, Rain

FPS = 20


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="matrix",
        description="Digital rain in your terminal. Like sl, you can't stop it.",
    )
    p.add_argument("-d", "--duration", type=float, default=6.0,
                   help="seconds of rain before it drains away (default 6)")
    p.add_argument("-f", "--forever", action="store_true",
                   help="rain until q / Esc / Ctrl+C")
    p.add_argument("-c", "--cancellable", action="store_true",
                   help="allow Ctrl+C (off by default, like sl)")
    p.add_argument("-s", "--speed", type=float, default=1.0,
                   help="speed multiplier (default 1)")
    p.add_argument("--density", type=float, default=0.7,
                   help="how much rain, 0.1-2 (default 0.7)")
    p.add_argument("-a", "--ascii", action="store_true",
                   help="ASCII only, no katakana")
    p.add_argument("-m", "--message", default="",
                   help="text typed out in the middle when the rain drains")
    p.add_argument("-V", "--version", action="version",
                   version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)
    if args.speed <= 0:
        p.error("--speed must be positive")
    args.density = min(2.0, max(0.1, args.density))
    return args


def _init_colors() -> dict[int, int]:
    """Curses attributes for each brightness level."""
    attrs = {HEAD: curses.A_BOLD, BRIGHT: curses.A_BOLD, NORMAL: 0, DIM: curses.A_DIM}
    if not curses.has_colors():
        return attrs
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    if curses.COLORS >= 256:
        palette = {HEAD: 231, BRIGHT: 46, NORMAL: 34, DIM: 22}
        for i, (level, fg) in enumerate(palette.items(), start=1):
            curses.init_pair(i, fg, bg)
            attrs[level] = curses.color_pair(i) | (curses.A_BOLD if level == HEAD else 0)
    else:
        curses.init_pair(1, curses.COLOR_WHITE, bg)
        curses.init_pair(2, curses.COLOR_GREEN, bg)
        attrs = {
            HEAD: curses.color_pair(1) | curses.A_BOLD,
            BRIGHT: curses.color_pair(2) | curses.A_BOLD,
            NORMAL: curses.color_pair(2),
            DIM: curses.color_pair(2) | curses.A_DIM,
        }
    return attrs


def _put(scr, y: int, x: int, text: str, attr: int) -> None:
    try:
        scr.addstr(y, x, text, attr)
    except curses.error:
        pass  # writing the bottom-right cell raises; harmless


def _type_message(scr, message: str, attr: int, delay: float) -> None:
    h, w = scr.getmaxyx()
    message = message[: max(0, w - 2)]
    y, x = h // 2, max(0, (w - len(message)) // 2)
    for i, ch in enumerate(message):
        _put(scr, y, x + i, ch, attr)
        _put(scr, y, x + i + 1, "█", attr)
        scr.refresh()
        time.sleep(delay)
    _put(scr, y, x + len(message), " ", attr)
    scr.refresh()
    time.sleep(1.2)


def run(scr, args: argparse.Namespace) -> None:
    curses.curs_set(0)
    scr.nodelay(True)
    attrs = _init_colors()
    h, w = scr.getmaxyx()
    rain = Rain(w, h, density=args.density, ascii_only=args.ascii)
    rain.seed_screen()

    frame = 1.0 / (FPS * args.speed)
    end = None if args.forever else time.monotonic() + args.duration
    while not rain.finished:
        key = scr.getch()
        if key == curses.KEY_RESIZE:
            h, w = scr.getmaxyx()
            rain.resize(w, h)
        elif key in (ord("q"), 27) and (args.forever or args.cancellable):
            rain.stop()
            rain.drops.clear()
        if end is not None and time.monotonic() >= end:
            rain.stop()

        rain.step()
        scr.erase()
        for (y, x), (ch, level) in rain.cells().items():
            _put(scr, y, x, ch, attrs[level])
        scr.refresh()
        time.sleep(frame)

    if args.message:
        _type_message(scr, args.message, attrs[BRIGHT], 0.08 / args.speed)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.cancellable and not args.forever:
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # the sl tradition
    locale.setlocale(locale.LC_ALL, "")
    if "UTF" not in (locale.getpreferredencoding(False) or "").upper():
        args.ascii = True
    try:
        curses.wrapper(run, args)
    except KeyboardInterrupt:
        pass
    return 0
