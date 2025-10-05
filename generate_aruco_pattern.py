#!/usr/bin/env python3
"""
Generator planszy ChArUco zgodny z tutorialem (OpenCV 4.x, Python).
- Tworzy obiekt cv2.aruco.CharucoBoard i renderuje planszę metodą generateImage/draw.
- Osadza planszę na A4 (JPG, DPI), dodaje pasek skali 100 mm i podpis.
- Domyślna plansza: 4×6 pól, pole 40 mm, marker 32 mm (80%), DICT_6X6_1000.

Wskazówki:
- Drukuj w 100% (bez dopasowania). Po wydruku zmierz pasek 100 mm.
- Jeśli chcesz ścisłej zgodności z układem „legacy” (np. z tutoriali 3.x) przy parzystych wymiarach,
  pozostaw LEGACY_PATTERN = True (zalecane).
Wymaga: opencv-contrib-python, pillow
"""

import os
import cv2
import numpy as np
from PIL import Image

MM_PER_INCH = 25.4

# --- Parametry planszy ChArUco ---
SQUARES_X = 4           # liczba pól w poziomie (kolumny)
SQUARES_Y = 6           # liczba pól w pionie (wiersze)
SQUARE_MM = 40.0        # rozmiar jednego pola (mm)
MARKER_FRAC = 0.8       # marker = 80% pola -> 32 mm
DICT_NAME = 'DICT_6X6_1000'
LEGACY_PATTERN = True   # zalecane przy parzystych wymiarach/zgodność z 3.x

# --- Strona i kompozycja ---
DPI = 300
A4_W_MM, A4_H_MM = 210.0, 297.0  # pion
GAP_MM = 5.0                     # odstęp między planszą a paskiem skali

# --- Pasek skali 100 mm ---
SCALE_MM = 100.0
SCALE_THICK_MM = 1.2
TICK_THICK_MM  = 0.8
TICK_LEN_MM    = 8.0
LABEL_OFFSET_MM = 2.5

def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm * dpi / MM_PER_INCH))

def get_aruco_dictionary(name: str):
    aruco = cv2.aruco
    if hasattr(aruco, 'getPredefinedDictionary'):
        return aruco.getPredefinedDictionary(getattr(aruco, name))
    # starsze API
    return aruco.Dictionary_get(getattr(aruco, name))

def create_charuco_board(sx: int, sy: int, square_mm: float, marker_mm: float, dictionary):
    """Tworzy obiekt CharucoBoard – kompatybilnie z różnymi wersjami OpenCV."""
    aruco = cv2.aruco
    # Długości w jednostkach "świata" – tu po prostu w milimetrach (zgodne z mm).
    square_len = float(square_mm)
    marker_len = float(marker_mm)
    board = None
    # Preferowany nowy konstruktor (4.x)
    try:
        board = aruco.CharucoBoard((sx, sy), square_len, marker_len, dictionary)
    except Exception:
        pass
    # Fallback na starsze API (czasem obecne również w 4.x buildach)
    if board is None and hasattr(aruco, 'CharucoBoard_create'):
        board = aruco.CharucoBoard_create(sx, sy, square_len, marker_len, dictionary)
    if board is None:
        raise RuntimeError("Nie udało się utworzyć CharucoBoard – sprawdź instalację opencv-contrib-python.")

    # Opcjonalny układ legacy (zalecane dla zgodności z tutorialem 3.x / parzyste wymiary)
    if LEGACY_PATTERN and hasattr(board, 'setLegacyPattern'):
        try:
            board.setLegacyPattern(True)
        except Exception:
            pass
    return board

def render_board_image(board, size_px: tuple[int, int]) -> np.ndarray:
    """Renderuje sam obraz planszy ChArUco jako GRAY."""
    w, h = size_px
    # Preferowane: generateImage (4.x)
    if hasattr(board, 'generateImage'):
        # marginSize=0 (bez marginesu), borderBits=1 (obramowanie markerów)
        return board.generateImage((w, h), marginSize=0, borderBits=1)
    # Fallback: draw (starsze API)
    if hasattr(board, 'draw'):
        img = np.zeros((h, w), dtype=np.uint8)
        board.draw((w, h), img, marginSize=0, borderBits=1)
        return img
    raise RuntimeError("Brak metod renderowania (generateImage/draw) dla CharucoBoard.")

