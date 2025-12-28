import argparse
import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader

# --- SŁOWNIK TŁUMACZEŃ ---
TRANSLATIONS = {
    'PL': {
        'red_label': "Obszar czerwony (30%)",
        'red_desc': "Spad - zostanie odcięty.",
        'blue_label': "Obszar zakreskowany",
        'blue_desc': "Margines techniczny - brak ważnych grafik.",
        'green_label': "Obszar pusty",
        'green_desc': "Obszar bezpieczny - miejsce na Twój projekt.",
        'card_header': "WYMIAR KARTY (NETTO)",
        'file_header': "WYMIAR PLIKU (BRUTTO)",
    },
    'EN': {
        'red_label': "Red Area (30%)",
        'red_desc': "Bleed - will be trimmed off.",
        'blue_label': "Hatched Area",
        'blue_desc': "Unsafe area - keep text away.",
        'green_label': "Empty Area",
        'green_desc': "Safe area - place design here.",
        'card_header': "CARD SIZE (CUT)",
        'file_header': "FILE SIZE (BLEED)",
    }
}

def register_polish_font():
    font_name = "Helvetica" 
    try:
        font_paths = ["C:\\Windows\\Fonts\\arial.ttf", "arial.ttf", "/usr/share/fonts/truetype/arial.ttf"]
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('Arial', path))
                return 'Arial'
    except:
        pass
    return font_name

def find_logo_file():
    candidates = ["templates/MB-print-logo11.png", "logo.jpg", "logo.jpeg", "logo.png", "logo.bmp"]
    for filename in candidates:
        if os.path.exists(filename):
            return filename
    return None

def add_round_rect_reverse(path, x, y, w, h, r):
    path.moveTo(x, y + h - r)
    path.lineTo(x, y + r)
    path.curveTo(x, y + r * 0.45, x + r * 0.45, y, x + r, y)
    path.lineTo(x + w - r, y)
    path.curveTo(x + w - r * 0.45, y, x + w, y + r * 0.45, x + w, y + r)
    path.lineTo(x + w, y + h - r)
    path.curveTo(x + w, y + h - r * 0.45, x + w - r * 0.45, y + h, x + w - r, y + h)
    path.lineTo(x + r, y + h)
    path.curveTo(x + r * 0.45, y + h, x, y + h - r * 0.45, x, y + h - r)
    path.close()

def draw_hatching(c, x, y, w, h, step_mm=2):
    step = step_mm * mm
    c.setStrokeColor(HexColor('#0000FF'))
    c.setLineWidth(0.3)
    c.setStrokeAlpha(0.4)
    max_dim = w + h
    for i in range(0, int(max_dim), int(step)):
        c.line(x + i - h, y, x + i, y + h)

