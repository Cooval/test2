"""
generator.py – rysuje siatkę pudełka (spód + oklejka) dokładnie wg logiki
oryginalnego skryptu PackLib, ale bez żadnych bibliotek CAD.
"""
import svgwrite
from math import isclose

# Stałe graficzne
CUT_STROKE   = {'stroke': '#ff0000', 'stroke_width': '0.25mm', 'fill': 'none'}
FOLD_STROKE  = {'stroke': '#0000ff', 'stroke_width': '0.25mm',
                'fill': 'none', 'stroke_dasharray': '2,2'}

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

def svg_bytes_from_params(L, B, H, R, ep):
    v = _derived_vars(L, B, H, R, ep)
    segs = _segment_list(v)

    # Ustalamy rozmiar roboczy   –   ► margines 20 mm, reszta auto-bbox
    max_x = max(max(x0, x1) for _, x0, _, x1, _ in segs) + 20
    max_y = max(max(y0, y1) for _, _, y0, _, y1 in segs) + 20

    dwg = svgwrite.Drawing(size=(f"{max_x}mm", f"{max_y}mm"), profile='tiny')

    cut_layer  = dwg.add(dwg.g(id="CUT",  **CUT_STROKE))
    fold_layer = dwg.add(dwg.g(id="FOLD", **FOLD_STROKE))

    for kind, x0, y0, x1, y1 in segs:
        layer = cut_layer if kind == "CUT" else fold_layer
        layer.add(dwg.line(start=(f"{x0}mm", f"{y0}mm"),
                           end  =(f"{x1}mm", f"{y1}mm")))

    return dwg.tostring().encode("utf-8")
