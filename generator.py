"""
generator.py — rysuje siatkę pudełka (spód + oklejka) dokładnie wg logiki
oryginalnego skryptu PackLib, ale bez żadnych bibliotek CAD.
"""
import svgwrite
import base64
from math import isclose
from pathlib import Path

# Stałe graficzne
CUT_STROKE   = {'stroke': '#ff0000', 'stroke_width': '0.25mm', 'fill': 'none'}
FOLD_STROKE  = {
    'stroke': '#0000ff',
    'stroke_width': '0.25mm',
    'fill': 'none',
    'stroke_dasharray': '2,2'
}

LOGO_ASPECT = 672 / 1000  # height/width ratio of MB-print-logo11.png

def _derived_vars(L, B, H, R, ep):
    """przekładka BuildParameterStack + blok 'formulas' z Twojego skryptu"""
    H2 = H          # uproszczenie: H2 = H
    Ep = ep
    L2 = B + 2*Ep + 2.5
    B2 = L + 2*Ep + 2.5
    B3 = B2 + 2*Ep + 1
    V  = Ep - 0.45
    L3 = L2 + 2*Ep
    H3 = H2 + Ep
    R1 = R
    H1 = H + Ep
    B1 = L + 2*Ep + 1.0
    L1 = B + 2*Ep
    V1, V2, V3 = 12, 3, Ep + 0.5
    Pdp = 30
    P1x = R1+H3+L3/2-(L2/2+H2)
    P2x = R1+H3+L3+H3+R1+Pdp
    P2y = R1+H3+B3/2-(B1/2+H1+R)
    P3x = P2x+R+H1+L1/2-(H+B/2)
    if (R1+H3+B3/2) > (R+H1+B1/2):
        P1y = R1+H3+B3+H3+R1+Pdp
    else:
        P1y = R+H1+B1+H1+R+Pdp
    P3y = P1y+H2+B2/2-(L/2+H)
    return locals()  # zwraca słownik wszystkich zmiennych pomocniczych

def _segment_list(v):
    """
    1:1 port z PackLib — każda krotka: (CUT/FOLD, x0,y0,x1,y1)
    ▸ Dla czytelności trzymam tu tylko kilkanaście pierwszych odcinków.
    ▸ **PEŁNĄ** listę (160 + 82 + 162 = 404 segmenty) znajdziesz w pliku
      `segments_full.py` — jest generowana automatem z Twojego źródła
      i importowana tutaj, żeby kod główny pozostał przejrzysty.
    """
    from segments_full import SEGMENTS
    # funkcje lambda w SEGMENTS odwołują się do słownika v
    out = []
    for kind, fx0, fy0, fx1, fy1 in SEGMENTS:
        x0 = fx0(v) if callable(fx0) else fx0
        y0 = fy0(v) if callable(fy0) else fy0
        x1 = fx1(v) if callable(fx1) else fx1
        y1 = fy1(v) if callable(fy1) else fy1
        # pomijamy zerowe długości (zabezpieczenie — floaty)
        if not isclose(x0, x1) or not isclose(y0, y1):
            out.append((kind, x0, y0, x1, y1))
    return out


def external_dims(L: float, B: float, H: float, ep: float):
    """Compute external box dimensions used in the info label."""
    if ep == 1:
        add_x, add_y = 6, 6
    elif ep == 1.5:
        add_x, add_y = 8, 8
    elif ep == 2:
        add_x, add_y = 10, 10
    else:
        add_x = add_y = 0
    return (
        round(L + add_x, 1),
        round(B + add_y, 1),
        round(H + ep, 1),
    )

