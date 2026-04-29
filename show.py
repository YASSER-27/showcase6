#!/usr/bin/env python3
"""
Showcase Builder  ·  Professional 3D/2D Image Compositor
50 curated layouts · 17 backgrounds · Smart aspect-ratio engine
"""
import os, sys, math, random, time, subprocess

try:
    from PySide6.QtGui import (
        QGuiApplication, QImage, QPainter, QColor,
        QTransform, QPainterPath, QLinearGradient,
    )
    from PySide6.QtCore import Qt, QRectF
except ImportError:
    sys.exit("PySide6 required — install with:  pip install PySide6")

try:
    import imageio.v3 as iio
    import numpy as np
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False


# ════════════════════════════════════════════════════════════════ RenderItem ══

class RenderItem:
    """Holds image data + layout parameters for one image slot."""

    def __init__(self, path: str):
        self.path = path
        self.is_video = path.lower().endswith(".gif")
        self.frames: list[QImage] = []

        if self.is_video and HAS_VIDEO:
            try:
                for frame in iio.imread(path):
                    if len(frame.shape) == 3:
                        h, w, c = frame.shape
                        fmt = QImage.Format_RGB888 if c == 3 else QImage.Format_RGBA8888
                        self.frames.append(
                            QImage(frame.data, w, h, w * c, fmt).copy()
                        )
                    else:
                        self.frames.append(QImage(path))
            except Exception:
                self.frames = [QImage(path)]
        else:
            self.frames = [QImage(path)]

        if not self.frames or self.frames[0].isNull():
            fb = QImage(120, 120, QImage.Format_RGB32)
            fb.fill(Qt.gray)
            self.frames = [fb]

        self.img = self.frames[0]
        self.w   = self.img.width()
        self.h   = self.img.height()
        self._reset()

    def _reset(self):
        self.x  = self.y  = 0.0
        self.tw = self.th = 0.0
        self.rx = self.ry = self.rz = 0.0
        self.z             = 0
        self.shadow        = True
        self.opacity       = 1.0
        self.corner_radius = 14.0

    def set_frame(self, idx: int):
        self.img = self.frames[idx % len(self.frames)]


# ═══════════════════════════════════════════════════════════ Size helpers ══

# Width fractions indexed by (n-1), capped at index 6
_FRACS = [0.68, 0.46, 0.40, 0.34, 0.28, 0.24, 0.20]


def _sz(item: RenderItem, cw: float, ch: float, n: int,
        frac: float | None = None, max_h: float = 0.82) -> tuple[float, float]:
    """
    Compute (tw, th) that:
      • respects the image's original aspect ratio
      • fits within max_h * ch canvas height
      • scales based on item count when frac is None
    """
    if frac is None:
        frac = _FRACS[min(n - 1, len(_FRACS) - 1)]
    tw = cw * frac
    th = item.h * tw / item.w if item.w else tw
    if th > ch * max_h:
        th = ch * max_h
        tw = item.w * th / item.h if item.h else th
    return tw, th


def _fit_cell(item: RenderItem, cell_w: float, cell_h: float,
              pad: float = 0.92) -> tuple[float, float]:
    """Fit item into a cell while preserving aspect ratio."""
    tw = cell_w * pad
    th = item.h * tw / item.w if item.w else tw
    if th > cell_h * pad:
        th = cell_h * pad
        tw = item.w * th / item.h if item.h else th
    return tw, th


# ═══════════════════════════════════════════════════════════ Backgrounds ══

