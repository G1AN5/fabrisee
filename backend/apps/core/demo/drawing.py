"""Flat illustrations for the demo data, drawn with Pillow.

Simple drawings of counters, booths, signs, and display stands stand in for design renders
and reference photos. Every image carries a "DEMO" corner label. No real brand names,
logos, or photos are used.
"""

import io
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1600, 1000
SUPERSAMPLE = 2  # draw at twice the size, then scale down for smooth edges
HORIZON = 640
BAND_TOP = 904

INK = "#1F2937"
MUTED = "#64748B"
DIMENSION = "#1E40AF"
WALL = "#EEF1F5"
FLOOR = "#D9DFE7"
PAPER = "#FBF8F1"
PEN = "#1E3A8A"


@lru_cache(maxsize=32)
def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


class Scene:
    """A 1600 × 1000 drawing surface with a wall, a floor, and a title band.

    In `sketch` mode every shape is drawn as a pen outline on paper, which makes the same
    drawing look like a client's reference sketch instead of a render.
    """

    def __init__(self, *, sketch: bool = False, wall: str = WALL, floor: str = FLOOR):
        self.sketch = sketch
        background = PAPER if sketch else wall
        self.image = Image.new("RGB", (WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE), background)
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        if sketch:
            self.line([(60, HORIZON), (WIDTH - 60, HORIZON)], fill="#B9C2D0", width=2)
        else:
            self.draw.rectangle(self._box(0, HORIZON, WIDTH, BAND_TOP - HORIZON), fill=floor)
            self.line([(0, HORIZON), (WIDTH, HORIZON)], fill="#C5CCD6", width=2)

    # --- helpers -----------------------------------------------------------------

    @staticmethod
    def _px(value: float) -> int:
        return round(value * SUPERSAMPLE)

    def _box(self, x: float, y: float, w: float, h: float) -> list[int]:
        return [self._px(x), self._px(y), self._px(x + w), self._px(y + h)]

    def _style(self, fill, outline, width):
        """Fill, outline and outline width, adjusted for sketch mode."""
        if self.sketch:
            return "#FFFFFF" if fill else None, PEN, self._px(max(width, 3))
        return fill, outline, self._px(width) if outline else 0

    # --- shapes ------------------------------------------------------------------

    def rect(self, x, y, w, h, fill=None, outline=None, width=2, radius=0):
        fill, outline, width = self._style(fill, outline, width)
        box = self._box(x, y, w, h)
        if radius:
            self.draw.rounded_rectangle(
                box, radius=self._px(radius), fill=fill, outline=outline, width=width
            )
        else:
            self.draw.rectangle(box, fill=fill, outline=outline, width=width)

    def poly(self, points, fill=None, outline=None, width=2):
        fill, outline, width = self._style(fill, outline, width)
        scaled = [(self._px(x), self._px(y)) for x, y in points]
        self.draw.polygon(scaled, fill=fill, outline=outline, width=width)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=2):
        fill, outline, width = self._style(fill, outline, width)
        self.draw.ellipse(
            self._box(cx - rx, cy - ry, 2 * rx, 2 * ry), fill=fill, outline=outline, width=width
        )

    def arc(self, cx, cy, rx, ry, start, end, fill, width=4):
        self.draw.arc(
            self._box(cx - rx, cy - ry, 2 * rx, 2 * ry),
            start,
            end,
            fill=PEN if self.sketch else fill,
            width=self._px(width),
        )

    def line(self, points, fill=INK, width=2):
        scaled = [(self._px(x), self._px(y)) for x, y in points]
        self.draw.line(scaled, fill=PEN if self.sketch else fill, width=self._px(width))

    def text(self, x, y, text, size=24, fill=INK, anchor="la"):
        color = PEN if self.sketch else fill
        self.draw.text(
            (self._px(x), self._px(y)), text, font=_font(self._px(size)), fill=color, anchor=anchor
        )

    def shadow(self, cx, cy, rx, ry=20):
        if not self.sketch:
            self.draw.ellipse(self._box(cx - rx, cy - ry, 2 * rx, 2 * ry), fill=(15, 23, 42, 34))

    def glow(self, x, y, w, h, color, spread=18):
        """A soft light around a panel (backlighting)."""
        if self.sketch:
            return
        red, green, blue = ImageColorCache.rgb(color)
        for step in range(3):
            grow = spread * (3 - step) / 3
            self.draw.rounded_rectangle(
                self._box(x - grow, y - grow, w + 2 * grow, h + 2 * grow),
                radius=self._px(grow + 6),
                fill=(red, green, blue, 60 + step * 45),
            )

    # --- dimension lines (the "blueprint" touch) ----------------------------------

    def dim_h(self, x1, x2, y, label):
        self.line([(x1, y), (x2, y)], fill=DIMENSION, width=2)
        for x in (x1, x2):
            self.line([(x, y - 9), (x, y + 9)], fill=DIMENSION, width=2)
        self.text((x1 + x2) / 2, y - 8, label, size=22, fill=DIMENSION, anchor="md")

    def dim_v(self, x, y1, y2, label):
        self.line([(x, y1), (x, y2)], fill=DIMENSION, width=2)
        for y in (y1, y2):
            self.line([(x - 9, y), (x + 9, y)], fill=DIMENSION, width=2)
        self.text(x + 14, (y1 + y2) / 2, label, size=22, fill=DIMENSION, anchor="lm")

    # --- finishing ---------------------------------------------------------------

    def finish(self, *, title: str, subtitle: str, label: str, kind: str) -> bytes:
        """Add the title band and the DEMO corner label, and return PNG bytes."""
        band = self._box(0, BAND_TOP, WIDTH, HEIGHT - BAND_TOP)
        self.draw.rectangle(band, fill="#FFFFFF")
        self.draw.line(
            [(0, self._px(BAND_TOP)), (self._px(WIDTH), self._px(BAND_TOP))],
            fill="#CBD5E1",
            width=self._px(2),
        )
        font_small, font_title = _font(self._px(18)), _font(self._px(30))
        self.draw.text(
            (self._px(48), self._px(BAND_TOP + 18)), kind.upper(), font=font_small, fill=MUTED
        )
        self.draw.text((self._px(48), self._px(BAND_TOP + 44)), title, font=font_title, fill=INK)
        self.draw.text(
            (self._px(WIDTH - 48), self._px(BAND_TOP + 18)),
            subtitle,
            font=font_small,
            fill=MUTED,
            anchor="ra",
        )
        self.draw.text(
            (self._px(WIDTH - 48), self._px(BAND_TOP + 44)),
            label,
            font=font_title,
            fill=DIMENSION,
            anchor="ra",
        )
        # DEMO corner label
        self.draw.rounded_rectangle(
            self._box(WIDTH - 172, 28, 144, 48), radius=self._px(8), fill="#C2410C"
        )
        self.draw.text(
            (self._px(WIDTH - 100), self._px(52)),
            "DEMO",
            font=_font(self._px(26)),
            fill="#FFFFFF",
            anchor="mm",
        )
        final = self.image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        final.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()


