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

def generate_aruco_pattern():
    """
    Generuje wzorzec ARUCO na kartce A4 z wzorcem skali
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
    
    # Parametry wzorca ARUCO
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    # Rozmiar pojedynczego markera ARUCO w mm (większy dla lepszej widoczności)
    marker_size_mm = 30
    marker_size_px = int(marker_size_mm * DPI / MM_TO_INCH)
    
    # Marginesy w mm
    margin_mm = 15
    margin_px = int(margin_mm * DPI / MM_TO_INCH)
    
    # Odstęp między markerami w mm
    spacing_mm = 10
    spacing_px = int(spacing_mm * DPI / MM_TO_INCH)
    
    # Obliczenie ile markerów zmieści się w rzędzie i kolumnie
    available_width = width_px - 2 * margin_px
    available_height = height_px - 2 * margin_px - 100  # miejsce na wzorzec skali
    
    markers_per_row = (available_width + spacing_px) // (marker_size_px + spacing_px)
    markers_per_col = (available_height + spacing_px) // (marker_size_px + spacing_px)
    
    print(f"Markery w rzędzie: {markers_per_row}")
    print(f"Markery w kolumnie: {markers_per_col}")
    print(f"Rozmiar markera: {marker_size_mm} mm")
    
    # Generowanie markerów ARUCO
    marker_id = 0
    for row in range(markers_per_col):
        for col in range(markers_per_row):
            if marker_id >= 250:  # Maksymalna liczba markerów w słowniku
                break
                
            # Pozycja markera
            x = margin_px + col * (marker_size_px + spacing_px)
            y = margin_px + row * (marker_size_px + spacing_px)
            
            # Generowanie markera
            marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)
            
            # Umieszczenie markera na obrazie
            img[y:y+marker_size_px, x:x+marker_size_px] = marker
            
            marker_id += 1
    
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

def save_pattern(img, filename="aruco_calibration_pattern.png"):
    """
    Zapisuje wzorzec do pliku PNG w folderze projektu
    Zapisuje w dwóch wersjach: standardowej i wysokiej rozdzielczości dla wydruku
    """
    # Utwórz folder 'patterns' jeśli nie istnieje
    patterns_dir = "patterns"
    if not os.path.exists(patterns_dir):
        os.makedirs(patterns_dir)
        print(f"Utworzono folder: {patterns_dir}")
    
    # Dodaj timestamp do nazwy pliku
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    timestamped_filename = f"{name}_{timestamp}{ext}"
    
    # Pełna ścieżka do pliku
    full_path = os.path.join(patterns_dir, timestamped_filename)
    
    # Zapisz wzorzec standardowy
    cv2.imwrite(full_path, img)
    print(f"Wzorzec zapisany jako: {full_path}")
    
    # Zapisz również podstawową wersję bez timestamp
    basic_path = os.path.join(patterns_dir, filename)
    cv2.imwrite(basic_path, img)
    print(f"Wzorzec zapisany również jako: {basic_path}")
    
    # Zapisz wersję wysokiej rozdzielczości dla wydruku (300 DPI)
    print_quality_filename = f"{name}_print_quality_{timestamp}{ext}"
    print_quality_path = os.path.join(patterns_dir, print_quality_filename)
    
    # Skaluj obraz do wysokiej rozdzielczości (300 DPI)
    scale_factor = 300.0 / 72.0  # 300 DPI / 72 DPI
    new_width = int(img.shape[1] * scale_factor)
    new_height = int(img.shape[0] * scale_factor)
    
    # Użyj INTER_CUBIC dla lepszej jakości skalowania
    high_res_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Zapisz wysoką rozdzielczość
    cv2.imwrite(print_quality_path, high_res_img)
    print(f"Wzorzec wysokiej jakości (300 DPI) zapisany jako: {print_quality_path}")
    
    # Zapisz również podstawową wersję wysokiej jakości
    print_basic_path = os.path.join(patterns_dir, f"{name}_print_quality{ext}")
    cv2.imwrite(print_basic_path, high_res_img)
    print(f"Wzorzec wysokiej jakości zapisany również jako: {print_basic_path}")
    
    return full_path, basic_path, print_quality_path, print_basic_path

def display_pattern(img):
    """
    Wyświetla wzorzec na ekranie
    """
    plt.figure(figsize=(12, 16))
    plt.imshow(img, cmap='gray')
    plt.title('Wzorzec ARUCO do kalibracji kamery (A4)')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def main():
    """
    Główna funkcja programu
    """
    print("=== Generator wzorca ARUCO do kalibracji kamery ===")
    print("Generowanie wzorca na kartce A4 z wzorcem skali 10 cm...")
    
    # Generowanie wzorca
    img, dpi = generate_aruco_pattern()
    
    # Zapisanie wzorca
    timestamped_path, basic_path, print_quality_path, print_basic_path = save_pattern(img)
    
    # Wyświetlenie wzorca
    display_pattern(img)
    
    print("\n=== Informacje o wzorcu ===")
    print(f"Rozdzielczość: {dpi} DPI")
    print(f"Wymiary A4: 210 x 297 mm")
    print(f"Wzorzec skali: 100 mm")
    print(f"Rozmiar markera: 30 mm")
    print(f"Zapisano w folderze: patterns/")
    print(f"\nPliki wygenerowane:")
    print(f"  - Standardowy: {os.path.basename(basic_path)}")
    print(f"  - Z timestamp: {os.path.basename(timestamped_path)}")
    print(f"  - Wysoka jakość: {os.path.basename(print_basic_path)}")
    print(f"  - Wysoka jakość z timestamp: {os.path.basename(print_quality_path)}")
    print(f"\n📄 DO WYDRUKU UŻYJ: {os.path.basename(print_basic_path)}")
    print("✅ Wzorzec gotowy do wydruku w skali 100% na papierze A4!")

if __name__ == "__main__":
    main()