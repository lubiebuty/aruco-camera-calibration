#!/usr/bin/env python3
"""
Minimalny generator planszy ChArUco (A4, JPG, DPI) – tylko to, co potrzebne.
- Szachownica: 4×6 pól
- Rozmiar pola: 40 mm
- Marker: 80% pola (32 mm)
- Słownik: DICT_6X6_1000
- Plansza wyśrodkowana na A4, poniżej czarna linia 100 mm do weryfikacji skali

Drukuj w 100% (bez dopasowania). Po wydruku zmierz linię 100 mm.
Wymaga: opencv-contrib-python, pillow
"""

import os
import cv2
import numpy as np
from PIL import Image

MM_PER_INCH = 25.4

# Domyślne parametry (zmień wedle potrzeb)
SQUARES_X = 4
SQUARES_Y = 6
SQUARE_MM = 40.0
MARKER_FRAC = 0.8  # 80% pola -> marker 32 mm
DICT_NAME = 'DICT_6X6_1000'
DPI = 300
GAP_MM = 5.0       # odstęp między planszą a linią 100 mm

# Pasek skali
SCALE_MM = 100.0
SCALE_THICK_MM = 1.2
TICK_THICK_MM  = 0.8
TICK_LEN_MM    = 8.0
LABEL_OFFSET_MM = 2.5

# A4 pion (mm)
A4_W_MM, A4_H_MM = 210.0, 297.0


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm * dpi / MM_PER_INCH))


def generate_charuco_jpg(out_path: str = 'patterns/charuco_4x6_40mm.jpg') -> str:
    # Obraz A4 w pikselach (RGB, białe tło)
    width_px  = mm_to_px(A4_W_MM, DPI)
    height_px = mm_to_px(A4_H_MM, DPI)
    img = np.full((height_px, width_px, 3), 255, np.uint8)

    # Słownik ArUco
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(getattr(aruco, DICT_NAME))

    # Wymiary planszy w px
    square_px = mm_to_px(SQUARE_MM, DPI)
    marker_px = mm_to_px(SQUARE_MM * MARKER_FRAC, DPI)
    board_w_px = SQUARES_X * square_px
    board_h_px = SQUARES_Y * square_px

    # Pasek skali – w px
    scale_len_px = mm_to_px(SCALE_MM, DPI)
    scale_th_px  = max(1, mm_to_px(SCALE_THICK_MM, DPI))
    tick_th_px   = max(1, mm_to_px(TICK_THICK_MM,  DPI))
    tick_len_px  = mm_to_px(TICK_LEN_MM, DPI)
    gap_px       = mm_to_px(GAP_MM, DPI)
    label_off_px = mm_to_px(LABEL_OFFSET_MM, DPI)

    # Tekst „100 mm” – oblicz rozmiar przed centrowaniem pionowym
    label = '100 mm'
    font_scale = 0.8
    thickness = max(1, int(round(2 * DPI / 300)))
    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

    # Całkowita wysokość kompozycji (plansza + przerwa + pasek + pół długości kresek + odstęp + napis)
    below_bar_extra = (tick_len_px // 2) + label_off_px + text_size[1]
    content_h_px = board_h_px + gap_px + scale_th_px + below_bar_extra

    # Wyśrodkowanie kompozycji na A4
    x0 = (width_px  - board_w_px) // 2
    y0 = (height_px - content_h_px) // 2

    # Pozycje paska 100 mm
    scale_x0 = (width_px - scale_len_px) // 2
    scale_y  = y0 + board_h_px + gap_px  # górna krawędź paska

    # Rysuj planszę (czarne/białe pola) i markery w czarnych polach
    marker_id = 0
    for r in range(SQUARES_Y):
        for c in range(SQUARES_X):
            x = x0 + c * square_px
            y = y0 + r * square_px
            is_black = ((r + c) % 2 == 0)
            color = (0, 0, 0) if is_black else (255, 255, 255)
            cv2.rectangle(img, (x, y), (x + square_px, y + square_px), color, -1)
            if is_black:
                mx = x + (square_px - marker_px) // 2
                my = y + (square_px - marker_px) // 2
                # Generowanie markera (kompatybilnie z wersjami OpenCV)
                if hasattr(aruco, 'drawMarker'):
                    m = aruco.drawMarker(dictionary, marker_id, marker_px)
                else:
                    m = aruco.generateImageMarker(dictionary, marker_id, marker_px)
                img[my:my + marker_px, mx:mx + marker_px] = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
                marker_id += 1

    # Pasek 100 mm + kreski końcowe
    cv2.rectangle(img, (scale_x0, scale_y), (scale_x0 + scale_len_px, scale_y + scale_th_px), (0, 0, 0), -1)
    cv2.rectangle(img, (scale_x0, scale_y - tick_len_px // 2), (scale_x0 + tick_th_px, scale_y + tick_len_px // 2), (0, 0, 0), -1)
    cv2.rectangle(img, (scale_x0 + scale_len_px - tick_th_px, scale_y - tick_len_px // 2), (scale_x0 + scale_len_px, scale_y + tick_len_px // 2), (0, 0, 0), -1)

    # Podpis pod paskiem
    tx = (width_px - text_size[0]) // 2
    ty = scale_y + scale_th_px + label_off_px + text_size[1]
    cv2.putText(img, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness, lineType=cv2.LINE_AA)

    # Zapis JPG z DPI
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(img[..., ::-1]).save(out_path, format='JPEG', quality=95, dpi=(DPI, DPI))
    print(f'Zapisano: {out_path}')
    return out_path


if __name__ == '__main__':
    generate_charuco_jpg()