class ImageColorCache:
    @staticmethod
    @lru_cache(maxsize=64)
    def rgb(color: str) -> tuple[int, int, int]:
        color = color.lstrip("#")
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


# --- Scenes ---------------------------------------------------------------------------
# Each function draws one kind of project. `variant` changes visible details so that
# revisions R1, R2, R3 of the same project differ the way the client asked.


def experience_counter(scene: Scene, variant: int = 1) -> None:
    """A backlit brand wall with a listening counter (Aurelia Audio Labs)."""
    teal, wood, top = "#0F766E", "#B08968", "#E7D8C9"
    light = "#BAE6FD" if variant == 1 else "#FDE68A"  # cool white, then warm white
    stations = 2 if variant == 1 else 4

    scene.glow(250, 150, 1100, 490, light)
    scene.rect(250, 150, 1100, 490, fill=teal, outline="#0B5E58", width=3, radius=6)
    for index in range(3):
        scene.arc(520, 300, 46 + index * 30, 46 + index * 30, 300, 60, "#99F6E4", width=7)
    scene.text(860, 280, "AURELIA", size=92, fill="#FFFFFF", anchor="mm")
    scene.text(860, 352, "AUDIO  LABS", size=30, fill="#CCFBF1", anchor="mm")

    scene.shadow(800, 768, 440)
    scene.rect(420, 578, 760, 184, fill=wood, outline="#8C6B4F", width=3)
    scene.rect(402, 556, 796, 24, fill=top, outline="#C9B8A6", width=2, radius=4)
    scene.rect(420, 742, 760, 20, fill="#6B4F3A")
    for index in range(stations):
        cx = 420 + 760 * (index + 0.5) / stations
        scene.line([(cx, 556), (cx, 508)], fill="#334155", width=5)
        scene.arc(cx, 492, 30, 30, 180, 360, "#334155", width=6)
        scene.rect(cx - 38, 486, 16, 30, fill="#1F2937", radius=5)
        scene.rect(cx + 22, 486, 16, 30, fill="#1F2937", radius=5)

    scene.dim_h(250, 1350, 116, "4.8 m")
    scene.dim_v(1392, 150, 640, "2.7 m")
    scene.dim_h(420, 1180, 836, "3.0 m")