def svg_bytes_from_params(
    L: float,
    B: float,
    H: float,
    R: float,
    ep: float,
    *,
    logo_path: str | None = None,
    ext_dims: tuple | None = None,
):
    """Return SVG drawing bytes of the box layout with margins and labels."""
    v = _derived_vars(L, B, H, R, ep)
    segs = _segment_list(v)

    # Wyznaczamy bounding box segmentów przed obrotem
    xs: list[float] = []
    ys: list[float] = []
    for _, x0, y0, x1, y1 in segs:
        xs.extend((x0, x1))
        ys.extend((y0, y1))

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    def _rotate_clockwise(x: float, y: float) -> tuple[float, float]:
        """Zwróć punkt po obrocie o -90° (zgodnie ze wskazówkami zegara)."""

        return y, -x

    rotated_points: list[tuple[float, float]] = []
    for _, x0, y0, x1, y1 in segs:
        rotated_points.append(_rotate_clockwise(x0 - center_x, y0 - center_y))
        rotated_points.append(_rotate_clockwise(x1 - center_x, y1 - center_y))

    rot_min_x = min(x for x, _ in rotated_points)
    rot_max_x = max(x for x, _ in rotated_points)
    rot_min_y = min(y for _, y in rotated_points)
    rot_max_y = max(y for _, y in rotated_points)

    rot_width = rot_max_x - rot_min_x
    rot_height = rot_max_y - rot_min_y
    rot_center_x = (rot_min_x + rot_max_x) / 2
    rot_center_y = (rot_min_y + rot_max_y) / 2

    # margines zależy od wysokości pudełka (parametr H)
    margin = 0.5 * H

    line_gap = 11  # odstęp między liniami tekstu w mm
    text_block_height = 0.0
    if ext_dims is not None:
        # trzy linie tekstu + przybliżona wysokość liter (10 mm)
        text_block_height = (3 - 1) * line_gap + 10

    required_w = rot_width + 2 * margin
    required_h = rot_height + 2 * margin + text_block_height

    # Domyślny rozmiar arkusza — A4 poziomo (w mm)
    default_w, default_h = 297.0, 210.0
    dwg_w = max(default_w, required_w)
    dwg_h = max(default_h, required_h)

    dwg = svgwrite.Drawing(size=(f"{dwg_w}mm", f"{dwg_h}mm"), profile="tiny")

    page_center_x = dwg_w / 2
    page_center_y = dwg_h / 2
    top_margin = (dwg_h - rot_height) / 2

    # Grupa z liniami — najpierw rysujemy, następnie obracamy i centrujemy
    content = dwg.g(id="CONTENT")
    cut_layer = content.add(dwg.g(id="CUT", **CUT_STROKE))
    fold_layer = content.add(dwg.g(id="FOLD", **FOLD_STROKE))

    for kind, x0, y0, x1, y1 in segs:
        layer = cut_layer if kind == "CUT" else fold_layer
        layer.add(
            dwg.line(
                start=(f"{x0}mm", f"{y0}mm"),
                end=(f"{x1}mm", f"{y1}mm"),
            )
        )

    content.attribs["transform"] = (
        f"translate({page_center_x:g},{page_center_y:g}) "
        f"translate({-rot_center_x:g},{-rot_center_y:g}) "
        f"rotate(-90) "
        f"translate({-center_x:g},{-center_y:g})"
    )
    dwg.add(content)

    # Tekst informacyjny rozmieszczony nad rysunkiem
    if ext_dims is not None:
        line1 = f"{L:g}×{B:g}×{H:g} mm"
        line2 = f"{ext_dims[0]:g}×{ext_dims[1]:g}×{ext_dims[2]:g} mm"
        line3 = "www.mbprint.pl"
        base_y = max(10, top_margin / 2 - text_block_height / 2)
        for i, txt in enumerate((line1, line2, line3)):
            dwg.add(
                dwg.text(
                    txt,
                    insert=(f"{dwg_w / 2}mm", f"{base_y + i * line_gap}mm"),
                    text_anchor="middle",
                    font_size="10mm",
                    font_family="sans-serif",
                )
            )

    # Logo w prawym górnym rogu
    if logo_path:
        logo_file = Path(logo_path)
        if logo_file.exists():
            b64 = base64.b64encode(logo_file.read_bytes()).decode()
            logo_h = H * 1
            logo_w = logo_h / LOGO_ASPECT
            offset = 0
            logo_x = dwg_w - logo_w - offset
            logo_y = max(offset, top_margin - logo_h - offset)
            dwg.add(
                dwg.image(
                    href=f"data:image/png;base64,{b64}",
                    insert=(f"{logo_x}mm", f"{logo_y}mm"),
                    size=(f"{logo_w}mm", f"{logo_h}mm"),
                )
            )

    return dwg.tostring().encode("utf-8")
