# matrix-rain

Digital rain in your terminal, in the spirit of `sl`: type `matrix`, the screen
fills with falling green glyphs for a few seconds, then the rain drains away.
And just like `sl`, **Ctrl+C doesn't stop it**.

Pure Python standard library (`curses`), no dependencies.

## Install

```bash
pipx install git+https://github.com/mostodont01/matrix-rain
# or just run it from a clone
git clone https://github.com/mostodont01/matrix-rain && ./matrix-rain/matrix
```

## Usage

```
matrix                 # 6 s of rain, can't be interrupted
matrix -d 15           # 15 s
matrix -f              # rain forever, q / Esc / Ctrl+C to quit
matrix -c              # allow Ctrl+C
matrix -s 2            # twice as fast
matrix --density 1.5   # heavier rain (0.1-2)
matrix -a              # ASCII only (also automatic on non-UTF-8 terminals)
matrix -m "follow the white rabbit"   # typed out when the rain ends
```

Prank idea, the `sl` way: `alias mtrix=matrix`, or `alias cls=matrix`.

## Development

```bash
pip install -e . pytest
pytest
```

Tests cover the simulation and run the real program in a pseudo-terminal
(exits on its own, ignores Ctrl+C, `-c` makes it cancellable).

## License

MIT