def window_display(scene: Scene, variant: int = 1) -> None:
    """A storefront window with a platform, pedestals, and a backlit panel."""
    teal = "#0F766E"
    scene.rect(200, 120, 1200, 660, fill="#F6F9FC", outline="#334155", width=10)
    if variant > 0:
        scene.glow(520, 200, 560, 300, "#FDE68A", spread=14)
        scene.rect(520, 200, 560, 300, fill=teal, outline="#0B5E58", width=3, radius=6)
        scene.text(800, 320, "AURELIA", size=74, fill="#FFFFFF", anchor="mm")
        scene.text(800, 384, "HOLIDAY  SOUND", size=26, fill="#CCFBF1", anchor="mm")
    scene.rect(222, 700, 1156, 62, fill="#B08968", outline="#8C6B4F", width=3)
    pedestals = [(330, 190), (730, 120), (1110, 230)] if variant > 0 else [(360, 120), (980, 160)]
    for x, height in pedestals:
        scene.rect(x, 700 - height, 170, height, fill="#FFFFFF", outline="#CBD5E1", width=3)
        scene.rect(x + 40, 700 - height - 96, 90, 96, fill="#1F2937", radius=10)
        scene.ellipse(x + 85, 700 - height - 60, 24, 24, fill="#475569", outline="#94A3B8")
        scene.ellipse(x + 85, 700 - height - 22, 10, 10, fill="#475569")
    scene.dim_h(200, 1400, 86, "3.2 m")
    scene.dim_v(1438, 120, 780, "2.6 m")


