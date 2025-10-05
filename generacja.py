#!/usr/bin/env python3
"""
Generator ChArUco (A4, portret)
– squaresX x squaresY = 4 x 6 (liczba pól szachownicy)
– squareLength = 40 mm
– markerLength = 32 mm (80% pola)
– słownik: DICT_6X6_1000
– plansza wyśrodkowana, na dole czarna linia 100 mm do weryfikacji skali

Uwaga: wymagany OpenCV z modułem aruco:
    pip install opencv-contrib-python matplotlib
"""

from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import cv2

MM_PER_INCH = 25.4

# --- Strona A4 (portret) w mm oraz calach ---
A4_W_MM, A4_H_MM = 210.0, 297.0
A4_W_IN, A4_H_IN = A4_W_MM / MM_PER_INCH, A4_H_MM / MM_PER_INCH

# --- Parametry ChArUco ---
SQUARES_X = 4              # kolumny (liczba KWADRATÓW szachownicy)
SQUARES_Y = 6              # wiersze
SQUARE_MM = 40.0           # bok kwadratu (mm)
MARKER_MM = 32.0           # bok markera (mm) = 80% pola
DICT_NAME = 'DICT_6X6_1000'

# rozmiar całej tablicy w mm
BOARD_W_MM = SQUARES_X * SQUARE_MM
BOARD_H_MM = SQUARES_Y * SQUARE_MM

# wyśrodkowanie planszy na stronie
x0 = (A4_W_MM - BOARD_W_MM) / 2.0
y0 = (A4_H_MM - BOARD_H_MM) / 2.0

# --- Pasek skali 100 mm ---
SCALE_LEN_MM = 100.0
SCALE_BAR_THICK_MM = 1.2
SCALE_TICK_THICK_MM = 0.8
SCALE_TICK_LEN_MM = 8.0
SCALE_Y = 10.0  # 10 mm nad dolną krawędzią kartki

# --- Przygotowanie słownika i planszy ChArUco ---
aruco = cv2.aruco
dictionary = aruco.getPredefinedDictionary(getattr(aruco, DICT_NAME))

# Kompatybilność z różnymi wersjami OpenCV (4.5–4.10+)
if hasattr(aruco, 'CharucoBoard_create'):
    # starsze API
    board = aruco.CharucoBoard_create(
        squaresX=SQUARES_X,
        squaresY=SQUARES_Y,
        squareLength=SQUARE_MM,
        markerLength=MARKER_MM,
        dictionary=dictionary,
    )
else:
    # nowsze API (cv2.aruco.CharucoBoard.create)
    board = aruco.CharucoBoard.create(
        SQUARES_X,
        SQUARES_Y,
        SQUARE_MM,
        MARKER_MM,
        dictionary,
    )

# Narysuj planszę w wysokiej rozdzielczości (raster), a następnie umieść ją w pliku PDF
# z dokładnym pozycjonowaniem w milimetrach.
PX_PER_MM = 12  # ~304.8 DPI na obszarze planszy (bardzo ostre krawędzie)
board_w_px = int(round(BOARD_W_MM * PX_PER_MM))
board_h_px = int(round(BOARD_H_MM * PX_PER_MM))
# Rysowanie obrazu tablicy w zależności od API OpenCV
if hasattr(board, 'generateImage'):
    board_img = board.generateImage((board_w_px, board_h_px))
else:
    board_img = board.draw((board_w_px, board_h_px))

# --- Kompozycja PDF w układzie milimetrów ---
fig = plt.figure(figsize=(A4_W_IN, A4_H_IN))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_axis_off()
ax.set_xlim(0, A4_W_MM)
ax.set_ylim(0, A4_H_MM)

# tło
ax.add_patch(Rectangle((0, 0), A4_W_MM, A4_H_MM, facecolor='white', edgecolor='none'))

# umieść obraz planszy dokładnie w prostokącie [x0, x0+BOARD_W_MM] x [y0, y0+BOARD_H_MM]
extent = [x0, x0 + BOARD_W_MM, y0, y0 + BOARD_H_MM]
ax.imshow(board_img, cmap='gray', origin='lower', extent=extent, interpolation='nearest')

# cienka ramka dookoła planszy (ułatwia cięcie/pozycjonowanie)
ax.add_patch(Rectangle((x0, y0), BOARD_W_MM, BOARD_H_MM, fill=False, edgecolor='black', linewidth=0.4))

# pasek 100 mm u dołu (wyśrodkowany horyzontalnie)
scale_x0 = (A4_W_MM - SCALE_LEN_MM) / 2.0
ax.add_patch(Rectangle((scale_x0, SCALE_Y), SCALE_LEN_MM, SCALE_BAR_THICK_MM,
                       facecolor='black', edgecolor='black'))
# kreski końcowe
ax.add_patch(Rectangle((scale_x0, SCALE_Y - SCALE_TICK_LEN_MM/2),
                       SCALE_TICK_THICK_MM, SCALE_TICK_LEN_MM,
                       facecolor='black', edgecolor='black'))
ax.add_patch(Rectangle((scale_x0 + SCALE_LEN_MM - SCALE_TICK_THICK_MM,
                        SCALE_Y - SCALE_TICK_LEN_MM/2),
                       SCALE_TICK_THICK_MM, SCALE_TICK_LEN_MM,
                       facecolor='black', edgecolor='black'))
# podpis skali
ax.text(A4_W_MM/2.0, SCALE_Y + SCALE_BAR_THICK_MM + 2.5, '100 mm',
        ha='center', va='bottom', fontsize=7)

# (opcjonalnie) podpis techniczny poniżej planszy
spec = f"ChArUco {SQUARES_X}×{SQUARES_Y} | square={SQUARE_MM:.0f} mm | marker={MARKER_MM:.0f} mm | {DICT_NAME} | A4"
ax.text(A4_W_MM/2.0, y0 - 5.0, spec, ha='center', va='top', fontsize=7)

# --- Zapis ---
out_name = f"charuco_A4_{SQUARES_X}x{SQUARES_Y}_sq{int(SQUARE_MM)}mm_DICT6x6_1000.pdf"
fig.savefig(out_name, format='pdf')
plt.close(fig)
print('Zapisano:', out_name)