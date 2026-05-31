from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .palette import extract_palette, Palette


def _print_swatch(palette: Palette) -> None:
    # ANSI truecolor swatches
    for i, c in enumerate(palette, start=1):
        bg = f"\033[48;2;{c.r};{c.g};{c.b}m"
        fg = "\033[38;2;0;0;0m" if c.is_light else "\033[38;2;255;255;255m"
        reset = "\033[0m"
        swatch = f"{bg}{fg}  {c.hex}  {reset}"
        bar = "█" * max(1, int(round(c.share * 30)))
        print(f"  {i}. {swatch}  {bar}  {c.share * 100:5.1f}%")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="chroma",
        description="Extract a color palette from any image.",
    )
    parser.add_argument("image", help="Path to image file (PNG, JPG, WebP...)")
    parser.add_argument(
        "-n", "--n-colors", type=int, default=5, help="Number of colors (default: 5)"
    )
    parser.add_argument(
        "--format",
        choices=("swatch", "hex", "json", "css", "tailwind"),
        default="swatch",
        help="Output format (default: swatch)",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Variable prefix for css/tailwind formats",
    )
    parser.add_argument("--version", action="version", version=f"chroma {__version__}")

    args = parser.parse_args(argv)

    try:
        palette = extract_palette(args.image, n_colors=args.n_colors)
    except FileNotFoundError:
        print(f"chroma: image not found: {args.image}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"chroma: {e}", file=sys.stderr)
        return 1

    fmt = args.format
    if fmt == "swatch":
        _print_swatch(palette)
    elif fmt == "hex":
        for c in palette:
            print(c.hex)
    elif fmt == "json":
        print(json.dumps(palette.to_json(), indent=2))
    elif fmt == "css":
        print(palette.to_css(var_prefix=args.prefix or "color"))
    elif fmt == "tailwind":
        print(palette.to_tailwind(name_prefix=args.prefix or "brand"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
