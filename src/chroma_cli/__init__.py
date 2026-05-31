"""chroma-cli — extract a color palette from any image."""

__version__ = "0.1.0"

from .palette import extract_palette, Color, Palette

__all__ = ["extract_palette", "Color", "Palette"]