def cafe_counter(scene: Scene, variant: int = 1) -> None:
    """A café service counter with a menu board (Kapetirya Coffee House).

    R1: tall counter, menu board on the side. R2: lower counter, menu board on the back
    wall. R3: light oak, closed storage under the counter, pastry display case.
    """
    dark_wood, light_oak = "#5B3A29", "#D8B892"
    wood = light_oak if variant >= 3 else dark_wood
    edge = "#B89468" if variant >= 3 else "#3F281C"
    counter_top = 500 if variant == 1 else 545

    board = (130, 230, 300, 200) if variant == 1 else (500, 170, 600, 220)
    bx, by, bw, bh = board
    scene.rect(bx, by, bw, bh, fill="#1F2937", outline="#0F172A", width=4, radius=6)
    scene.text(bx + bw / 2, by + 34, "MENU", size=30, fill="#F5E6D3", anchor="mm")
    columns = 2 if variant == 1 else 3
    for column in range(columns):
        left = bx + 24 + column * (bw - 48) / columns
        for row in range(5):
            y = by + 70 + row * 24
            scene.line([(left, y), (left + (bw - 48) / columns - 60, y)], fill="#94A3B8", width=4)
            scene.line(
                [(left + (bw - 48) / columns - 44, y), (left + (bw - 48) / columns - 20, y)],
                fill="#F5E6D3",
                width=4,
            )

    for x in (560, 800, 1040):
        scene.line([(x, 0), (x, 110)], fill="#475569", width=3)
        scene.poly([(x - 34, 150), (x + 34, 150), (x + 16, 110), (x - 16, 110)], fill="#F59E0B")

    scene.shadow(800, 776, 470)
    scene.rect(380, counter_top + 22, 840, 770 - counter_top - 22, fill=wood, outline=edge, width=3)
    scene.rect(362, counter_top, 876, 24, fill="#F3EDE4", outline="#D6CCBE", width=2, radius=4)
    scene.rect(380, 750, 840, 20, fill="#2B1B12" if variant < 3 else "#8C6B4F")
    if variant >= 3:
        for x in range(410, 1190, 195):
            scene.rect(x, counter_top + 92, 175, 104, outline="#B89468", width=3, radius=4)
            scene.ellipse(x + 150, counter_top + 144, 6, 6, fill="#8C6B4F")
        scene.rect(968, counter_top - 86, 220, 86, fill="#E0F2FE", outline="#7DD3FC", width=3)
        for x in (1000, 1060, 1120):
            scene.ellipse(x, counter_top - 22, 20, 14, fill="#D97706")
    scene.text(
        650 if variant >= 3 else 800,
        counter_top + 54,
        "KAPETIRYA",
        size=40,
        fill="#5B3A29" if variant >= 3 else "#F5E6D3",
        anchor="mm",
    )

    scene.dim_h(380, 1220, 836, "3.6 m")
    scene.dim_v(1262, counter_top, 770, "1.20 m" if variant == 1 else "1.05 m")


def fair_booth(scene: Scene, variant: int = 1) -> None:
    """A 3 m × 6 m trade fair booth (Lunaria Skin Studio).

    R1: small brand panel, counter at the side. R2: larger brand panel, product shelves
    on the left wall, counter facing the aisle.
    """
    plum, rose, cream = "#7A3E65", "#F3C6CE", "#FFF8F0"
    scene.poly([(300, 640), (1300, 640), (1430, 786), (170, 786)], fill="#EBD5DA")
    scene.rect(170, 786, 1260, 18, fill="#C9A9B1")
    scene.poly([(300, 170), (180, 214), (180, 776), (300, 640)], fill="#E6E9EE", outline="#C5CCD6")
    scene.rect(300, 170, 1000, 470, fill="#FFFFFF", outline="#C5CCD6", width=3)
    for x in (633, 966):
        scene.line([(x, 170), (x, 640)], fill="#E2E8F0", width=2)
    scene.rect(280, 108, 1040, 64, fill=plum, radius=4)
    scene.text(800, 140, "LUNARIA  SKIN  STUDIO", size=34, fill=cream, anchor="mm")

    panel = (690, 230, 300, 170) if variant == 1 else (590, 200, 500, 250)
    px, py, pw, ph = panel
    scene.glow(px, py, pw, ph, "#FBCFE8", spread=12)
    scene.rect(px, py, pw, ph, fill=rose, outline="#E3A5B1", width=3, radius=8)
    scene.ellipse(px + pw / 2, py + ph / 2 - 12, 44, 44, fill=cream)
    scene.ellipse(px + pw / 2 + 18, py + ph / 2 - 22, 38, 38, fill=rose)
    scene.text(px + pw / 2, py + ph - 30, "LUNARIA", size=30, fill=plum, anchor="mm")

    if variant >= 2:
        for index, y in enumerate((270, 370, 470)):
            scene.rect(330, y, 210, 10, fill="#D6CCBE")
            for bottle in range(4):
                scene.rect(
                    346 + bottle * 48 + index * 4,
                    y - 46,
                    22,
                    46,
                    fill=plum if (bottle + index) % 2 else rose,
                    radius=5,
                )
        scene.shadow(1010, 742, 210, 16)
        scene.rect(830, 580, 360, 156, fill=plum, outline="#5C2D4C", width=3, radius=4)
        scene.rect(816, 560, 388, 22, fill=cream, outline="#E7D8C9", width=2, radius=4)
        scene.text(1010, 660, "CONSULTATION", size=26, fill=cream, anchor="mm")
    else:
        scene.shadow(450, 742, 110, 14)
        scene.rect(370, 580, 160, 156, fill=plum, outline="#5C2D4C", width=3, radius=4)
        scene.rect(358, 560, 184, 22, fill=cream, outline="#E7D8C9", width=2, radius=4)

    scene.dim_h(300, 1300, 76, "6.0 m")
    scene.dim_v(1344, 170, 640, "2.4 m")
    scene.text(1392, 720, "3.0 m deep", size=22, fill=DIMENSION, anchor="lm")


