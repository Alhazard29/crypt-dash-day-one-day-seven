#!/usr/bin/env python3
"""CRYPT DASH, day one vs day seven.

One tiny top-down game, drawn twice from the same simulation: the bare build
of day one and the build after a week of daily updates. The map, the start
tile and the player's path are identical in both, and the camera never moves,
so the only thing that changes between two cuts is the game itself.

Usage: python3 render.py <frames.rgb> <audio.wav>
Writes raw RGB24 frames (1080x1920, 30 fps) and a mono 44.1 kHz soundtrack.
"""
import math
import random
import struct
import sys
import wave

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
TILE = 120
COLS, ROWS = W // TILE, H // TILE  # 9 x 16
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# The one map both builds share. # wall, . floor, o coin, T torch (a wall).
MAP = [
    "#########",
    "#########",
    "#T#####T#",
    "#..o....#",
    "#.##.##.#",
    "#.#o..#o#",
    "#.#.#.#.#",
    "#o..#..o#",
    "#T#.#.#T#",
    "#..o..#.#",
    "#.###.#.#",
    "#.o...o.#",
    "#.#.###.#",
    "#...o...#",
    "#########",
    "#########",
]
assert len(MAP) == ROWS and all(len(r) == COLS for r in MAP)

# The player's route, tile by tile, the same in both builds.
ROUTE = [(1, 13), (1, 11), (5, 11), (5, 9), (3, 9), (3, 7), (1, 7), (1, 3),
         (4, 3), (4, 5), (5, 5), (5, 7), (7, 7), (7, 3), (1, 3), (1, 7),
         (3, 7), (3, 9), (5, 9), (5, 11), (7, 11), (7, 13), (4, 13)]
SPEED = 3.4  # tiles a second


def centre(tx, ty):
    return tx * TILE + TILE // 2, ty * TILE + TILE // 2


def route_legs():
    legs, t = [], 0.0
    for a, b in zip(ROUTE, ROUTE[1:]):
        d = abs(a[0] - b[0]) + abs(a[1] - b[1])
        legs.append((t, t + d / SPEED, a, b))
        t += d / SPEED
    return legs


LEGS = route_legs()
ROUTE_END = LEGS[-1][1]


def player_at(t):
    """Pixel position and facing of the player at game time t."""
    t = max(0.0, min(t, ROUTE_END - 1e-6))
    for t0, t1, a, b in LEGS:
        if t0 <= t < t1:
            k = (t - t0) / (t1 - t0)
            ax, ay = centre(*a)
            bx, by = centre(*b)
            face = (b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1])
            return ax + (bx - ax) * k, ay + (by - ay) * k, face
    x, y = centre(*ROUTE[-1])
    return x, y, (0, 1)


def coin_times():
    """When the player first touches each coin: {(tx, ty): game time}."""
    coins = {(x, y) for y, r in enumerate(MAP) for x, c in enumerate(r) if c == "o"}
    got, t = {}, 0.0
    while t < ROUTE_END and len(got) < len(coins):
        px, py, _ = player_at(t)
        for c in coins - set(got):
            cx, cy = centre(*c)
            if abs(px - cx) + abs(py - cy) < TILE * 0.45:
                got[c] = t
        t += 1 / 120
    return coins, got


COINS, GOT = coin_times()
TORCHES = [(x, y) for y, r in enumerate(MAP) for x, c in enumerate(r) if c == "T"]

# Patrols: (tile a, tile b, period, phase). Day one ships only the first.
PATROLS = [((5, 13), (7, 13), 2.6, 0.0), ((3, 11), (3, 13), 2.2, 0.3),
           ((7, 9), (7, 11), 2.0, 0.6), ((5, 5), (5, 7), 2.4, 0.1),
           ((2, 3), (7, 3), 4.2, 0.5), ((3, 5), (3, 6), 1.6, 0.2)]


def patrol_at(p, t):
    a, b, period, phase = p
    k = 0.5 - 0.5 * math.cos(2 * math.pi * (t / period + phase))
    ax, ay = centre(*a)
    bx, by = centre(*b)
    return ax + (bx - ax) * k, ay + (by - ay) * k


def score_at(t):
    return sum(1 for v in GOT.values() if v <= t)


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- day one --
def draw_day1(t):
    im = Image.new("RGB", (W, H), (24, 24, 24))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(MAP):
        for x, c in enumerate(row):
            if c in "#T":
                d.rectangle([x * TILE, y * TILE, x * TILE + TILE - 1, y * TILE + TILE - 1],
                            fill=(92, 92, 92))
    for c in COINS:
        if GOT.get(c, 1e9) > t:
            cx, cy = centre(*c)
            d.rectangle([cx - 14, cy - 14, cx + 14, cy + 14], fill=(230, 200, 40))
    ex, ey = patrol_at(PATROLS[0], t)
    d.rectangle([ex - 30, ey - 30, ex + 30, ey + 30], fill=(210, 50, 50))
    px, py, _ = player_at(t)
    d.rectangle([px - 32, py - 32, px + 32, py + 32], fill=(245, 245, 245))
    d.text((28, 62), "score: %d" % score_at(t), font=font(MONO, 34), fill=(200, 200, 200))
    return im