def create_template(width_mm, height_mm, lang):
    lang = lang.upper()
    if lang not in TRANSLATIONS: lang = 'EN'
    txt = TRANSLATIONS[lang]
    font_name = register_polish_font()
    
    filename = f"template_{width_mm}x{height_mm}mm_{lang}.pdf"
    
    # GEOMETRIA
    BLEED = 3 * mm
    CUT_W = width_mm * mm
    CUT_H = height_mm * mm
    PAGE_W = CUT_W + (2 * BLEED)
    PAGE_H = CUT_H + (2 * BLEED)
    
    SAFE_MARGIN = 4 * mm
    SAFE_W = CUT_W - (2 * SAFE_MARGIN)
    SAFE_H = CUT_H - (2 * SAFE_MARGIN)
    SAFE_X = BLEED + SAFE_MARGIN
    SAFE_Y = BLEED + SAFE_MARGIN
    CORNER_RADIUS = 5 * mm

    c = canvas.Canvas(filename, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"Szablon {width_mm}x{height_mm} {lang}")

    # --- 1. WARSTWY TŁA ---
    # Czerwony Spad
    c.saveState()
    p_bleed = c.beginPath()
    p_bleed.rect(0, 0, PAGE_W, PAGE_H)
    add_round_rect_reverse(p_bleed, BLEED, BLEED, CUT_W, CUT_H, CORNER_RADIUS)
    c.clipPath(p_bleed, stroke=0, fill=0)
    c.setFillColor(HexColor('#FF0000'))
    c.setFillAlpha(0.3) 
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.restoreState()

    # Kreskowanie
    c.saveState()
    p_unsafe = c.beginPath()
    p_unsafe.roundRect(BLEED, BLEED, CUT_W, CUT_H, CORNER_RADIUS)
    add_round_rect_reverse(p_unsafe, SAFE_X, SAFE_Y, SAFE_W, SAFE_H, CORNER_RADIUS)
    c.clipPath(p_unsafe, stroke=0, fill=0)
    draw_hatching(c, 0, 0, PAGE_W, PAGE_H, step_mm=2)
    c.restoreState()

    # Linia cięcia
    c.setStrokeColor(HexColor('#000000'))
    c.setLineWidth(0.8)
    c.setStrokeAlpha(1.0)
    c.setFillColor(Color(0,0,0, alpha=0))
    c.roundRect(BLEED, BLEED, CUT_W, CUT_H, CORNER_RADIUS, fill=0, stroke=1)

    # --- 2. LOGO - PRZYGOTOWANIE ---
    logo_file = find_logo_file()
    logo_height_final = 0
    target_w = 0
    target_h = 0
    logo_obj = None # Obiekt ImageReader
    
    logo_scale_factor = 1.0
    if width_mm < 60:
        logo_scale_factor = width_mm / 60.0

    if logo_file:
        try:
            # KLUCZOWE: Wczytanie obrazu do obiektu przed rysowaniem
            logo_obj = ImageReader(logo_file)
            iw, ih = logo_obj.getSize()
            aspect = ih / float(iw)
            target_w = min(30 * mm, SAFE_W * 0.5) * logo_scale_factor
            target_h = target_w * aspect
            logo_height_final = target_h
            print(f"ZNALAZŁEM: {logo_file} ({iw}x{ih})")
        except Exception as e:
            print(f"BŁĄD PLIKU: {e}")
    else:
        # Placeholder dla braku pliku
        target_w = 30 * mm * logo_scale_factor
        target_h = 10 * mm * logo_scale_factor
        logo_height_final = target_h

    # --- 3. TEKSTY ---
    base_desc_size = 7
    base_header_size = 8
    base_data_size = 8
    
    # Scaling based on card dimensions (both width and height)
    min_dim = min(width_mm, height_mm)
    if min_dim < 100:
        scale = min_dim / 100.0
        # More aggressive scaling for very small cards
        if min_dim < 60:
            base_desc_size = max(3.5, base_desc_size * scale * 0.8)
            base_header_size = max(4, base_header_size * scale * 0.8)
            base_data_size = max(4, base_data_size * scale * 0.8)
        else:
            base_desc_size = max(4.5, base_desc_size * scale)
            base_header_size = max(5, base_header_size * scale)
            base_data_size = max(5, base_data_size * scale)

    styles = getSampleStyleSheet()
    style_desc = ParagraphStyle('Desc', parent=styles['Normal'], fontName=font_name, 
                                fontSize=base_desc_size, leading=base_desc_size+2, 
                                alignment=TA_CENTER, textColor=HexColor('#000000'))
    style_header = ParagraphStyle('Header', parent=styles['Normal'], fontName=font_name, 
                                  fontSize=base_header_size, leading=base_header_size+2, 
                                  alignment=TA_CENTER, spaceBefore=3, textColor=HexColor('#000000'))
    style_data = ParagraphStyle('Data', parent=styles['Normal'], fontName=font_name, 
                                fontSize=base_data_size, leading=base_data_size+2, 
                                alignment=TA_CENTER, textColor=HexColor('#000000'))

    story = []
    story.append(Spacer(1, logo_height_final + 2*mm))

    legend_html = f"""
    <b>{txt['red_label']}:</b> {txt['red_desc']}<br/>
    <b>{txt['blue_label']}:</b> {txt['blue_desc']}<br/>
    <b>{txt['green_label']}:</b> {txt['green_desc']}
    """
    story.append(Paragraph(legend_html, style_desc))
    story.append(Spacer(1, 3*mm))

    w_inch = width_mm / 25.4
    h_inch = height_mm / 25.4
    px_cut_w = int(w_inch * 300)
    px_cut_h = int(h_inch * 300)
    page_w_mm = PAGE_W / mm
    page_h_mm = PAGE_H / mm
    page_inch_w = page_w_mm / 25.4
    page_inch_h = page_h_mm / 25.4
    px_page_w = int(page_inch_w * 300)
    px_page_h = int(page_inch_h * 300)

    story.append(Paragraph(f"<b>{txt['card_header']}</b>", style_header))
    story.append(Paragraph(f"{width_mm}x{height_mm} mm | {w_inch:.2f}\"x{h_inch:.2f}\"", style_data))
    story.append(Paragraph(f"300 DPI: {px_cut_w}x{px_cut_h} px", style_data))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"<b>{txt['file_header']}</b>", style_header))
    story.append(Paragraph(f"{page_w_mm:.1f}x{page_h_mm:.1f} mm | {page_inch_w:.2f}\"x{page_inch_h:.2f}\"", style_data))
    story.append(Paragraph(f"300 DPI: {px_page_w}x{px_page_h} px", style_data))

    frame = Frame(SAFE_X + 1*mm, SAFE_Y + 1*mm, 
                  SAFE_W - 2*mm, SAFE_H - 2*mm, 
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
    frame.addFromList(story, c)

    # --- 4. RYSOWANIE LOGO (CRITICAL FIX) ---
    
    # Resetowanie wszelkich stanów graficznych Canvas przed rysowaniem obrazu
    c.setStrokeAlpha(1.0)
    c.setFillAlpha(1.0)
    c.setFillColor(HexColor('#000000'))
    
    pos_x = SAFE_X + (SAFE_W - target_w) / 2
    pos_y = SAFE_Y + SAFE_H - target_h
    
    if logo_obj:
        # Rysujemy obiekt ImageReader, nie nazwę pliku
        # Maska ustawiona na None, preserveAspectRatio włączone
        c.drawImage(logo_obj, pos_x, pos_y, width=target_w, height=target_h, 
                    mask=None, preserveAspectRatio=True)
    else:
        # Ramka błędu
        c.setStrokeColor(HexColor('#FF0000'))
        c.setLineWidth(1)
        c.rect(pos_x, pos_y, target_w, target_h)
        c.line(pos_x, pos_y, pos_x + target_w, pos_y + target_h)
        c.line(pos_x, pos_y + target_h, pos_x + target_w, pos_y)

    c.save()
    print(f"GOTOWE: {filename}")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generator makiety v10 (Alpha Reset)")
    parser.add_argument("width", type=float, help="Szerokość (mm)")
    parser.add_argument("height", type=float, help="Wysokość (mm)")
    parser.add_argument("lang", type=str, choices=['PL', 'EN', 'pl', 'en'], help="Język (PL lub EN)")
    
    args = parser.parse_args()
    create_template(args.width, args.height, args.lang)