def draw_background(painter: QPainter, cw: int, ch: int, bg_sel: int):
    def grad_v(stops):
        g = QLinearGradient(0, 0, 0, ch)
        for p, c in stops: g.setColorAt(p, QColor(*c))
        painter.fillRect(0, 0, cw, ch, g)

    def grad_d(stops):
        g = QLinearGradient(0, 0, cw, ch)
        for p, c in stops: g.setColorAt(p, QColor(*c))
        painter.fillRect(0, 0, cw, ch, g)

    if   bg_sel == 0:  painter.fillRect(0, 0, cw, ch, QColor(0, 0, 0, 0))
    elif bg_sel == 1:  painter.fillRect(0, 0, cw, ch, QColor(250, 250, 250))
    elif bg_sel == 2:  painter.fillRect(0, 0, cw, ch, QColor(21, 21, 21))
    elif bg_sel == 3:  grad_v([(0,(5,5,30)),(1,(20,0,60))])
    elif bg_sel == 4:  grad_d([(0,(255,94,77)),(0.5,(255,154,0)),(1,(255,206,84))])
    elif bg_sel == 5:  grad_v([(0,(0,60,120)),(1,(0,180,200))])
    elif bg_sel == 6:  grad_d([(0,(60,0,100)),(1,(180,0,180))])
    elif bg_sel == 7:  grad_v([(0,(5,30,10)),(1,(20,80,30))])
    elif bg_sel == 8:  grad_d([(0,(220,140,120)),(1,(255,200,180))])
    elif bg_sel == 9:
        grad_d([(0,(10,0,30)),(0.5,(0,20,60)),(1,(20,0,50))])
        for x in range(0, cw, max(1, cw // 10)):
            painter.fillRect(x, 0, 1, ch, QColor(0, 200, 255, 22))
    elif bg_sel == 10: grad_d([(0,(40,40,45)),(1,(60,60,70))])
    elif bg_sel == 11:
        painter.fillRect(0, 0, cw, ch, QColor(220, 230, 255, 200))
        g = QLinearGradient(0, 0, cw, ch)
        g.setColorAt(0, QColor(255,255,255,80)); g.setColorAt(1, QColor(200,220,255,60))
        painter.fillRect(0, 0, cw, ch, g)
    elif bg_sel == 12: grad_d([(0,(0,30,60)),(0.4,(0,100,80)),(0.7,(100,0,120)),(1,(0,20,50))])
    elif bg_sel == 13: grad_v([(0,(255,248,235)),(1,(240,220,190))])
    elif bg_sel == 14: grad_v([(0,(15,20,60)),(1,(25,35,100))])
    elif bg_sel == 15: grad_v([(0,(255,200,50)),(0.5,(220,120,30)),(1,(180,60,20))])
    elif bg_sel == 16:
        hue = random.randint(0, 359)
        g = QLinearGradient(0, 0, cw, ch)
        g.setColorAt(0,   QColor.fromHsv(hue,         180, 200))
        g.setColorAt(0.5, QColor.fromHsv((hue+60)%360, 220, 150))
        g.setColorAt(1,   QColor.fromHsv((hue+120)%360,180, 220))
        painter.fillRect(0, 0, cw, ch, g)


# ════════════════════════════════════════════════════════════ Layout engine ══

def apply_layout(items: list[RenderItem], layout_idx: int, cw: float, ch: float):
    n = len(items)
    if n == 0:
        return

    for i, item in enumerate(items):
        item._reset()
        item.z = i

    cx0  = cw / 2.0          # canvas centre x
    cy0  = ch / 2.0          # canvas centre y
    mid  = (n - 1) / 2.0     # symmetric float centre index

    # ── helpers used inside layouts ──────────────────────────────────────────
    def place(item, tx, ty):
        item.x = tx - item.tw / 2
        item.y = ty - item.th / 2

    def place_tl(item, tx, ty):
        """Place top-left corner at (tx, ty)."""
        item.x = tx
        item.y = ty

    # ╔══════════════════════════════════════════════════════════════════════╗
    # ║  SECTION A — 3D Perspective Layouts  (1 – 30)                       ║
    # ╚══════════════════════════════════════════════════════════════════════╝

    # ── 1 · Isometric Stack ──────────────────────────────────────────────────
    if layout_idx == 1:
        frac = max(0.26, 0.46 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 50;  item.rz = 45
            off = i - mid
            place(item, cx0 + off * cw * 0.065, cy0 - off * ch * 0.072)
            item.z = n - i

    # ── 2 · Perspective Right ────────────────────────────────────────────────
    elif layout_idx == 2:
        frac = max(0.26, 0.44 - n * 0.018)
        step = cw * max(0.11, 0.22 - n * 0.012)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.ry = 28
            off = i - mid
            place(item, cx0 + off * step, cy0)
            item.z = i

    # ── 3 · Perspective Left ─────────────────────────────────────────────────
    elif layout_idx == 3:
        frac = max(0.26, 0.44 - n * 0.018)
        step = cw * max(0.11, 0.22 - n * 0.012)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.ry = -28
            off = i - mid
            place(item, cx0 - off * step, cy0)
            item.z = n - i

    # ── 4 · Coverflow ────────────────────────────────────────────────────────
    elif layout_idx == 4:
        centre_i = n // 2
        for i, item in enumerate(items):
            dist = i - centre_i
            if dist == 0:
                item.tw, item.th = _sz(item, cw, ch, 1, frac=min(0.58, 0.80))
                item.ry = 0
                place(item, cx0, cy0)
                item.z = 100
            else:
                item.tw, item.th = _sz(item, cw, ch, n, frac=max(0.22, 0.35 - n * 0.015))
                sign = 1 if dist > 0 else -1
                item.ry = sign * 42
                gap = cw * 0.20
                tx = cx0 + sign * (cw * 0.18 + abs(dist) * gap)
                place(item, tx, cy0 + abs(dist) * ch * 0.03)
                item.z = 50 - abs(dist)

    # ── 5 · V-Formation ──────────────────────────────────────────────────────
    elif layout_idx == 5:
        frac = max(0.26, 0.42 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            off = abs(i - mid)
            sign = 1 if i > mid else (-1 if i < mid else 0)
            item.ry = sign * min(35, off * 18)
            tx = cx0 + sign * off * cw * 0.16
            place(item, tx, cy0 - off * ch * 0.05)
            item.z = n - int(off)

    # ── 6 · Diagonal Cascade ─────────────────────────────────────────────────
    elif layout_idx == 6:
        frac = max(0.28, 0.44 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 14;  item.ry = 12
            off = i - mid
            place(item, cx0 + off * cw * 0.12, cy0 + off * ch * 0.10)
            item.z = n - i

    # ── 7 · Tilted Floor ─────────────────────────────────────────────────────
    elif layout_idx == 7:
        frac = max(0.24, 0.40 - n * 0.018)
        step = cw * max(0.14, 0.26 - n * 0.014)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 55
            off = i - mid
            place(item, cx0 + off * step, cy0 + ch * 0.10)
            item.z = i

    # ── 8 · Cylinder Inward ──────────────────────────────────────────────────
    elif layout_idx == 8:
        frac  = max(0.24, 0.38 - n * 0.015)
        r_cyl = cw * 0.26
        span  = math.pi * 0.55
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            a = (i - mid) * (span / max(1, n - 1)) if n > 1 else 0
            place(item, cx0 + r_cyl * math.sin(a), cy0)
            item.ry = math.degrees(a)
            item.z  = int(r_cyl * math.cos(a))

    # ── 9 · Step Stairs ──────────────────────────────────────────────────────
    elif layout_idx == 9:
        frac = max(0.26, 0.42 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 8;  item.ry = 12
            off = i - mid
            place(item, cx0 + off * cw * 0.13, cy0 - off * ch * 0.09)
            item.z = n - i

    # ── 10 · Focus Center ────────────────────────────────────────────────────
    elif layout_idx == 10:
        for i, item in enumerate(items):
            if i == 0:
                item.tw, item.th = _sz(item, cw, ch, 1, frac=0.58)
                place(item, cx0, cy0)
                item.z = 100
            else:
                item.tw, item.th = _sz(item, cw, ch, n, frac=max(0.18, 0.28 - n * 0.01))
                j  = i - 1
                ar = j * (2 * math.pi / max(1, n - 1))
                r  = min(cw, ch) * 0.30
                place(item, cx0 + r * math.cos(ar), cy0 + r * math.sin(ar) * 0.60)
                item.ry = -math.degrees(ar) * 0.30
                item.z  = 0

    # ── 11 · Deck of Cards ───────────────────────────────────────────────────
    elif layout_idx == 11:
        item0 = items[0]
        item0.tw, item0.th = _sz(item0, cw, ch, 1, frac=0.52)
        for i, item in enumerate(items):
            item.tw, item.th = items[0].tw, items[0].th
            off = i - mid
            item.rz = off * 7.0
            place(item, cx0 + off * cw * 0.006, cy0 + off * ch * 0.004)
            item.z = i

    # ── 12 · Panorama Sweep ──────────────────────────────────────────────────
    elif layout_idx == 12:
        frac = max(0.26, 0.42 - n * 0.018)
        step = cw * max(0.13, 0.22 - n * 0.010)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            off = i - mid
            item.ry = off * 14
            place(item, cx0 + off * step, cy0)
            item.z = n - abs(int(off))

    # ── 13 · Simple Row ──────────────────────────────────────────────────────
    elif layout_idx == 13:
        gap   = cw * 0.022
        # compute the largest size that fits n items in a row
        best_tw = (cw * 0.92 - (n - 1) * gap) / n
        for i, item in enumerate(items):
            item.tw = best_tw
            item.th = item.h * best_tw / item.w if item.w else best_tw
            if item.th > ch * 0.82:
                item.th = ch * 0.82
                item.tw = item.w * item.th / item.h if item.h else item.th
        max_th = max(it.th for it in items)
        total  = sum(it.tw for it in items) + (n - 1) * gap
        sx     = cx0 - total / 2
        for i, item in enumerate(items):
            item.x = sx
            item.y = cy0 - item.th / 2
            sx    += item.tw + gap
            item.z = i

    # ── 14 · Circle Grid ─────────────────────────────────────────────────────
    elif layout_idx == 14:
        cols = max(1, math.ceil(math.sqrt(n)))
        rows = math.ceil(n / cols)
        cell_w = cw / cols
        cell_h = ch / rows
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, cell_w * 0.94, cell_h * 0.90)
            item.x = cell_w * c + (cell_w - item.tw) / 2
            item.y = cell_h * r + (cell_h - item.th) / 2
            item.z = i

    # ── 15 · Arc Rainbow ─────────────────────────────────────────────────────
    elif layout_idx == 15:
        frac   = max(0.22, 0.38 - n * 0.015)
        r_arc  = ch * 0.44
        span_r = math.pi * 0.52
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            t_v = (i - mid) / max(1, mid) if mid > 0 else 0
            a   = t_v * span_r
            tx  = cx0 + r_arc * math.sin(a)
            ty  = cy0 - r_arc * (1 - math.cos(a)) * 0.42
            place(item, tx, ty)
            item.ry = -math.degrees(a) * 0.55
            item.z  = n - abs(i - round(mid))

    # ── 16 · Floating Shelf ──────────────────────────────────────────────────
    elif layout_idx == 16:
        frac = max(0.22, 0.40 - n * 0.018)
        step = cw * max(0.14, 0.24 - n * 0.012)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 20
            off = i - mid
            place(item, cx0 + off * step, cy0 + ch * 0.06)
            item.z = i

    # ── 17 · Stage & Wings ───────────────────────────────────────────────────
    elif layout_idx == 17:
        centre_i = n // 2
        for i, item in enumerate(items):
            dist = abs(i - centre_i)
            sign = 1 if i > centre_i else (-1 if i < centre_i else 0)
            if i == centre_i:
                item.tw, item.th = _sz(item, cw, ch, 1, frac=0.52)
                item.ry = 0
                place(item, cx0, cy0)
                item.z = 100
            else:
                item.tw, item.th = _sz(item, cw, ch, n, frac=max(0.20, 0.34 - n * 0.015))
                item.ry = sign * min(40, dist * 22)
                tx = cx0 + sign * (cw * 0.18 + dist * cw * 0.14)
                place(item, tx, cy0 + dist * ch * 0.04)
                item.z = 50 - dist * 10

    # ── 18 · Depth Stack ─────────────────────────────────────────────────────
    elif layout_idx == 18:
        base_frac = 0.58
        for i, item in enumerate(items):
            scale = max(0.55, 1.0 - i * 0.08)
            item.tw, item.th = _sz(item, cw, ch, 1, frac=base_frac * scale)
            place(item, cx0 + (i - mid) * cw * 0.012,
                        cy0 + (i - mid) * ch * 0.006)
            item.z = n - i

    # ── 19 · Fan Spread ──────────────────────────────────────────────────────
    elif layout_idx == 19:
        max_angle = min(52.0, 9.0 * n)
        pivot_y   = cy0 + ch * 0.42
        arm       = ch * 0.46
        # All cards same size (use first for reference)
        ref_tw, ref_th = _sz(items[0], cw, ch, 1, frac=0.46)
        for i, item in enumerate(items):
            item.tw, item.th = ref_tw, ref_th
            t_v   = (i - mid) / max(1, mid) if mid > 0 else 0
            ang_d = t_v * max_angle
            ang_r = math.radians(ang_d)
            item.rz = ang_d
            tx = cx0 - arm * math.sin(ang_r)
            ty = pivot_y - arm * math.cos(ang_r)
            place(item, tx, ty)
            item.z = i

    # ── 20 · Open Book ───────────────────────────────────────────────────────
    elif layout_idx == 20:
        frac = max(0.22, 0.40 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            half_n = n / 2
            if i < half_n:
                sign = -1
                pos  = half_n - 1 - i
            else:
                sign = 1
                pos  = i - half_n
            angle = sign * min(48, 18 + pos * 16)
            item.ry = angle
            tx = cx0 + sign * (item.tw * 0.52 + pos * item.tw * 0.18)
            place(item, tx, cy0)
            item.z = n - int(pos)

    # ── 21 · Center Stage ────────────────────────────────────────────────────
    elif layout_idx == 21:
        feat = items[0]
        feat.tw, feat.th = _sz(feat, cw, ch, 1, frac=0.52)
        place(feat, cx0, cy0 - ch * 0.04)
        feat.z = 100
        others_n = n - 1
        for j in range(1, n):
            item = items[j]
            item.tw, item.th = _sz(item, cw, ch, n, frac=max(0.18, 0.28 - n * 0.01))
            ar = (j - 1) * (2 * math.pi / max(1, others_n))
            r  = min(cw, ch) * 0.32
            place(item, cx0 + r * math.cos(ar), cy0 + r * math.sin(ar) * 0.55)
            item.ry = -math.degrees(ar) * 0.28
            item.z  = 10 + int(math.sin(ar) * 5)

    # ── 22 · Wide Perspective ────────────────────────────────────────────────
    elif layout_idx == 22:
        frac = max(0.24, 0.42 - n * 0.018)
        step = cw * max(0.15, 0.26 - n * 0.014)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            off = i - mid
            item.ry = off * 10
            place(item, cx0 + off * step, cy0)
            item.z = n - abs(int(off))

    # ── 23 · Depth Corridor ──────────────────────────────────────────────────
    elif layout_idx == 23:
        for i, item in enumerate(items):
            scale = max(0.38, math.pow(0.76, i))
            item.tw, item.th = _sz(item, cw, ch, 1, frac=min(0.64, 0.64 * scale + 0.05))
            place(item, cx0, cy0)
            item.z = n - i

    # ── 24 · Floating Array ──────────────────────────────────────────────────
    elif layout_idx == 24:
        frac = max(0.22, 0.38 - n * 0.016)
        step = cw * max(0.14, 0.23 - n * 0.010)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            off = i - mid
            item.ry = off * 8
            item.rz = off * 1.5
            ty = cy0 + math.sin(i * 0.85) * ch * 0.065
            place(item, cx0 + off * step, ty)
            item.z = n - abs(int(off))

    # ── 25 · Mirror Pair ─────────────────────────────────────────────────────
    elif layout_idx == 25:
        half = (n + 1) // 2
        frac = max(0.20, 0.36 - n * 0.015)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            if i < half:
                side, pos = -1, i
            else:
                side, pos = 1, i - half
            item.ry = side * (24 + pos * 8)
            tx = cx0 + side * (cw * 0.14 + pos * cw * 0.13)
            place(item, tx, cy0 + pos * ch * 0.04)
            item.z = half - pos

    # ── 26 · Trophy Shelf ────────────────────────────────────────────────────
    elif layout_idx == 26:
        shelves   = max(1, math.ceil(n / 3))
        per_shelf = math.ceil(n / shelves)
        frac      = max(0.18, 0.36 - n * 0.016)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rx = 10
            shelf   = i // per_shelf
            pos_in  = i % per_shelf
            cnt_in  = min(per_shelf, n - shelf * per_shelf)
            lm      = (cnt_in - 1) / 2
            tx = cx0 + (pos_in - lm) * (item.tw * 1.12)
            ty = cy0 - (shelves - 1 - shelf) * ch * 0.22 + (shelves - 1) * ch * 0.11
            place(item, tx, ty)
            item.z = i

    # ── 27 · Radial Display ──────────────────────────────────────────────────
    elif layout_idx == 27:
        frac = max(0.20, 0.36 - n * 0.014)
        r    = min(cw, ch) * 0.28
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            ar = i * (2 * math.pi / n)
            place(item, cx0 + r * math.cos(ar), cy0 + r * math.sin(ar) * 0.62)
            item.ry = -math.degrees(ar) * 0.38
            item.z  = int(math.sin(ar) * 30)

    # ── 28 · Perspective Grid ────────────────────────────────────────────────
    elif layout_idx == 28:
        cols = max(2, math.ceil(math.sqrt(n)))
        rows = math.ceil(n / cols)
        cell_w = cw * 0.86 / cols
        cell_h = ch * 0.76 / rows
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.88)
            item.rx = 12
            item.ry = (c - (cols - 1) / 2) * 8
            item.x = cw * 0.07 + c * cell_w + (cell_w - item.tw) / 2
            item.y = ch * 0.12 + r * cell_h + (cell_h - item.th) / 2
            item.z = rows - r

    # ── 29 · Spiral Stack ────────────────────────────────────────────────────
    elif layout_idx == 29:
        frac = max(0.22, 0.38 - n * 0.015)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            fi  = i / max(1, n - 1)
            ar  = fi * 2.4 * math.pi
            r   = fi * cw * 0.26
            place(item, cx0 + r * math.cos(ar), cy0 + r * math.sin(ar) * 0.48)
            item.ry = -math.degrees(ar) * 0.32
            item.rz =  math.degrees(ar) * 0.08
            item.z  = i

    # ── 30 · Layered Frames ──────────────────────────────────────────────────
    elif layout_idx == 30:
        for i, item in enumerate(items):
            off  = i - mid
            frac = max(0.22, 0.56 - abs(off) * 0.06)
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.rz = off * 5
            item.ry = off * 9
            place(item, cx0 + off * cw * 0.055, cy0 + off * ch * 0.028)
            item.z = n - abs(int(off))

    # ╔══════════════════════════════════════════════════════════════════════╗
    # ║  SECTION B — Flat / Editorial Layouts  (31 – 50)                    ║
    # ╚══════════════════════════════════════════════════════════════════════╝

    # ── 31 · Bento Grid ──────────────────────────────────────────────────────
    elif layout_idx == 31:
        PAD = 0.03
        # Slot definitions as (left, top, width, height) — all fractions of canvas
        slot_maps = {
            1: [(PAD, 0.08, 1-2*PAD, 0.84)],
            2: [(PAD, 0.08, 0.46, 0.84), (0.54, 0.08, 0.46-PAD, 0.84)],
            3: [(PAD, 0.08, 0.46, 0.84), (0.54, 0.08, 0.46-PAD, 0.40),
                (0.54, 0.52, 0.46-PAD, 0.40)],
            4: [(PAD, 0.08, 0.46, 0.40), (PAD, 0.52, 0.22, 0.40),
                (0.28, 0.52, 0.22, 0.40), (0.54, 0.08, 0.46-PAD, 0.84)],
            5: [(PAD, 0.08, 0.46, 0.40), (PAD, 0.52, 0.46, 0.40),
                (0.54, 0.08, 0.22, 0.84), (0.78, 0.08, 0.20, 0.40),
                (0.78, 0.52, 0.20, 0.40)],
        }
        slots = slot_maps.get(min(n, 5), slot_maps[5])
        cols  = max(3, math.ceil(math.sqrt(n)))
        rows  = math.ceil(n / cols)

        if n <= 5:
            for i, item in enumerate(items):
                if i >= len(slots): break
                sx, sy, sw, sh = slots[i]
                cell_w = cw * sw;  cell_h = ch * sh
                item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.96)
                item.x = cw * sx + (cell_w - item.tw) / 2
                item.y = ch * sy + (cell_h - item.th) / 2
                item.z = i
        else:
            cell_w = cw * 0.92 / cols;  cell_h = ch * 0.84 / rows
            for i, item in enumerate(items):
                c, r = i % cols, i // cols
                item.tw, item.th = _fit_cell(item, cell_w, cell_h)
                item.x = cw * 0.04 + c * cell_w + (cell_w - item.tw) / 2
                item.y = ch * 0.08 + r * cell_h + (cell_h - item.th) / 2
                item.z = i

    # ── 32 · Hero Layout ─────────────────────────────────────────────────────
    elif layout_idx == 32:
        if n == 1:
            item = items[0]
            item.tw, item.th = _sz(item, cw, ch, 1, frac=0.70)
            place(item, cx0, cy0)
        else:
            hero = items[0]
            hero.tw, hero.th = _sz(hero, cw, ch, 1, frac=0.52)
            hero.x = cw * 0.03;  hero.y = cy0 - hero.th / 2;  hero.z = 10
            rest    = items[1:]
            nrest   = len(rest)
            area_h  = ch * 0.88
            each_h  = (area_h - (nrest - 1) * ch * 0.022) / max(1, nrest)
            for j, item in enumerate(rest):
                item.th = each_h * 0.94
                item.tw = item.w * item.th / item.h if item.h else item.th
                item.tw = min(item.tw, cw * 0.40)
                item.x  = cw - item.tw - cw * 0.03
                item.y  = ch * 0.06 + j * (each_h + ch * 0.022)
                item.z  = j

    # ── 33 · Magazine Spread ─────────────────────────────────────────────────
    elif layout_idx == 33:
        specs = [
            (0.03, 0.06, 0.56, 0.88),
            (0.62, 0.06, 0.35, 0.42),
            (0.62, 0.52, 0.35, 0.42),
        ]
        for i, item in enumerate(items):
            if i < len(specs):
                sx, sy, sw, sh = specs[i]
                cell_w = cw * sw;  cell_h = ch * sh
                item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.96)
                item.x = cw * sx + (cell_w - item.tw) / 2
                item.y = ch * sy + (cell_h - item.th) / 2
                item.z = len(specs) - i
            else:
                # overflow strip at bottom
                k     = i - len(specs)
                item.tw, item.th = _sz(item, cw, ch, n, frac=0.16)
                item.x = cw * 0.03 + k * (item.tw + cw * 0.02)
                item.y = ch * 0.84
                item.z = 0

    # ── 34 · Product Lineup ──────────────────────────────────────────────────
    elif layout_idx == 34:
        gap = cw * 0.022
        # Equal-width columns filling canvas
        col_w = (cw * 0.92 - (n - 1) * gap) / max(1, n)
        sx    = cw * 0.04
        for i, item in enumerate(items):
            item.th = ch * 0.72
            item.tw = item.w * item.th / item.h if item.h else item.th
            item.tw = min(item.tw, col_w)
            item.x  = sx + (col_w - item.tw) / 2
            item.y  = cy0 - item.th / 2
            sx      += col_w + gap
            item.z  = i

    # ── 35 · Pinterest Board ─────────────────────────────────────────────────
    elif layout_idx == 35:
        cols       = max(2, min(4, n))
        col_w      = (cw * 0.94) / cols
        col_tops   = [ch * 0.05] * cols
        gap        = ch * 0.022
        for i, item in enumerate(items):
            col    = i % cols
            item.tw = col_w * 0.90
            item.th = item.h * item.tw / item.w if item.w else item.tw
            item.th = min(item.th, ch * 0.55)
            item.x  = cw * 0.03 + col * col_w + (col_w * 0.90 - item.tw) / 2
            item.y  = col_tops[col]
            col_tops[col] += item.th + gap
            item.z  = i

    # ── 36 · App Gallery ─────────────────────────────────────────────────────
    elif layout_idx == 36:
        cols   = 3
        rows   = math.ceil(n / cols)
        cell_w = cw * 0.88 / cols
        cell_h = ch * 0.85 / rows
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.88)
            item.x = cw * 0.06 + c * cell_w + (cell_w - item.tw) / 2
            item.y = ch * 0.075 + r * cell_h + (cell_h - item.th) / 2
            item.z = i

    # ── 37 · Balanced Grid ───────────────────────────────────────────────────
    elif layout_idx == 37:
        cols   = max(1, math.ceil(math.sqrt(n)))
        rows   = math.ceil(n / cols)
        pad_x  = cw * 0.045;  pad_y = ch * 0.045
        gap_x  = cw * 0.022;  gap_y = ch * 0.022
        cell_w = (cw - 2 * pad_x - (cols - 1) * gap_x) / cols
        cell_h = (ch - 2 * pad_y - (rows - 1) * gap_y) / rows
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.96)
            item.x = pad_x + c * (cell_w + gap_x) + (cell_w - item.tw) / 2
            item.y = pad_y + r * (cell_h + gap_y) + (cell_h - item.th) / 2
            item.z = i

    # ── 38 · Z-Pattern Flow ──────────────────────────────────────────────────
    elif layout_idx == 38:
        frac   = max(0.20, 0.38 - n * 0.018)
        cols   = 3
        xs     = [cw * 0.05, cw * 0.38, cw * 0.72]
        row_h  = ch * 0.34
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            row = i // cols
            col = i % cols
            # Alternate row reading direction
            effective_col = col if row % 2 == 0 else (cols - 1 - col)
            item.x = xs[effective_col]
            item.y = ch * 0.08 + row * row_h
            item.z = i

    # ── 39 · Polaroid Wall ───────────────────────────────────────────────────
    elif layout_idx == 39:
        frac = max(0.16, 0.38 - n * 0.016)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            item.corner_radius = 5.0
            # Deterministic scatter
            seed_x = (i * 137 + 29) % 83
            seed_y = (i * 97 + 53)  % 79
            safe_w = cw * 0.84 - item.tw
            safe_h = ch * 0.84 - item.th
            item.x  = cw * 0.08 + (seed_x / 83) * max(0, safe_w)
            item.y  = ch * 0.08 + (seed_y / 79) * max(0, safe_h)
            item.rz = ((i * 23 + 7) % 32) - 16
            item.z  = i

    # ── 40 · Timeline Strip ──────────────────────────────────────────────────
    elif layout_idx == 40:
        gap   = cw * 0.018
        tw_ea = max(cw * 0.12, (cw * 0.94 - (n - 1) * gap) / max(1, n))
        sx    = cw * 0.03
        for i, item in enumerate(items):
            item.tw = tw_ea
            item.th = item.h * tw_ea / item.w if item.w else tw_ea
            item.th = min(item.th, ch * 0.42)
            item.x  = sx
            item.y  = cy0 - item.th / 2 + (0 if i % 2 == 0 else ch * 0.10)
            sx     += tw_ea + gap
            item.z  = i

    # ── 41 · Hero + Thumbnails ───────────────────────────────────────────────
    elif layout_idx == 41:
        if n == 1:
            item = items[0]
            item.tw, item.th = _sz(item, cw, ch, 1, frac=0.70)
            place(item, cx0, cy0)
        else:
            hero   = items[0]
            hero.tw = cw * 0.88
            hero.th = hero.h * hero.tw / hero.w if hero.w else hero.tw
            hero.th = min(hero.th, ch * 0.66)
            hero.x  = cx0 - hero.tw / 2
            hero.y  = ch * 0.04
            hero.z  = 10
            rest  = items[1:]
            nrest = len(rest)
            gap   = cw * 0.016
            tw_ea = (cw * 0.88 - (nrest - 1) * gap) / max(1, nrest)
            sx    = cx0 - cw * 0.44
            for j, item in enumerate(rest):
                item.tw = tw_ea
                item.th = item.h * tw_ea / item.w if item.w else tw_ea
                item.th = min(item.th, ch * 0.22)
                item.x  = sx
                item.y  = ch - item.th - ch * 0.04
                sx     += tw_ea + gap
                item.z  = j

    # ── 42 · Feature Spotlight ───────────────────────────────────────────────
    elif layout_idx == 42:
        if n == 1:
            item = items[0]
            item.tw, item.th = _sz(item, cw, ch, 1, frac=0.68)
            place(item, cx0, cy0)
        else:
            feat = items[0]
            feat.tw, feat.th = _sz(feat, cw, ch, 1, frac=0.54)
            place(feat, cx0, cy0)
            feat.z = 100
            ring_positions = [
                (cx0 - cw * 0.36, cy0),
                (cx0 + cw * 0.36, cy0),
                (cx0, cy0 - ch * 0.36),
                (cx0, cy0 + ch * 0.36),
                (cx0 - cw * 0.28, cy0 - ch * 0.28),
                (cx0 + cw * 0.28, cy0 - ch * 0.28),
            ]
            for j in range(1, n):
                item = items[j]
                item.tw, item.th = _sz(item, cw, ch, n, frac=max(0.14, 0.24 - n * 0.01))
                px, py = ring_positions[(j - 1) % len(ring_positions)]
                place(item, px, py)
                item.z = j

    # ── 43 · Brick Wall ──────────────────────────────────────────────────────
    elif layout_idx == 43:
        cols   = max(2, min(5, n))
        rows   = math.ceil(n / cols)
        cell_w = cw * 0.90 / cols
        cell_h = ch * 0.88 / rows
        gap    = cell_w * 0.04
        for i, item in enumerate(items):
            r, c = i // cols, i % cols
            offset_x = (cell_w * 0.5) if (r % 2 == 1) else 0.0
            item.tw, item.th = _fit_cell(item, cell_w - gap, cell_h * 0.92)
            item.x = cw * 0.05 + c * cell_w + offset_x + (cell_w - gap - item.tw) / 2
            item.y = ch * 0.06 + r * cell_h + (cell_h * 0.92 - item.th) / 2
            item.z = i

    # ── 44 · Cross Layout ────────────────────────────────────────────────────
    elif layout_idx == 44:
        pos_sizes = [
            (cx0,        cy0,        0.40),   # centre
            (cx0,        ch * 0.14,  0.22),   # top
            (cx0,        ch * 0.86,  0.22),   # bottom
            (cw * 0.12,  cy0,        0.22),   # left
            (cw * 0.88,  cy0,        0.22),   # right
        ]
        for i, item in enumerate(items[:5]):
            tx, ty, frac = pos_sizes[i]
            item.tw, item.th = _sz(item, cw, ch, 1, frac=frac)
            place(item, tx, ty)
            item.z = 5 - i

    # ── 45 · Split Panels ────────────────────────────────────────────────────
    elif layout_idx == 45:
        if n == 1:
            item = items[0]
            item.tw, item.th = _sz(item, cw, ch, 1, frac=0.68)
            place(item, cx0, cy0)
        else:
            half    = (n + 1) // 2
            panel_w = (cw - cw * 0.04) / 2
            for i, item in enumerate(items):
                side      = 0 if i < half else 1
                pos_side  = i if side == 0 else i - half
                cnt       = half if side == 0 else n - half
                cell_h    = (ch * 0.88) / max(1, cnt)
                item.th   = cell_h * 0.93
                item.tw   = item.w * item.th / item.h if item.h else item.th
                item.tw   = min(item.tw, panel_w * 0.93)
                item.x    = cw * 0.02 + side * (panel_w + cw * 0.02) + (panel_w - item.tw) / 2
                item.y    = ch * 0.06 + pos_side * cell_h + (cell_h - item.th) / 2
                item.z    = i

    # ── 46 · Scattered Desk ──────────────────────────────────────────────────
    elif layout_idx == 46:
        frac = max(0.18, 0.40 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            seed  = i * 17 + 3
            item.rz = ((seed * 7) % 34) - 17.0
            xr   = ((seed * 13) % 80) / 100.0
            yr   = ((seed * 11) % 80) / 100.0
            item.x = cw * 0.05 + xr * max(0, cw * 0.85 - item.tw)
            item.y = ch * 0.05 + yr * max(0, ch * 0.85 - item.th)
            item.z = i

    # ── 47 · Overlapping Cards ───────────────────────────────────────────────
    elif layout_idx == 47:
        ref_tw, ref_th = _sz(items[0], cw, ch, 1, frac=0.50)
        overlap = 0.36
        total_w = ref_tw + (n - 1) * ref_tw * overlap
        sx      = cx0 - total_w / 2
        for i, item in enumerate(items):
            item.tw, item.th = ref_tw, ref_th
            item.x  = sx + i * ref_tw * overlap
            item.y  = cy0 - ref_th / 2 + (i - mid) * ch * 0.012
            item.rz = (i - mid) * 2.8
            item.z  = i

    # ── 48 · Framed Gallery ──────────────────────────────────────────────────
    elif layout_idx == 48:
        cols        = max(1, math.ceil(math.sqrt(n)))
        rows        = math.ceil(n / cols)
        margin      = cw * 0.055
        gap         = cw * 0.030
        frame_b     = cw * 0.014
        cell_w = (cw - 2 * margin - (cols - 1) * gap) / cols
        cell_h = (ch - 2 * margin - (rows - 1) * gap) / rows
        inner_w = cell_w - 2 * frame_b
        inner_h = cell_h - 2 * frame_b
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, inner_w, inner_h, pad=0.98)
            item.x = margin + c * (cell_w + gap) + frame_b + (inner_w - item.tw) / 2
            item.y = margin + r * (cell_h + gap) + frame_b + (inner_h - item.th) / 2
            item.z = i

    # ── 49 · Diagonal Stack ──────────────────────────────────────────────────
    elif layout_idx == 49:
        frac = max(0.24, 0.42 - n * 0.018)
        for i, item in enumerate(items):
            item.tw, item.th = _sz(item, cw, ch, n, frac=frac)
            if n > 1:
                t_v = i / (n - 1)
                item.x = cw * 0.04 + t_v * (cw * 0.88 - item.tw)
                item.y = ch * 0.04 + t_v * (ch * 0.88 - item.th)
            else:
                item.x = cx0 - item.tw / 2
                item.y = cy0 - item.th / 2
            item.rz = (i - mid) * 3.0
            item.z  = n - i

    # ── 50 · Minimal Showcase ────────────────────────────────────────────────
    elif layout_idx == 50:
        cols   = max(1, math.ceil(math.sqrt(n)))
        rows   = math.ceil(n / cols)
        margin = min(cw, ch) * 0.08
        gap    = min(cw, ch) * 0.045
        area_w = cw - 2 * margin - (cols - 1) * gap
        area_h = ch - 2 * margin - (rows - 1) * gap
        cell_w = area_w / cols
        cell_h = area_h / rows
        for i, item in enumerate(items):
            c, r = i % cols, i // cols
            item.tw, item.th = _fit_cell(item, cell_w, cell_h, pad=0.95)
            item.x = margin + c * (cell_w + gap) + (cell_w - item.tw) / 2
            item.y = margin + r * (cell_h + gap) + (cell_h - item.th) / 2
            item.z = i


# ════════════════════════════════════════════════════════════════ Renderer ══

def draw_item(painter: QPainter, item: RenderItem):
    # Use floats for all coordinates to maintain sub-pixel precision
    tw, th = item.tw, item.th
    if tw < 2 or th < 2:
        return

    painter.save()

    # Enable all high-quality rendering hints for this item
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # Build world transform: rotate around image centre, then position
    cx_i, cy_i = tw / 2.0, th / 2.0
    t = QTransform()
    t.translate(item.x + cx_i, item.y + cy_i)
    if item.rz: t.rotate(item.rz, Qt.ZAxis)
    if item.ry: t.rotate(item.ry, Qt.YAxis)
    if item.rx: t.rotate(item.rx, Qt.XAxis)
    t.translate(-cx_i, -cy_i)
    painter.setTransform(t, True)

    if item.opacity < 1.0:
        painter.setOpacity(item.opacity)

    # Premium soft drop-shadow
    if item.shadow:
        sx = max(6.0, min(tw, th) * 0.02)
        sy = max(10.0, min(tw, th) * 0.032)
        sp = QPainterPath()
        sp.addRoundedRect(QRectF(sx, sy, tw, th), item.corner_radius, item.corner_radius)
        # Using a softer, slightly darker shadow for high resolution
        painter.fillPath(sp, QColor(0, 0, 0, 72))

    # High-quality clip and draw
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, tw, th), item.corner_radius, item.corner_radius)
    painter.setClipPath(clip)
    
    # CRITICAL: We draw the original high-res image directly into the target rect.
    # The painter's SmoothPixmapTransform hint provides superior interpolation 
    # compared to pre-scaling the QImage.
    painter.drawImage(QRectF(0, 0, tw, th), item.img)

    painter.restore()