# -------------------------------------------------------------- day seven --
def radial(size, colour, power=2.0, peak=255):
    """A soft round sprite: colour at the centre fading to nothing."""
    im = Image.new("RGBA", (size, size), colour + (0,))
    px = im.load()
    r = size / 2
    for y in range(size):
        for x in range(size):
            k = 1 - min(1.0, math.hypot(x - r, y - r) / r)
            px[x, y] = colour + (int(peak * k ** power),)
    return im


def build_floor():
    """The static layer of day seven: stone floor, bevelled walls, moss."""
    rnd = random.Random(7)
    im = Image.new("RGB", (W, H), (18, 16, 26))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(MAP):
        for x, c in enumerate(row):
            x0, y0 = x * TILE, y * TILE
            if c in "#T":
                d.rectangle([x0, y0, x0 + TILE - 1, y0 + TILE - 1], fill=(40, 35, 62))
                d.rectangle([x0, y0, x0 + TILE - 1, y0 + 13], fill=(78, 70, 112))
                d.rectangle([x0, y0 + TILE - 16, x0 + TILE - 1, y0 + TILE - 1], fill=(26, 22, 42))
                for _ in range(3):  # brick seams
                    sx, sy = x0 + rnd.randrange(12, 96), y0 + rnd.randrange(24, 92)
                    d.line([sx, sy, sx + rnd.randrange(14, 30), sy], fill=(28, 24, 46), width=3)
                if rnd.random() < 0.3:
                    d.ellipse([x0 + 16, y0 + 78, x0 + 52, y0 + 100], fill=(52, 96, 70))
            else:
                base = (96, 84, 108) if (x + y) % 2 else (108, 94, 120)
                d.rectangle([x0, y0, x0 + TILE - 1, y0 + TILE - 1], fill=base)
                d.rectangle([x0, y0, x0 + TILE - 1, y0 + TILE - 1], outline=(74, 64, 88), width=2)
                for _ in range(4):  # pebbles
                    sx, sy = x0 + rnd.randrange(8, 108), y0 + rnd.randrange(8, 108)
                    d.ellipse([sx, sy, sx + 6, sy + 4], fill=(126, 112, 138))
    return im


FLOOR = None
GLOW = SHADE = COINGLOW = None