def popup_booth(scene: Scene, variant: int = 1) -> None:
    """A pop-up coffee booth with a canopy (Kapetirya Coffee House)."""
    brown, cream, green = "#7C4A2D", "#F5E6D3", "#4D7C5B"
    stripes = 8
    for index in range(stripes):
        x0 = 420 + index * 760 / stripes
        x1 = 420 + (index + 1) * 760 / stripes
        bottom0 = 340 + index * 920 / stripes
        bottom1 = 340 + (index + 1) * 920 / stripes
        scene.poly(
            [(x0, 190), (x1, 190), (bottom1, 300), (bottom0, 300)],
            fill=green if index % 2 == 0 else cream,
            outline="#3F6349",
            width=1,
        )
    for x in (372, 1228):
        scene.line([(x, 300), (x, 770)], fill="#475569", width=8)
    scene.rect(520, 324, 560, 76, fill=brown, radius=6)
    scene.text(800, 362, "KAPETIRYA  COFFEE", size=34, fill=cream, anchor="mm")

    scene.rect(440, 470, 720, 10, fill="#B08968")
    for x in range(480, 1120, 70):
        scene.rect(x, 436, 30, 34, fill="#FFFFFF", outline="#CBD5E1", width=2, radius=4)

    scene.shadow(800, 776, 410)
    scene.rect(440, 582, 720, 188, fill="#B08968", outline="#8C6B4F", width=3)
    for x in range(480, 1160, 40):
        scene.line([(x, 590), (x, 762)], fill="#9A7657", width=2)
    scene.rect(424, 560, 752, 24, fill=cream, outline="#D6CCBE", width=2, radius=4)
    if variant >= 2:
        scene.line([(800, 584), (800, 770)], fill="#5B3A29", width=5)  # folds in two parts
        scene.rect(1176, 380, 150, 54, fill=brown, radius=6)  # side sign
        scene.text(1251, 407, "COFFEE", size=22, fill=cream, anchor="mm")

    scene.dim_h(440, 1160, 836, "1.8 m")
    scene.dim_v(1290, 190, 770, "2.3 m")