# ════════════════════════════════════════════════════════════════════ CLI ══

ASCII_TITLE = """\033[95m
  ██████  ██░ ██  ▒█████   █     █░ ▄████▄   ▄▄▄       ██████ ▓█████ 
▒██    ▒ ▓██░ ██▒▒██▒  ██▒▓█░ █ ▒█▒▒██▀ ▀█  ▒████▄   ▒██    ▒ ▓█   ▀ 
░ ▓██▄   ▒██▀▀██░▒██░  ██▒▒█░ █ ▒█ ▒▓█    ▄ ▒██  ▀█▄ ░ ▓██▄   ▒███   
  ▒   ██▒░▓█ ░██ ▒██   ██░░█░ █ ▒█ ▒▓▓▄ ▄██▒░██▄▄▄▄██  ▒   ██▒▒▓█  ▄ 
▒██████▒▒░▓█▒░██▓░ ████▓▒░░░██▒██▓ ▒ ▓███▀ ░ ▓█   ▓██▒▒██████▒▒▒████▒
▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒░ ▒░▒░▒░ ░ ▓░▒ ▒  ░ ░▒ ▒  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░░ ▒░ ░
\033[0m"""


def get_key() -> str:
    if sys.platform == "win32":
        import msvcrt
        c = msvcrt.getch()
        if c == b'\x03': sys.exit(0)
        if c in (b'\xe0', b'\x00'):
            c2 = msvcrt.getch()
            return {'H':'up','P':'down','K':'left','M':'right'}.get(c2.decode('latin-1','ignore'), 'other')
        if c == b'\r': return 'enter'
        if c == b' ':  return 'space'
        return c.decode('utf-8', 'ignore')
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x03': sys.exit(0)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    return {'A':'up','B':'down','C':'right','D':'left'}.get(ch3, 'other')
            if ch in ('\r', '\n'): return 'enter'
            if ch == ' ':         return 'space'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def interactive_menu(step_title: str, options: list[str], multi: bool = False):
    selected:  set[int] = set()
    current_idx: int    = 0
    display_opts = list(options)
    if multi:
        display_opts.append("\033[44m\033[97m [ DONE / NEXT ] \033[0m")

    sys.stdout.write('\033[?25l')
    try:
        while True:
            sys.stdout.write('\033[H\033[J')
            print(ASCII_TITLE)
            print("Showcase Builder  ·  Professional 3D Image Compositor")
            print("=" * 65)
            print(f"\033[93m{step_title}\033[0m")
            print("  \033[96m↑ ↓\033[0m navigate", end="")
            if multi:
                print("  \033[96mSPACE\033[0m select  \033[96mENTER\033[0m confirm / [ DONE ]")
            else:
                print("  \033[96mENTER\033[0m select")
            print("-" * 65)

            MAX_DISP = 14
            start = max(0, current_idx - MAX_DISP // 2)
            end   = min(len(display_opts), start + MAX_DISP)
            if end - start < MAX_DISP:
                start = max(0, end - MAX_DISP)

            if start > 0: print("   ···")
            for i in range(start, end):
                opt    = display_opts[i]
                prefix = "\033[92m > \033[0m" if i == current_idx else "   "
                bold   = "\033[1m" if i == current_idx else "\033[0m"
                if multi:
                    if i == len(display_opts) - 1:
                        print(f"{prefix}{opt}")
                    else:
                        box = "\033[96m[x]\033[0m" if i in selected else "[ ]"
                        print(f"{prefix}{box} {bold}{opt}\033[0m")
                else:
                    print(f"{prefix}{bold}{opt}\033[0m")
            if end < len(display_opts): print("   ···")

            sys.stdout.flush()
            key = get_key()
            n_opts = len(display_opts)
            if key == 'up':
                current_idx = (current_idx - 1) % n_opts
            elif key == 'down':
                current_idx = (current_idx + 1) % n_opts
            elif key == 'space' and multi and current_idx < n_opts - 1:
                selected.discard(current_idx) if current_idx in selected else selected.add(current_idx)
            elif key == 'enter':
                if multi:
                    if current_idx == n_opts - 1:
                        return sorted(selected)
                    else:
                        selected.discard(current_idx) if current_idx in selected else selected.add(current_idx)
                else:
                    return current_idx
    finally:
        sys.stdout.write('\033[?25h\033[H\033[J')
        print(ASCII_TITLE)


def show_loading():
    print("\n\033[94m[+]\033[0m \033[1mCompositing 3D Showcase ...\033[0m")
    # Compact 3x3 pulsing grid
    sys.stdout.write("\n\n\n")
    colors = ["\033[38;5;236m", "\033[38;5;240m", "\033[38;5;245m", "\033[38;5;255m", "\033[38;5;245m", "\033[38;5;240m"]
    
    for i in range(36):
        sys.stdout.write("\033[3A") # Move up 3 lines
        for r in range(3):
            line = "        " # Indent for centering
            for c in range(3):
                # Diagonal pulse wave using smaller bullets
                idx = (i - r - c) % len(colors)
                line += f"{colors[idx]}• "
            sys.stdout.write(f"\r{line}\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.07)
    
    sys.stdout.write("\033[3A\r                                \n                                \n                                \r")
    print("   \033[92m[✓]\033[0m \033[1mShowcase Rendered Successfully!\033[0m\n")


# ════════════════════════════════════════════════════════════════ Session ══

TEMPLATES = [
    "01. Isometric Stack",        "02. Perspective Right",
    "03. Perspective Left",       "04. Coverflow",
    "05. V-Formation",            "06. Diagonal Cascade",
    "07. Tilted Floor",           "08. Cylinder Inward",
    "09. Step Stairs",            "10. Focus Center",
    "11. Deck of Cards",          "12. Panorama Sweep",
    "13. Simple Row",             "14. Circle Grid",
    "15. Arc Rainbow",            "16. Floating Shelf",
    "17. Stage & Wings",          "18. Depth Stack",
    "19. Fan Spread",             "20. Open Book",
    "21. Center Stage",           "22. Wide Perspective",
    "23. Depth Corridor",         "24. Floating Array",
    "25. Mirror Pair",            "26. Trophy Shelf",
    "27. Radial Display",         "28. Perspective Grid",
    "29. Spiral Stack",           "30. Layered Frames",
    "31. Bento Grid",             "32. Hero Layout",
    "33. Magazine Spread",        "34. Product Lineup",
    "35. Pinterest Board",        "36. App Gallery",
    "37. Balanced Grid",          "38. Z-Pattern Flow",
    "39. Polaroid Wall",          "40. Timeline Strip",
    "41. Hero + Thumbnails",      "42. Feature Spotlight",
    "43. Brick Wall",             "44. Cross Layout",
    "45. Split Panels",           "46. Scattered Desk",
    "47. Overlapping Cards",      "48. Framed Gallery",
    "49. Diagonal Stack",         "50. Minimal Showcase",
]

BG_OPTS = [
    "00. None (Transparent)",     "01. White",
    "02. Black",                  "03. Deep Space",
    "04. Sunset",                 "05. Ocean Deep",
    "06. Purple Haze",            "07. Forest Night",
    "08. Rose Gold",              "09. Neon City",
    "10. Charcoal",               "11. Frosted Glass",
    "12. Aurora",                 "13. Warm Cream",
    "14. Midnight Blue",          "15. Golden Hour",
    "16. Dynamic Colorful",
]

RATIOS = [
    "16:9  — 3840 × 2160 (Ultra HD 4K)",
    "9:16  — 2160 × 3840 (Ultra HD 4K)",
    "1:1   — 3000 × 3000 (Extreme Quality)",
    "4:3   — 3200 × 2400 (Professional Print)",
]
RATIO_DIMS = [(3840,2160),(2160,3840),(3000,3000),(3200,2400)]


def run_session(cwd: str) -> bool:
    exts  = ('.png','.jpg','.jpeg','.webp','.bmp','.gif')
    files = sorted(f for f in os.listdir(cwd) if f.lower().endswith(exts))

    if not files:
        print(ASCII_TITLE)
        print("\n[!] No images found in the current directory.\n")
        return False

    # ── Phase 1 · Image selection ────────────────────────────────────────────
    sel_idx = interactive_menu("[1/5]  SELECT IMAGES", files, multi=True)
    if not sel_idx:
        return False
    selected = [files[i] for i in sel_idx]

    while True:
        # ── Phase 2 · Background ─────────────────────────────────────────────────
        bg_idx = interactive_menu("[2/5]  SELECT BACKGROUND", BG_OPTS)

        # ── Phase 3 · Layout template ────────────────────────────────────────────
        layout_idx = interactive_menu("[3/5]  SELECT LAYOUT", TEMPLATES) + 1

        # ── Phase 4 · Canvas ratio ───────────────────────────────────────────────
        ratio_idx = interactive_menu("[4/5]  SELECT CANVAS RATIO", RATIOS)
        cw, ch    = RATIO_DIMS[ratio_idx]

        show_loading()

        # ── Build render items ───────────────────────────────────────────────────
        render_items = [RenderItem(os.path.join(cwd, p)) for p in selected]
        apply_layout(render_items, layout_idx, cw, ch)
        render_items.sort(key=lambda it: it.z)

        max_frames = max((len(it.frames) for it in render_items), default=1)

        # ── Render ───────────────────────────────────────────────────────────────
        def new_canvas():
            img = QImage(cw, ch, QImage.Format_ARGB32_Premultiplied)
            p   = QPainter(img)
            # Apply maximum quality rendering hints
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.TextAntialiasing)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            return img, p

        if max_frames > 1 and HAS_VIDEO:
            out_path = os.path.join(cwd, f"showcase_{int(time.time())}.gif")
            frames_arr = []
            for fi in range(max_frames):
                img, painter = new_canvas()
                draw_background(painter, cw, ch, bg_idx)
                for item in render_items:
                    item.set_frame(fi)
                    draw_item(painter, item)
                painter.end()
                rgb = img.convertToFormat(QImage.Format_RGB888)
                ptr = rgb.constBits()
                frames_arr.append(np.array(ptr).reshape(ch, cw, 3))
            iio.imwrite(out_path, frames_arr, extension=".gif", loop=0, duration=1000/30)
        else:
            out_path = os.path.join(cwd, f"showcase_{int(time.time())}.png")
            img, painter = new_canvas()
            draw_background(painter, cw, ch, bg_idx)
            for item in render_items:
                item.set_frame(0)
                draw_item(painter, item)
            painter.end()
            img.save(out_path)

        print(f"[✓] Exported → {out_path}")

        # Open the result
        if sys.platform == "win32":
            os.startfile(out_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", out_path])
        else:
            subprocess.call(["xdg-open", out_path])

        # ── Phase 5 · Repeat? ────────────────────────────────────────────────────
        choice = interactive_menu(
            "[5/5]  CREATE ANOTHER SHOWCASE?",
            ["Yes   — Start over", "Edit  — Change Background/Layout", "No    — Exit"]
        )
        if choice == 0: return True
        if choice == 1: continue
        return False


def main():
    if sys.platform == "win32":
        os.system("")   # enable VT-100 on Windows

    app = QGuiApplication(sys.argv)   # created once, never recreated
    cwd = os.getcwd()

    while True:
        if not run_session(cwd):
            print("\033[92m  Thank you for using Showcase Builder!\033[0m\n")
            break


if __name__ == "__main__":
    main()