def prepare():
    global FLOOR, GLOW, SHADE, COINGLOW
    FLOOR = build_floor()
    GLOW = radial(520, (255, 170, 70), 1.6, 150)
    COINGLOW = radial(120, (255, 220, 90), 2.0, 130)
    # Darkness with a lit hole, twice the frame so it can follow the player.
    small = Image.new("L", (W // 4 * 2, H // 4 * 2), 0)
    px = small.load()
    cw, ch = small.size
    for y in range(ch):
        for x in range(cw):
            k = math.hypot(x - cw / 2, y - ch / 2) / 150.0
            px[x, y] = int(105 * min(1.0, max(0.0, k - 0.7)))
    SHADE = small.resize((W * 2, H * 2), Image.BILINEAR)


def slime(d, x, y, t, tint):
    bob = math.sin(t * 7 + x * 0.01) * 5
    w, h = 36 + bob * 0.6, 30 - bob * 0.6
    d.ellipse([x - w, y - h + 6, x + w, y + h + 6], fill=tint, outline=(20, 16, 30), width=4)
    d.ellipse([x - w + 10, y - h + 10, x - 4, y - 2], fill=tuple(min(255, c + 60) for c in tint))
    for s in (-13, 13):
        d.ellipse([x + s - 7, y - 4, x + s + 7, y + 10], fill=(255, 255, 255))
        d.ellipse([x + s - 3, y + 1, x + s + 3, y + 8], fill=(20, 16, 30))


def draw_day7(t):
    im = FLOOR.copy().convert("RGBA")
    d = ImageDraw.Draw(im)
    rnd = random.Random(int(t * 12))
    # torches: flickering light, flame and drifting sparks
    for i, (tx, ty) in enumerate(TORCHES):
        cx, cy = centre(tx, ty)
        f = 0.82 + 0.18 * math.sin(t * 11 + i * 1.7) * math.sin(t * 5.3 + i)
        g = GLOW.resize((int(520 * f), int(520 * f)))
        im.alpha_composite(g, (cx - g.width // 2, cy + 40 - g.height // 2))
        d.rectangle([cx - 7, cy - 4, cx + 7, cy + 34], fill=(92, 60, 36))
        fh = 30 + 10 * f + rnd.randrange(0, 8)
        d.polygon([(cx - 15, cy), (cx, cy - fh), (cx + 15, cy)], fill=(255, 150, 40))
        d.polygon([(cx - 8, cy), (cx, cy - fh * 0.6), (cx + 8, cy)], fill=(255, 235, 150))
        for k in range(3):
            a = (t * 0.9 + k / 3 + i * 0.37) % 1.0
            sx = cx + math.sin(a * 9 + k * 2 + i) * 16
            d.ellipse([sx - 3, cy - 30 - a * 70 - 3, sx + 3, cy - 30 - a * 70 + 3],
                      fill=(255, 200, 90, int(255 * (1 - a))))
    # coins spin and glow; a pickup bursts and floats a +10
    for c in sorted(COINS):
        cx, cy = centre(*c)
        got = GOT.get(c, 1e9)
        if got > t:
            im.alpha_composite(COINGLOW, (cx - 60, cy - 60))
            w = abs(math.cos(t * 4 + cx * 0.02)) * 20 + 4
            hop = math.sin(t * 5 + cy * 0.03) * 5
            d.ellipse([cx - w, cy - 22 + hop, cx + w, cy + 22 + hop], fill=(255, 208, 60),
                      outline=(150, 96, 20), width=4)
            d.ellipse([cx - w * 0.4, cy - 12 + hop, cx + w * 0.1, cy + hop], fill=(255, 244, 180))
        elif t - got < 0.7:
            a = (t - got) / 0.7
            for k in range(10):
                ang = k * math.pi / 5 + 0.3
                r = 20 + 90 * a
                sx, sy = cx + math.cos(ang) * r, cy + math.sin(ang) * r
                s = 7 * (1 - a) + 1
                d.ellipse([sx - s, sy - s, sx + s, sy + s], fill=(255, 230, 120, int(255 * (1 - a))))
            d.text((cx - 34, cy - 50 - 60 * a), "+10", font=font(BOLD, 40),
                   fill=(255, 240, 150, int(255 * (1 - a))), stroke_width=3,
                   stroke_fill=(40, 24, 10, int(255 * (1 - a))))
    # six slimes where day one had one red square
    tints = [(214, 62, 72), (88, 190, 110), (96, 150, 232), (210, 110, 220),
             (232, 150, 60), (80, 200, 200)]
    for p, tint in zip(PATROLS, tints):
        ex, ey = patrol_at(p, t)
        slime(d, ex, ey, t, tint)
    # the hero: dash trail, body, eyes that look where it goes
    px, py, face = player_at(t)
    for k in range(1, 7):
        qx, qy, _ = player_at(t - k * 0.035)
        s = 30 - k * 3.5
        d.ellipse([qx - s, qy - s, qx + s, qy + s], fill=(120, 220, 255, 110 - k * 16))
    step = math.sin(t * 16) * 4
    d.rounded_rectangle([px - 34, py - 36 + step, px + 34, py + 36 + step], 18,
                        fill=(90, 205, 250), outline=(18, 26, 48), width=5)
    d.rounded_rectangle([px - 34, py - 36 + step, px + 34, py - 14 + step], 12, fill=(250, 96, 150))
    for s in (-13, 13):
        ex, ey = px + s + face[0] * 7, py - 2 + step + face[1] * 7
        d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=(255, 255, 255))
        d.ellipse([ex - 4 + face[0] * 3, ey - 4 + face[1] * 3, ex + 4 + face[0] * 3,
                   ey + 4 + face[1] * 3], fill=(18, 26, 48))
    # darkness that follows the hero, then the HUD on top of it
    dark = Image.new("RGBA", (W, H), (6, 4, 16, 255))
    mask = SHADE.crop((int(W - px), int(H - py), int(W - px) + W, int(H - py) + H))
    im.paste(dark, (0, 0), mask)
    d = ImageDraw.Draw(im)
    score = score_at(t)
    d.rounded_rectangle([24, 44, 1056, 140], 22, fill=(14, 10, 28, 215), outline=(120, 108, 170), width=3)
    for k in range(3):
        hx = 52 + k * 58
        d.polygon([(hx, 80), (hx + 12, 68), (hx + 24, 80), (hx + 36, 68), (hx + 48, 80),
                   (hx + 24, 116)], fill=(240, 70, 100))
    d.text((250, 66), "SCORE %04d" % (score * 10), font=font(MONO, 46), fill=(255, 236, 150))
    d.text((622, 66), "CRYPT 1-1", font=font(MONO, 46), fill=(170, 220, 255))
    d.text((920, 66), "x%d" % max(1, score), font=font(MONO, 46), fill=(250, 96, 150))
    # minimap, tucked into the bottom wall rows so it never hides the hero
    mx, my, ms = 36, 1690, 13
    d.rounded_rectangle([mx - 10, my - 10, mx + COLS * ms + 10, my + ROWS * ms + 10], 10,
                        fill=(14, 10, 28, 200), outline=(120, 108, 170), width=2)
    for y, row in enumerate(MAP):
        for x, c in enumerate(row):
            if c in ".o":
                d.rectangle([mx + x * ms, my + y * ms, mx + x * ms + ms - 2, my + y * ms + ms - 2],
                            fill=(88, 80, 124))
    d.rectangle([mx + px / TILE * ms - 5, my + py / TILE * ms - 5, mx + px / TILE * ms + 5,
                 my + py / TILE * ms + 5], fill=(120, 230, 255))
    return im.convert("RGB")


# ------------------------------------------------------------ the edit --
# (build, game time at the cut's first frame, seconds on screen, headline)
CUTS = [
    (1, 0.0, 1.7, "My AI agent built this game"),
    (7, 0.0, 1.7, "Same map. Same start."),
    (1, 3.3, 1.2, ""),
    (7, 3.3, 1.2, ""),
    (1, 6.4, 1.2, ""),
    (7, 6.4, 1.2, "One week of daily updates"),
    # the close: the newer build simply being played, then the invitation
    (7, 7.6, 1.6, ""),
    (7, 9.2, 2.4, "Start yours at make.fun"),
]


def label(im, build, headline, age):
    d = ImageDraw.Draw(im, "RGBA")
    text = "DAY 1" if build == 1 else "DAY 7"
    colour = (236, 236, 236) if build == 1 else (255, 208, 60)
    f = font(BOLD, 104)
    tw = d.textlength(text, font=f)
    pop = 1.0 if age > 0.12 else 0.6 + age / 0.3
    box = [W / 2 - tw / 2 - 44, 196, W / 2 + tw / 2 + 44, 196 + 136 * pop]
    d.rounded_rectangle(box, 28, fill=(10, 8, 20, 235), outline=colour, width=6)
    d.text((W / 2 - tw / 2, 204), text, font=f, fill=colour)
    if headline:
        f2 = font(BOLD, 62)
        tw = d.textlength(headline, font=f2)
        d.rounded_rectangle([W / 2 - tw / 2 - 30, 1206, W / 2 + tw / 2 + 30, 1306], 24,
                            fill=(10, 8, 20, 225))
        d.text((W / 2 - tw / 2, 1218), headline, font=f2, fill=(255, 255, 255))


def frames():
    for build, t0, secs, headline in CUTS:
        for i in range(round(secs * FPS)):
            t = t0 + i / FPS
            im = draw_day1(t) if build == 1 else draw_day7(t)
            label(im, build, headline, i / FPS)
            yield im


# ------------------------------------------------------------- the sound --
RATE = 44100


def tone(freq, secs, shape, vol):
    out = []
    for i in range(int(secs * RATE)):
        ph = (i * freq / RATE) % 1.0
        v = (1.0 if ph < 0.5 else -1.0) if shape == "square" else 4 * abs(ph - 0.5) - 1
        env = min(1.0, i / 200) * max(0.0, 1 - i / (secs * RATE)) ** 1.5
        out.append(v * vol * env)
    return out


def soundtrack():
    total = sum(c[2] for c in CUTS)
    buf = [0.0] * int(total * RATE)

    def add(at, samples):
        s = int(at * RATE)
        for i, v in enumerate(samples):
            if s + i < len(buf):
                buf[s + i] += v

    at = 0.0
    for build, t0, secs, _ in CUTS:
        picks = [g - t0 for g in GOT.values() if t0 <= g < t0 + secs]
        if build == 1:  # day one: a lone beep per coin, silence between
            for p in picks:
                add(at + p, tone(440, 0.09, "square", 0.25))
        else:  # day seven: bass, arpeggio and a two-note chime per coin
            beat, n = 0.15, int(secs / 0.15)
            arp = [330, 392, 494, 587, 494, 392]
            for k in range(n):
                add(at + k * beat, tone(arp[k % 6], 0.13, "square", 0.10))
                if k % 4 == 0:
                    add(at + k * beat, tone(82 if (k // 4) % 2 == 0 else 110, 0.5, "tri", 0.30))
            for p in picks:
                add(at + p, tone(988, 0.07, "square", 0.22))
                add(at + p + 0.07, tone(1319, 0.16, "square", 0.22))
        at += secs
    return buf


def main():
    frames_path, audio_path = sys.argv[1], sys.argv[2]
    prepare()
    with open(frames_path, "wb") as f:
        for im in frames():
            f.write(im.tobytes())
    buf = soundtrack()
    with wave.open(audio_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 30000)) for v in buf))


if __name__ == "__main__":
    main()
