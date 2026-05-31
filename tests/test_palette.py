from pathlib import Path

import numpy as np
from PIL import Image

from chroma_cli import extract_palette


def _make_image(tmp_path: Path, blocks: list[tuple[int, int, int]]) -> Path:
    arr = np.zeros((100, 100 * len(blocks), 3), dtype=np.uint8)
    for i, color in enumerate(blocks):
        arr[:, i * 100 : (i + 1) * 100] = color
    img = Image.fromarray(arr, mode="RGB")
    path = tmp_path / "test.png"
    img.save(path)
    return path


def _close(a: tuple[int, int, int], b: tuple[int, int, int], tol: int = 3) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_extracts_n_colors(tmp_path: Path) -> None:
    img = _make_image(tmp_path, [(255, 0, 0), (0, 255, 0), (0, 0, 255)])
    palette = extract_palette(img, n_colors=3)
    assert len(palette) == 3
    rgbs = [c.rgb for c in palette]
    # Should recover the three primaries (within encoding tolerance)
    assert any(_close(rgb, (255, 0, 0)) for rgb in rgbs)
    assert any(_close(rgb, (0, 255, 0)) for rgb in rgbs)
    assert any(_close(rgb, (0, 0, 255)) for rgb in rgbs)


def test_shares_sum_to_one(tmp_path: Path) -> None:
    img = _make_image(tmp_path, [(255, 0, 0), (0, 255, 0)])
    palette = extract_palette(img, n_colors=2)
    total = sum(c.share for c in palette)
    assert abs(total - 1.0) < 1e-6


def test_sorted_by_share(tmp_path: Path) -> None:
    # 70% red, 30% blue
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :70] = (255, 0, 0)
    arr[:, 70:] = (0, 0, 255)
    img_path = tmp_path / "skewed.png"
    Image.fromarray(arr, mode="RGB").save(img_path)
    palette = extract_palette(img_path, n_colors=2)
    assert palette[0].share > palette[1].share


def test_css_output(tmp_path: Path) -> None:
    img = _make_image(tmp_path, [(255, 0, 0), (0, 255, 0)])
    palette = extract_palette(img, n_colors=2)
    css = palette.to_css()
    assert ":root {" in css
    assert "--color-1:" in css
    assert "--color-2:" in css


def test_missing_file_raises() -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        extract_palette("/nonexistent/path/to/image.png")