def generate_charuco_jpg(out_path: str = 'patterns/charuco_4x6_40mm.jpg') -> str:
    # --- Płótno A4 (RGB, białe) ---
    page_w_px  = mm_to_px(A4_W_MM, DPI)
    page_h_px  = mm_to_px(A4_H_MM, DPI)
    page = np.full((page_h_px, page_w_px, 3), 255, np.uint8)

    # --- Słownik i board ---
    aruco = cv2.aruco
    dictionary = get_aruco_dictionary(DICT_NAME)
    marker_mm = SQUARE_MM * MARKER_FRAC
    board_w_mm = SQUARES_X * SQUARE_MM
    board_h_mm = SQUARES_Y * SQUARE_MM
    board_w_px = mm_to_px(board_w_mm, DPI)
    board_h_px = mm_to_px(board_h_mm, DPI)

    board = create_charuco_board(SQUARES_X, SQUARES_Y, SQUARE_MM, marker_mm, dictionary)
    board_gray = render_board_image(board, (board_w_px, board_h_px))
    board_bgr = cv2.cvtColor(board_gray, cv2.COLOR_GRAY2BGR)

    # --- Pasek skali (w px) ---
    scale_len_px = mm_to_px(SCALE_MM, DPI)
    scale_th_px  = max(1, mm_to_px(SCALE_THICK_MM, DPI))
    tick_th_px   = max(1, mm_to_px(TICK_THICK_MM,  DPI))
    tick_len_px  = mm_to_px(TICK_LEN_MM, DPI)
    gap_px       = mm_to_px(GAP_MM, DPI)
    label_off_px = mm_to_px(LABEL_OFFSET_MM, DPI)

    # Tekst pod paskiem
    label = '100 mm'
    font_scale = 0.8
    thickness = max(1, int(round(2 * DPI / 300)))
    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

    # Całkowita wysokość: plansza + przerwa + pasek + pół długości kresek + odstęp + napis
    below_bar_extra = (tick_len_px // 2) + label_off_px + text_size[1]
    content_h_px = board_h_px + gap_px + scale_th_px + below_bar_extra

    # --- Pozycjonowanie na stronie ---
    x0 = (page_w_px  - board_w_px) // 2
    y0 = (page_h_px  - content_h_px) // 2

    # Wklej planszę
    page[y0:y0 + board_h_px, x0:x0 + board_w_px] = board_bgr

    # Pasek skali (centrowany pod planszą)
    scale_x0 = (page_w_px - scale_len_px) // 2
    scale_y  = y0 + board_h_px + gap_px
    cv2.rectangle(page, (scale_x0, scale_y), (scale_x0 + scale_len_px, scale_y + scale_th_px), (0, 0, 0), -1)
    # kreski końcowe
    cv2.rectangle(page, (scale_x0, scale_y - tick_len_px // 2),
                  (scale_x0 + tick_th_px, scale_y + tick_len_px // 2), (0, 0, 0), -1)
    cv2.rectangle(page, (scale_x0 + scale_len_px - tick_th_px, scale_y - tick_len_px // 2),
                  (scale_x0 + scale_len_px, scale_y + tick_len_px // 2), (0, 0, 0), -1)

    # Podpis "100 mm"
    tx = (page_w_px - text_size[0]) // 2
    ty = scale_y + scale_th_px + label_off_px + text_size[1]
    cv2.putText(page, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness, lineType=cv2.LINE_AA)

    # Zapis JPG z DPI
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(page[..., ::-1]).save(out_path, format='JPEG', quality=95, dpi=(DPI, DPI))
    print(f'Zapisano: {out_path}')
    return out_path

if __name__ == '__main__':
    generate_charuco_jpg()
