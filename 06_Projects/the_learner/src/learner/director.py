"""The Director + scene renderer.

The director maps journal events to scenes from a fixed cast of verified
event types only. It cannot change what was predicted, what the market did,
or what the trainer updated — it only chooses what the audience sees.

Two synchronized surfaces render the SAME journal records:
  vertical   1080x1920 (TikTok shape)
  landscape  1920x1080 (YouTube shape)
Neither computes its own results — every number on screen comes straight
from journal payloads.
"""

from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

BG = (10, 12, 18)
PANEL = (20, 26, 38)
INK = (235, 240, 248)
DIM = (140, 150, 168)
LONG_C = (76, 217, 123)
SHORT_C = (255, 92, 92)
WAIT_C = (255, 196, 66)
ACCENT = (96, 160, 255)
WARN = (255, 140, 60)
DISCLAIMER = ("SIMULATED — no real orders · educational experiment, "
              "not financial advice")

SCENES = {
    "next_round": "THE NEXT ROUND",
    "reveal": "THE REVEAL",
    "learning_moment": "THE LEARNING MOMENT",
    "rivalry": "THE RIVALRY",
    "referees_review": "THE REFEREE'S REVIEW",
    "science_room": "THE SCIENCE ROOM",
    "season_score": "THE SEASON SCORE",
    "data_break": "THE DATA BREAK",
    "cold_open": "DAY ZERO: THE AI ENTERS THE ARENA",
}


def pick_scene(rec: dict) -> Optional[str]:
    """Map one journal record to a scene kind. Returns None to skip."""
    k = rec.get("kind")
    p = rec.get("payload", {})
    if k == "prediction":
        if p["learner"]["action"] != p["anchor"]["action"]:
            return "rivalry"
        return "next_round"
    if k == "outcome":
        if p.get("referee_review"):
            return "referees_review"
        return "reveal"
    if k == "training_update":
        return "learning_moment" if p.get("accepted") else None
    if k == "feed_invalid":
        return "data_break"
    if k == "science_eval":
        return "science_room"
    if k == "season_score":
        return "season_score"
    return None


def _font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_MONO if mono else FONT_BOLD, size)


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _action_color(a: str):
    return {"LONG": LONG_C, "SHORT": SHORT_C}.get(a, WAIT_C)


def _lines_for(rec: dict, scene: str) -> list[tuple[str, tuple, int, bool]]:
    """(text, color, relative size, mono) content rows."""
    p = rec.get("payload", {})
    rows: list[tuple[str, tuple, int, bool]] = []
    if scene in ("next_round", "rivalry"):
        rows.append((f"BTC {p['entry_price']:.1f} USDT", INK, 3, False))
        l, a = p["learner"], p["anchor"]
        rows.append((f"LEARNER  {l['action']}  {l['confidence']*100:.0f}%",
                     _action_color(l["action"]), 4, True))
        rows.append((f"ANCHOR   {a['action']}  {a['confidence']*100:.0f}%",
                     _action_color(a["action"]), 4, True))
        import time as _t
        hhmm = _t.strftime("%H:%M UTC", _t.gmtime(p["minute_ts"]))
        rows.append((f"{hhmm} · horizon {p['horizon_min']}m",
                     DIM, 1, True))
    elif scene in ("reveal", "referees_review"):
        rows.append((f"{p['move_bps']:+.1f} bps → {p['truth']}", INK, 4, True))
        rows.append((
            f"LEARNER {p['learner_action']} {'✓ +1' if p['learner']['correct'] else '✗ −1'}",
            _action_color(p['learner_action']), 3, True))
        rows.append((
            f"ANCHOR  {p['anchor_action']} {'✓ +1' if p['anchor']['correct'] else '✗ −1'}",
            _action_color(p['anchor_action']), 3, True))
        if scene == "referees_review":
            rows.append((f"high-confidence miss (conf "
                         f"{p['learner_conf']*100:.0f}%)", WARN, 2, False))
        rows.append((f"score L {p['learner_score_total']:+d} · "
                     f"A {p['anchor_score_total']:+d}", DIM, 1, True))
    elif scene == "learning_moment":
        rows.append(("WEIGHT UPDATE ACCEPTED", LONG_C, 3, False))
        rows.append((f"evidence: {p['evidence_n']} matured records", INK, 2, False))
        rows.append((f"delta ‖Δ‖ {p['delta_norm_applied']:.4f} "
                     f"(cap {p.get('delta_norm_cap', 0.05)})", INK, 2, True))
        rows.append((f"hash {p['weights_hash_after'][:16]}…", DIM, 1, True))
        rows.append(("'model updated' ≠ 'model improved'", DIM, 1, False))
    elif scene == "data_break":
        rows.append(("FEED INVALID — PREDICTIONS PAUSED", WARN, 3, False))
        rows.append((f"reason: {p['reason']}", INK, 2, True))
        rows.append(("no interpolated prediction was emitted", DIM, 1, False))
    elif scene == "science_room":
        sa, ba = p.get("scientist_acc"), p.get("baseline_acc")
        rows.append((f"scientist features: "
                     f"{'n/a' if sa is None else f'{sa*100:.0f}%'}",
                     ACCENT, 3, True))
        rows.append((f"simple indicators: "
                     f"{'n/a' if ba is None else f'{ba*100:.0f}%'}",
                     DIM, 3, True))
        verdict = p.get("verdict", "insufficient evidence")
        rows.append((verdict, WARN if "beat" not in verdict else LONG_C, 2, False))
    elif scene == "season_score":
        l, a = p["learner"], p["anchor"]
        rows.append((f"LEARNER  {l['points']:+d} pts  "
                     f"({l['correct']}/{l['scored']} correct)", LONG_C, 3, True))
        rows.append((f"ANCHOR   {a['points']:+d} pts  "
                     f"({a['correct']}/{a['scored']} correct)", ACCENT, 3, True))
        rows.append((p.get("verdict", ""), INK, 2, False))
        rows.append((f"updates accepted: {p.get('updates_accepted', 0)}",
                     DIM, 1, True))
    elif scene == "cold_open":
        rows.append(("Two identical models. One learns. One is frozen.",
                     INK, 3, False))
        rows.append(("BTC_USDT perpetual · Gate public feed", DIM, 2, False))
        rows.append(("60 minute boundaries · journal-verified", DIM, 2, False))
        rows.append(("The Anchor makes 'improvement' falsifiable.",
                     ACCENT, 2, False))
    return rows


