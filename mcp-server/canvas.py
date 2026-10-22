from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from PIL import Image
from palettes import PALETTES, parse_color, nearest_palette_color


@dataclass
class CanvasState:
    id: str
    width: int
    height: int
    palette_name: Optional[str]
    pixels: list[list[tuple[int, int, int]]]        # [y][x] = (r, g, b)
    frames: list[list[list[tuple[int, int, int]]]]  # list of pixel grids

    @classmethod
    def create(
        cls,
        canvas_id: str,
        width: int,
        height: int,
        palette: Optional[str] = None,
        bg_color: str = "#000000",
    ) -> "CanvasState":
        bg = parse_color(bg_color, palette)
        pixels = [[bg for _ in range(width)] for _ in range(height)]
        return cls(
            id=canvas_id,
            width=width,
            height=height,
            palette_name=palette,
            pixels=pixels,
            frames=[],
        )

    def _snap(self, color: tuple[int, int, int]) -> tuple[int, int, int]:
        if self.palette_name and self.palette_name in PALETTES:
            return nearest_palette_color(color, PALETTES[self.palette_name])
        return color

    def set_pixel(self, x: int, y: int, color: str) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        rgb = self._snap(parse_color(color, self.palette_name))
        self.pixels[y][x] = rgb

    def set_pixels(self, pixels: list[dict]) -> None:
        for p in pixels:
            self.set_pixel(p["x"], p["y"], p["color"])

    def fill_rect(self, x: int, y: int, w: int, h: int, color: str) -> None:
        rgb = self._snap(parse_color(color, self.palette_name))
        for py in range(max(0, y), min(self.height, y + h)):
            for px in range(max(0, x), min(self.width, x + w)):
                self.pixels[py][px] = rgb

    def flood_fill(self, x: int, y: int, color: str) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        rgb = self._snap(parse_color(color, self.palette_name))
        target = self.pixels[y][x]
        if target == rgb:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                continue
            if self.pixels[cy][cx] != target:
                continue
            self.pixels[cy][cx] = rgb
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

    def render_from_grid(self, grid: list[list[str]]) -> None:
        for y, row in enumerate(grid):
            if y >= self.height:
                break
            for x, color in enumerate(row):
                if x >= self.width:
                    break
                self.set_pixel(x, y, color)

    def add_frame(self) -> None:
        self.frames.append([row[:] for row in self.pixels])

    def to_image(self, scale: int = 8) -> Image.Image:
        img = Image.new("RGB", (self.width * scale, self.height * scale))
        for y in range(self.height):
            for x in range(self.width):
                color = self.pixels[y][x]
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((x * scale + dx, y * scale + dy), color)
        return img

    def frames_to_images(self, scale: int = 8) -> list[Image.Image]:
        imgs = []
        for frame in self.frames:
            img = Image.new("RGB", (self.width * scale, self.height * scale))
            for y in range(self.height):
                for x in range(self.width):
                    color = frame[y][x]
                    for dy in range(scale):
                        for dx in range(scale):
                            img.putpixel((x * scale + dx, y * scale + dy), color)
            imgs.append(img)
        return imgs

    def text_preview(self) -> str:
        """Unicode block preview for agent 'vision'."""
        lines = []
        for y in range(0, self.height, 2):
            row = ""
            for x in range(self.width):
                top = self.pixels[y][x]
                bot = self.pixels[y + 1][x] if y + 1 < self.height else (0, 0, 0)
                row += _block_char(top, bot)
            lines.append(row)
        return "\n".join(lines)


def _block_char(top: tuple, bot: tuple) -> str:
    t = (top[0] + top[1] + top[2]) // 3
    b = (bot[0] + bot[1] + bot[2]) // 3
    if t > 128 and b > 128:
        return "█"
    if t > 128:
        return "▀"
    if b > 128:
        return "▄"
    return " "
