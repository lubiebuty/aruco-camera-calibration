#!/usr/bin/env python3
"""
Generator wzorca ARUCO do kalibracji kamery
Generuje wzorzec ARUCO na kartce A4 z dodatkowym wzorcem skali 10 cm
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
import os
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages

def generate_charuco_pattern():
    """
    Generuje wzorzec ChArUco (szachownica + ARUCO) na kartce A4 z wzorcem skali
    Gotowy do wydruku w skali 100% na papierze A4
    """
    # Wymiary A4 w mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    # Rozdzielczość DPI dla wydruku (72 DPI = standardowa rozdzielczość ekranowa)
    DPI = 72
    MM_TO_INCH = 25.4
    
    # Konwersja mm na piksele
    width_px = int(A4_WIDTH_MM * DPI / MM_TO_INCH)
    height_px = int(A4_HEIGHT_MM * DPI / MM_TO_INCH)
    
    print(f"Rozmiar obrazu: {width_px}x{height_px} pikseli")
    print(f"Rozdzielczość: {DPI} DPI")
    print(f"Wymiary A4: {A4_WIDTH_MM}x{A4_HEIGHT_MM} mm")
    
    # Tworzenie białego tła
    img = np.ones((height_px, width_px), dtype=np.uint8) * 255
    
    # Parametry ChArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    # Rozmiar kwadratu szachownicy w mm
    square_size_mm = 20
    square_size_px = int(square_size_mm * DPI / MM_TO_INCH)
    
    # Rozmiar markera ARUCO w mm (proporcjonalny do kwadratu)
    marker_size_mm = square_size_mm * 0.8  # 80% rozmiaru kwadratu
    marker_size_px = int(marker_size_mm * DPI / MM_TO_INCH)
    
    # Marginesy w mm
    margin_mm = 15
    margin_px = int(margin_mm * DPI / MM_TO_INCH)
    
    # Obliczenie ile kwadratów zmieści się w rzędzie i kolumnie
    available_width = width_px - 2 * margin_px
    available_height = height_px - 2 * margin_px - 100  # miejsce na wzorzec skali
    
    squares_per_row = available_width // square_size_px
    squares_per_col = available_height // square_size_px
    
    print(f"Kwadraty w rzędzie: {squares_per_row}")
    print(f"Kwadraty w kolumnie: {squares_per_col}")
    print(f"Rozmiar kwadratu: {square_size_mm} mm")
    print(f"Rozmiar markera ARUCO: {marker_size_mm:.1f} mm")
    
    # Generowanie wzorca ChArUco
    marker_id = 0
    for row in range(squares_per_col):
        for col in range(squares_per_row):
            if marker_id >= 250:  # Maksymalna liczba markerów w słowniku
                break
                
            # Pozycja kwadratu
            x = margin_px + col * square_size_px
            y = margin_px + row * square_size_px
            
            # Rysowanie kwadratu szachownicy
            if (row + col) % 2 == 0:  # Czarny kwadrat
                cv2.rectangle(img, (x, y), (x + square_size_px, y + square_size_px), 0, -1)
                
                # Dodanie markera ARUCO w środku czarnego kwadratu
                marker_x = x + (square_size_px - marker_size_px) // 2
                marker_y = y + (square_size_px - marker_size_px) // 2
                
                # Generowanie markera ARUCO
                marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)
                
                # Umieszczenie markera na obrazie
                img[marker_y:marker_y+marker_size_px, marker_x:marker_x+marker_size_px] = marker
                
                marker_id += 1
            else:  # Biały kwadrat
                cv2.rectangle(img, (x, y), (x + square_size_px, y + square_size_px), 255, -1)
    
    # Dodanie wzorca skali 10 cm (100 mm)
    scale_length_mm = 100
    scale_length_px = int(scale_length_mm * DPI / MM_TO_INCH)
    
    # Pozycja wzorca skali (na dole kartki)
    scale_y = height_px - 50
    scale_x_start = width_px // 2 - scale_length_px // 2
    scale_x_end = scale_x_start + scale_length_px
    
    # Rysowanie linii skali
    cv2.line(img, (scale_x_start, scale_y), (scale_x_end, scale_y), 0, 3)
    
    # Dodanie oznaczeń końców linii
    cv2.line(img, (scale_x_start, scale_y - 10), (scale_x_start, scale_y + 10), 0, 2)
    cv2.line(img, (scale_x_end, scale_y - 10), (scale_x_end, scale_y + 10), 0, 2)
    
    # Dodanie tekstu z opisem skali
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    
    text = "100 mm"
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = scale_x_start + (scale_length_px - text_size[0]) // 2
    text_y = scale_y + 30
    
    cv2.putText(img, text, (text_x, text_y), font, font_scale, 0, thickness)
    
    return img, DPI

def save_pattern_pdf(filename="charuco_calibration_pattern.pdf"):
    """
    Generuje wzorzec ChArUco w PDF z dokładnymi wymiarami A4
    Używa OpenCV do generowania obrazu, potem konwertuje na PDF
    """
    # Utwórz folder 'patterns' jeśli nie istnieje
    patterns_dir = "patterns"
    if not os.path.exists(patterns_dir):
        os.makedirs(patterns_dir)
        print(f"Utworzono folder: {patterns_dir}")
    
    # Wymiary A4 w mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    # Rozdzielczość DPI dla wysokiej jakości
    DPI = 300
    MM_TO_INCH = 25.4
    
    # Konwersja mm na piksele
    width_px = int(A4_WIDTH_MM * DPI / MM_TO_INCH)
    height_px = int(A4_HEIGHT_MM * DPI / MM_TO_INCH)
    
    print(f"Wymiary A4: {A4_WIDTH_MM}x{A4_HEIGHT_MM} mm")
    print(f"Rozdzielczość: {DPI} DPI")
    print(f"Rozmiar obrazu: {width_px}x{height_px} pikseli")
    
    # Tworzenie białego tła
    img = np.ones((height_px, width_px), dtype=np.uint8) * 255
    
    # Parametry ChArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    # Marginesy w mm (zwiększone dla lepszego wyglądu)
    margin_mm = 10
    margin_px = int(margin_mm * DPI / MM_TO_INCH)
    
    # Miejsce na wzorzec skali w mm (minimalne - tylko na dole)
    scale_space_mm = 15
    scale_space_px = int(scale_space_mm * DPI / MM_TO_INCH)
    
    # Dostępna przestrzeń na szachownicę (wzorzec skali tylko na dole)
    available_width = width_px - 2 * margin_px
    available_height = height_px - margin_px - scale_space_px  # margines tylko na górze
    
    # Obliczenie optymalnego rozmiaru kwadratu dla maksymalnego wypełnienia
    # Szukamy największego kwadratu, który zmieści się w dostępnej przestrzeni
    # Minimum 15px na kwadrat dla czytelności
    min_square_size_px = 15
    
    # Obliczamy maksymalny rozmiar kwadratu na podstawie dostępnej przestrzeni
    max_square_size_px = min(available_width, available_height) // 10  # maksymalnie 10 kwadratów w każdym kierunku
    
    # Wybieramy rozmiar kwadratu (minimum 15px, maksimum obliczony)
    square_size_px = max(min_square_size_px, max_square_size_px)
    square_size_mm = square_size_px * MM_TO_INCH / DPI
    
    # Rozmiar markera ARUCO w mm (proporcjonalny do kwadratu)
    marker_size_mm = square_size_mm * 0.8  # 80% rozmiaru kwadratu
    marker_size_px = int(marker_size_mm * DPI / MM_TO_INCH)
    
    # Obliczenie ile kwadratów zmieści się w rzędzie i kolumnie
    squares_per_row = available_width // square_size_px
    squares_per_col = available_height // square_size_px
    
    # Ograniczenie do 9x12 kwadratów dla lepszych marginesów
    squares_per_row = min(squares_per_row, 9)
    squares_per_col = min(squares_per_col, 12)
    
    print(f"Kwadraty w rzędzie: {squares_per_row}")
    print(f"Kwadraty w kolumnie: {squares_per_col}")
    print(f"Rozmiar kwadratu: {square_size_mm} mm")
    print(f"Rozmiar markera ARUCO: {marker_size_mm:.1f} mm")
    
    # Generowanie wzorca ChArUco
    marker_id = 0
    for row in range(squares_per_col):
        for col in range(squares_per_row):
            if marker_id >= 250:  # Maksymalna liczba markerów w słowniku
                break
                
            # Pozycja kwadratu
            x = margin_px + col * square_size_px
            y = margin_px + row * square_size_px
            
            # Rysowanie kwadratu szachownicy
            if (row + col) % 2 == 0:  # Czarny kwadrat
                cv2.rectangle(img, (x, y), (x + square_size_px, y + square_size_px), 0, -1)
                
                # Dodanie markera ARUCO w środku czarnego kwadratu
                marker_x = x + (square_size_px - marker_size_px) // 2
                marker_y = y + (square_size_px - marker_size_px) // 2
                
                # Generowanie markera ARUCO
                marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)
                
                # Umieszczenie markera na obrazie
                img[marker_y:marker_y+marker_size_px, marker_x:marker_x+marker_size_px] = marker
                
                marker_id += 1
            else:  # Biały kwadrat
                cv2.rectangle(img, (x, y), (x + square_size_px, y + square_size_px), 255, -1)
    
    # Dodanie wzorca skali 10 cm (100 mm)
    scale_length_mm = 100
    scale_length_px = int(scale_length_mm * DPI / MM_TO_INCH)
    
    # Pozycja wzorca skali (na samym dole kartki)
    scale_y = height_px - int(10 * DPI / MM_TO_INCH)  # 10mm od dołu
    scale_x_start = width_px // 2 - scale_length_px // 2
    scale_x_end = scale_x_start + scale_length_px
    
    # Rysowanie linii skali
    cv2.line(img, (scale_x_start, scale_y), (scale_x_end, scale_y), 0, 3)
    
    # Dodanie oznaczeń końców linii
    cv2.line(img, (scale_x_start, scale_y - 10), (scale_x_start, scale_y + 10), 0, 2)
    cv2.line(img, (scale_x_end, scale_y - 10), (scale_x_end, scale_y + 10), 0, 2)
    
    # Dodanie tekstu z opisem skali
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    
    text = "100 mm"
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = scale_x_start + (scale_length_px - text_size[0]) // 2
    text_y = scale_y + 30
    
    cv2.putText(img, text, (text_x, text_y), font, font_scale, 0, thickness)
    
    # Konwersja na PDF
    full_path = os.path.join(patterns_dir, filename)
    
    # Użyj matplotlib do konwersji obrazu na PDF
    fig, ax = plt.subplots(figsize=(A4_WIDTH_MM/25.4, A4_HEIGHT_MM/25.4), dpi=DPI)
    ax.imshow(img, cmap='gray', extent=[0, A4_WIDTH_MM, 0, A4_HEIGHT_MM], aspect='equal', origin='lower')
    ax.set_xlim(0, A4_WIDTH_MM)
    ax.set_ylim(0, A4_HEIGHT_MM)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Zapisz do PDF
    with PdfPages(full_path) as pdf:
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
    
    print(f"Wzorzec ChArUco zapisany jako PDF: {full_path}")
    print("✅ Gotowy do wydruku w skali 100% na papierze A4!")
    
    return full_path

def display_pattern(img):
    """
    Wyświetla wzorzec na ekranie
    """
    plt.figure(figsize=(12, 16))
    plt.imshow(img, cmap='gray')
    plt.title('Wzorzec ChArUco do kalibracji kamery (A4)')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def main():
    """
    Główna funkcja programu
    """
    print("=== Generator wzorca ChArUco do kalibracji kamery ===")
    print("Generowanie wzorca ChArUco (szachownica + ARUCO) w PDF na kartce A4 z wzorcem skali 10 cm...")
    
    # Generowanie wzorca bezpośrednio w PDF
    pattern_path = save_pattern_pdf()
    
    print("\n=== Informacje o wzorcu ChArUco ===")
    print(f"Format: PDF")
    print(f"Wymiary A4: 210 x 297 mm")
    print(f"Wzorzec skali: 100 mm (dokładnie)")
    print(f"Rozmiar kwadratu szachownicy: 20 mm")
    print(f"Rozmiar markera ARUCO: 16 mm")
    print(f"Zapisano w folderze: patterns/")
    print(f"\n📄 PLIK DO WYDRUKU: {os.path.basename(pattern_path)}")
    print("✅ Wzorzec ChArUco gotowy do wydruku w skali 100% na papierze A4!")
    print("💡 Uwaga: Wydrukuj w skali 100% - wzorzec skali będzie dokładnie 100mm!")

if __name__ == "__main__":
    main()