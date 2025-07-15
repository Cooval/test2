"""
generator.py – rysuje siatkę pudełka (spód + oklejka) dokładnie wg logiki
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
    1:1 port z PackLib – każda krotka: (CUT/FOLD, x0,y0,x1,y1)
    ▸ Dla czytelności trzymam tu tylko kilkanaście pierwszych odcinków.
    ▸ **PEŁNĄ** listę (160 + 82 + 162 = 404 segmenty) znajdziesz w pliku
      `segments_full.py` – jest generowana automatem z Twojego źródła
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
        # pomijamy zerowe długości (zabezpieczenie – float’y)
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

    # Determine bounding box of generated segments
    min_x = min(min(x0, x1) for _, x0, _, x1, _ in segs)
    min_y = min(min(y0, y1) for _, _, y0, _, y1 in segs)
    max_x = max(max(x0, x1) for _, x0, _, x1, _ in segs)
    max_y = max(max(y0, y1) for _, _, y0, _, y1 in segs)

    width = max_x - min_x
    height = max_y - min_y
    # margin depends on Z dimension (H parameter)
    margin = 0.5 * H

    dwg_w = width + 2 * margin
    dwg_h = height + 2 * margin

    dwg = svgwrite.Drawing(size=(f"{dwg_w}mm", f"{dwg_h}mm"), profile="tiny")

    # group with translation to keep margin and center
    content = dwg.g(transform=f"translate({margin - min_x},{margin - min_y})")
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

    # Rotate entire sheet with lines 90 degrees counter-clockwise
    rotated = dwg.g(transform=f"rotate(-90,{dwg_w/2},{dwg_h/2})")
    rotated.add(content)
    dwg.add(rotated)

    # Informational text on top margin split into three lines
    if ext_dims is not None:
        line1 = f"{L:g}×{B:g}×{H:g} mm"
        line2 = f"{ext_dims[0]:g}×{ext_dims[1]:g}×{ext_dims[2]:g} mm"
        line3 = "www.mbprint.pl"
        base_y = margin / 3
        line_gap = 11  # vertical spacing between lines in mm
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

    # Position logo in the upper right corner if provided
    if logo_path:
        logo_file = Path(logo_path)
        if logo_file.exists():
            b64 = base64.b64encode(logo_file.read_bytes()).decode()
            # Scale logo to height Z*1.5 while keeping aspect ratio
            logo_h = H * 1
            logo_w = logo_h / LOGO_ASPECT
            # offset from page edges (in mm)
            offset = 0
            logo_x = dwg_w - logo_w - offset
            logo_y = offset
            dwg.add(
                dwg.image(
                    href=f"data:image/png;base64,{b64}",
                    insert=(f"{logo_x}mm", f"{logo_y}mm"),
                    size=(f"{logo_w}mm", f"{logo_h}mm"),
                )
            )

    return dwg.tostring().encode("utf-8")