def render_frame(rec: dict, scene: str, narration: str,
                 orientation: str, seq: int, frame_idx: int,
                 out_dir: str) -> str:
    if orientation == "vertical":
        W, H, u = 1080, 1920, 1.0
    else:
        W, H, u = 1920, 1080, 1.0
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    s = min(W / 1080, H / 1080)          # uniform scale
    pad = int(48 * s)

    # header
    d.rectangle([0, 0, W, int(64 * s)], fill=PANEL)
    d.text((pad, int(14 * s)), "THE LEARNER · AI vs BITCOIN · DAY ZERO",
           font=_font(int(28 * s)), fill=INK)
    seq_txt = f"journal #{seq}"
    d.text((W - pad - d.textlength(seq_txt, font=_font(int(22 * s), True)),
            int(18 * s)), seq_txt, font=_font(int(22 * s), True), fill=DIM)

    # scene title
    title = SCENES.get(scene, scene)
    d.text((pad, int(96 * s)), title, font=_font(int(44 * s)), fill=ACCENT)
    d.line([pad, int(158 * s), W - pad, int(158 * s)], fill=PANEL,
           width=int(3 * s))

    # content rows
    y = int(200 * s)
    if orientation == "vertical":
        max_w = W - 2 * pad
    else:
        max_w = int(W * 0.62)
    for text, color, rel, mono in _lines_for(rec, scene):
        size = int((26 + rel * 14) * s)
        f = _font(size, mono)
        for ln in _wrap(d, text, f, max_w):
            d.text((pad, y), ln, font=f, fill=color)
            y += int(size * 1.35)
        y += int(14 * s)

    # right-side score panel (landscape) / footer block (vertical)
    p = rec.get("payload", {})
    side_x = int(W * 0.66)
    if orientation == "landscape" and scene != "cold_open":
        box = [side_x, int(200 * s), W - pad, int(560 * s)]
        d.rectangle(box, fill=PANEL, outline=(50, 60, 84), width=2)
        tx, ty = side_x + int(28 * s), int(220 * s)
        d.text((tx, ty), "SCOREBOARD", font=_font(int(26 * s)), fill=DIM)
        ty += int(48 * s)
        for line in p.get("scoreboard", []):
            f = _font(int(30 * s), True)
            d.text((tx, ty), line, font=f, fill=INK)
            ty += int(44 * s)

    # narration lower-third
    if narration:
        ny = H - int(240 * s)
        d.rectangle([0, ny, W, ny + int(140 * s)], fill=PANEL)
        f = _font(int(30 * s))
        yy = ny + int(24 * s)
        for ln in _wrap(d, narration, f, W - 2 * pad)[:3]:
            d.text((pad, yy), ln, font=f, fill=INK)
            yy += int(40 * s)

    # integrity strip
    d.rectangle([0, H - int(80 * s), W, H], fill=(6, 8, 12))
    stamp = f"{DISCLAIMER}  ·  rec hash {rec.get('hash', '')[:12]}"
    d.text((pad, H - int(56 * s)), stamp,
           font=_font(int(20 * s), True), fill=DIM)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{frame_idx:06d}.png")
    img.save(path)
    return path
