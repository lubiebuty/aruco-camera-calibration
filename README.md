# Generator wzorca ARUCO do kalibracji kamery

## Opis
System do generowania wzorca ARUCO na kartce A4 z dodatkowym wzorcem skali 10 cm (100 mm) do weryfikacji poprawności wydruku.

## Pliki

### 1. `generate_aruco_pattern.py`
Generator wzorca ARUCO - tworzy wzorzec gotowy do wydruku.

### 2. `camera_calibration.py`
System kalibracji kamery - przeprowadza pełną kalibrację kamery używając wzorca ARUCO.

## Instalacja
```bash
# Utwórz środowisko wirtualne
python3 -m venv venv
source venv/bin/activate  # Na Windows: venv\Scripts\activate

# Zainstaluj zależności
pip install -r requirements.txt
```

## Użycie

### Generowanie wzorca ARUCO
```bash
python generate_aruco_pattern.py
```

### Kalibracja kamery
```bash
python camera_calibration.py
```

## Funkcje

### Generator wzorca (`generate_aruco_pattern.py`)
- Generuje wzorzec ARUCO na kartce A4 (210x297 mm)
- Gotowy do wydruku w skali 100% na papierze A4
- Markery ARUCO o rozmiarze 30 mm (lepsza widoczność)
- Wzorzec skali 100 mm na dole kartki
- Automatyczne obliczenie optymalnej liczby markerów
- Zapisuje w dwóch wersjach: standardowej (72 DPI) i wysokiej jakości (300 DPI)

### System kalibracji (`camera_calibration.py`)
- Interaktywna kalibracja z podglądem na żywo
- Wykrywanie markerów ARUCO w czasie rzeczywistym
- Walidacja jakości zdjęć (minimum 4 markery na zdjęcie)
- Obliczanie parametrów kamery (macierz kamerowa, współczynniki zniekształceń)
- Obliczanie błędów reprojekcji
- Zapisywanie wyników w formatach JSON i XML
- Test kalibracji z wizualizacją efektów
- Walidacja wyników kalibracji

## Parametry wzorca
- Słownik ARUCO: DICT_6X6_250
- Rozmiar markera: 30 mm (zwiększony dla lepszej widoczności)
- Marginesy: 15 mm
- Odstęp między markerami: 10 mm
- Wzorzec skali: 100 mm
- Rozdzielczość: 72 DPI (standardowa) + 300 DPI (wysoka jakość)

## Pliki wyjściowe
- `patterns/aruco_calibration_pattern.png` - wzorzec standardowy (72 DPI)
- `patterns/aruco_calibration_pattern_print_quality.png` - **wzorzec do wydruku (300 DPI)**
- `patterns/aruco_calibration_pattern_[timestamp].png` - wzorce z timestamp
- `camera_calibration.json` - parametry kalibracji (JSON)
- `camera_calibration.xml` - parametry kalibracji (OpenCV XML)

## Proces kalibracji
1. Wygeneruj wzorzec ARUCO (`python generate_aruco_pattern.py`)
2. **Wydrukuj plik `patterns/aruco_calibration_pattern_print_quality.png` w skali 100% na papierze A4**
3. Uruchom kalibrację (`python camera_calibration.py`)
4. Umieść wzorzec przed kamerą
5. Zmieniaj pozycję wzorca między zdjęciami
6. Naciśnij SPACJA aby zrobić zdjęcie (minimum 5 zdjęć)
7. Naciśnij ESC aby zakończyć
8. Program automatycznie obliczy parametry kamery

## Instrukcje wydruku
- **Użyj pliku**: `patterns/aruco_calibration_pattern_print_quality.png`
- **Skala**: 100% (bez skalowania)
- **Papier**: A4
- **Orientacja**: Pionowa
- **Jakość**: Wysoka (300 DPI)
- **Sprawdź wzorzec skali**: Linia 100 mm powinna mieć dokładnie 10 cm

## Wymagania techniczne
- Kamera USB lub wbudowana
- Dobre oświetlenie podczas kalibracji
- Stabilne trzymanie wzorca
- Różnorodne pozycje wzorca (kąty, odległości)

## Jakość kalibracji
- Średni błąd reprojekcji < 1.0 piksela = bardzo dobra kalibracja
- Średni błąd reprojekcji < 2.0 pikseli = dobra kalibracja
- Średni błąd reprojekcji > 2.0 pikseli = wymaga ponownej kalibracji

## Rozwiązywanie problemów
- **Za mało markerów**: Upewnij się, że wzorzec jest dobrze oświetlony i w pełni widoczny
- **Wysoki błąd reprojekcji**: Zbierz więcej zdjęć z różnorodnych pozycji
- **Kamera nie działa**: Sprawdź czy kamera jest podłączona i dostępna