def display_stands(scene: Scene) -> None:
    """Freestanding accessory stands with hooks, shelves, and a header sign."""
    violet, yellow = "#6D28D9", "#FACC15"
    for index, x in enumerate((300, 680, 1060)):
        scene.shadow(x + 120, 782, 140, 14)
        scene.rect(x, 190, 240, 74, fill=violet, radius=6)
        scene.text(x + 120, 227, "TINDAHAN TECH", size=22, fill="#FFFFFF", anchor="mm")
        scene.rect(x + 10, 264, 220, 500, fill="#FFFFFF", outline="#94A3B8", width=3)
        for row in range(3):
            for hook in range(4):
                hx, hy = x + 36 + hook * 52, 292 + row * 78
                scene.line([(hx, hy), (hx, hy + 16)], fill="#64748B", width=3)
                scene.rect(
                    hx - 14,
                    hy + 16,
                    28,
                    44,
                    fill=yellow if (hook + row + index) % 2 else violet,
                    radius=4,
                )
        for y in (600, 690):
            scene.rect(x + 10, y, 220, 10, fill="#CBD5E1")
            for item in range(3):
                scene.rect(
                    x + 34 + item * 64, y - 50, 44, 50, fill="#E2E8F0", outline="#94A3B8", radius=4
                )
        scene.rect(x - 6, 764, 252, 18, fill="#475569", radius=4)
    scene.dim_h(300, 540, 150, "0.6 m")
    scene.dim_v(1340, 190, 782, "1.7 m")


def storefront_sign(scene: Scene, lit: bool = False) -> None:
    """A storefront with the space for a brand sign above the entrance."""
    violet = "#6D28D9"
    scene.rect(220, 120, 1160, 660, fill="#F8FAFC", outline="#94A3B8", width=4)
    if lit:
        scene.glow(300, 170, 1000, 124, "#DDD6FE", spread=14)
        scene.rect(300, 170, 1000, 124, fill=violet, radius=8)
        scene.text(800, 232, "TINDAHAN TECH PH", size=76, fill="#FFFFFF", anchor="mm")
    else:
        scene.rect(300, 170, 1000, 124, fill="#E2E8F0", outline="#94A3B8", width=3)
        scene.text(800, 232, "old tarpaulin banner", size=36, fill=MUTED, anchor="mm")
    scene.rect(300, 340, 420, 420, fill="#E0F2FE", outline="#64748B", width=5)
    scene.line([(510, 340), (510, 760)], fill="#64748B", width=4)
    scene.rect(820, 340, 480, 300, fill="#E0F2FE", outline="#64748B", width=5)
    scene.rect(820, 660, 480, 100, fill="#CBD5E1", outline="#94A3B8", width=3)
    scene.dim_h(300, 1300, 86, "4.0 m")
    scene.dim_v(1420, 170, 294, "0.9 m")


def endcap_display(scene: Scene) -> None:
    """An end-cap display unit with a header and three shelves."""
    plum, rose = "#7A3E65", "#F3C6CE"
    scene.shadow(800, 782, 240, 16)
    scene.rect(560, 150, 480, 110, fill=plum, radius=8)
    scene.text(800, 205, "LUNARIA  SERUM", size=40, fill="#FFF8F0", anchor="mm")
    scene.rect(580, 260, 440, 500, fill="#FFFFFF", outline="#94A3B8", width=4)
    for row, y in enumerate((400, 540, 680)):
        scene.rect(580, y, 440, 12, fill="#CBD5E1")
        for bottle in range(6):
            scene.rect(
                606 + bottle * 68,
                y - 84,
                40,
                84,
                fill=plum if (bottle + row) % 2 else rose,
                radius=8,
            )
    scene.rect(566, 760, 468, 22, fill="#475569", radius=4)
    scene.dim_h(580, 1020, 116, "0.9 m")
    scene.dim_v(1078, 150, 782, "1.6 m")


SCENES = {
    "experience_counter": experience_counter,
    "window_display": window_display,
    "cafe_counter": cafe_counter,
    "fair_booth": fair_booth,
    "popup_booth": popup_booth,
    "display_stands": display_stands,
    "storefront_sign": storefront_sign,
    "endcap_display": endcap_display,
}


def render_image(
    scene_name: str,
    *,
    title: str,
    subtitle: str,
    label: str,
    kind: str = "FabriSee demo render",
    sketch: bool = False,
    **options,
) -> bytes:
    """Draw one of the scenes and return it as PNG bytes."""
    scene = Scene(sketch=sketch)
    SCENES[scene_name](scene, **options)
    return scene.finish(title=title, subtitle=subtitle, label=label, kind=kind)
