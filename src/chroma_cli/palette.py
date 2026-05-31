from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import warnings

from PIL import Image
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
import numpy as np


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int
    share: float  # 0..1, share of image pixels

    @property
    def hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self.r, self.g, self.b

    @property
    def luminance(self) -> float:
        # Relative luminance (WCAG)
        def chan(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

        return 0.2126 * chan(self.r) + 0.7152 * chan(self.g) + 0.0722 * chan(self.b)

    @property
    def is_light(self) -> bool:
        return self.luminance > 0.5


@dataclass(frozen=True)
class Palette:
    colors: tuple[Color, ...]

    def __iter__(self) -> Iterable[Color]:
        return iter(self.colors)

    def __len__(self) -> int:
        return len(self.colors)

    def __getitem__(self, i: int) -> Color:
        return self.colors[i]

    def to_css(self, var_prefix: str = "color") -> str:
        lines = [":root {"]
        for i, c in enumerate(self.colors, start=1):
            lines.append(f"  --{var_prefix}-{i}: {c.hex};")
        lines.append("}")
        return "\n".join(lines)

    def to_tailwind(self, name_prefix: str = "brand") -> str:
        # tailwind.config.js snippet
        entries = [
            f'        "{name_prefix}-{i}": "{c.hex}",'
            for i, c in enumerate(self.colors, start=1)
        ]
        return (
            "module.exports = {\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            + "\n".join(entries)
            + "\n      }\n"
            "    }\n"
            "  }\n"
            "}"
        )

    def to_json(self) -> list[dict]:
        return [
            {"hex": c.hex, "rgb": list(c.rgb), "share": round(c.share, 4)}
            for c in self.colors
        ]


def extract_palette(
    image_path: str | Path,
    n_colors: int = 5,
    *,
    resize_to: int = 200,
    random_state: int = 42,
) -> Palette:
    """Extract `n_colors` dominant colors from an image.

    The image is downsized for speed, converted to RGB, and clustered with
    KMeans. Returned colors are sorted by share (most prevalent first).
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(path)

    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((resize_to, resize_to))
        pixels = np.asarray(img).reshape(-1, 3)

    n_colors = max(1, min(n_colors, len(pixels)))

    km = KMeans(n_clusters=n_colors, n_init=4, random_state=random_state)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        labels = km.fit_predict(pixels)
    centers = km.cluster_centers_.round().astype(int)

    counts = np.bincount(labels, minlength=n_colors)
    shares = counts / counts.sum()

    items = sorted(
        zip(centers, shares),
        key=lambda x: x[1],
        reverse=True,
    )

    colors = tuple(
        Color(r=int(c[0]), g=int(c[1]), b=int(c[2]), share=float(s))
        for c, s in items
    )
    return Palette(colors=colors)
