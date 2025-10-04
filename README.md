# Generator wzorca ChArUco do kalibracji kamery

## Opis
System do generowania wzorca ChArUco (szachownica + ARUCO) na kartce A4 z dodatkowym wzorcem skali 10 cm (100 mm) do weryfikacji poprawności wydruku.

## Pliki

### 1. `generate_aruco_pattern.py`
Generator wzorca ChArUco - tworzy wzorzec szachownicy z markerami ARUCO gotowy do wydruku.

### 2. `camera_calibration.py`
System kalibracji kamery - przeprowadza pełną kalibrację kamery używając wzorca ChArUco.

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
- Generuje wzorzec ChArUco (szachownica + ARUCO) na kartce A4 (210x297 mm)
- Gotowy do wydruku w skali 100% na papierze A4
- Kwadraty szachownicy o rozmiarze 20 mm
- Markery ARUCO o rozmiarze 16 mm (80% rozmiaru kwadratu)
- Wzorzec skali 100 mm na dole kartki
- Automatyczne obliczenie optymalnej liczby kwadratów
- Zapisuje w dwóch wersjach: standardowej (72 DPI) i wysokiej jakości (300 DPI)

### System kalibracji (`camera_calibration.py`)
- Interaktywna kalibracja z podglądem na żywo
- Wykrywanie markerów ChArUco w czasie rzeczywistym
- Walidacja jakości zdjęć (minimum 4 markery na zdjęcie)
- Obliczanie parametrów kamery (macierz kamerowa, współczynniki zniekształceń)
- Używa cv2.aruco.calibrateCameraAruco dla ChArUco
- Obliczanie błędów reprojekcji
- Zapisywanie wyników w formatach JSON i XML
- Test kalibracji z wizualizacją efektów
- Walidacja wyników kalibracji

## Parametry wzorca ChArUco
- Słownik ARUCO: DICT_6X6_250
- Rozmiar kwadratu szachownicy: 20 mm
- Rozmiar markera ARUCO: 16 mm (80% rozmiaru kwadratu)
- Marginesy: 15 mm
- Wzorzec skali: 100 mm
- Rozdzielczość: 72 DPI (standardowa) + 300 DPI (wysoka jakość)

## Pliki wyjściowe
- `patterns/charuco_calibration_pattern.png` - wzorzec standardowy (72 DPI)
- `patterns/charuco_calibration_pattern_print_quality.png` - **wzorzec do wydruku (300 DPI)**
- `patterns/charuco_calibration_pattern_[timestamp].png` - wzorce z timestamp
- `camera_calibration.json` - parametry kalibracji (JSON)
- `camera_calibration.xml` - parametry kalibracji (OpenCV XML)

## Proces kalibracji
1. Wygeneruj wzorzec ChArUco (`python generate_aruco_pattern.py`)
2. **Wydrukuj plik `patterns/charuco_calibration_pattern_print_quality.png` w skali 100% na papierze A4**
3. Uruchom kalibrację (`python camera_calibration.py`)
4. Umieść wzorzec przed kamerą
5. Zmieniaj pozycję wzorca między zdjęciami
6. Naciśnij SPACJA aby zrobić zdjęcie (minimum 5 zdjęć)
7. Naciśnij ESC aby zakończyć
8. Program automatycznie obliczy parametry kamery

## Instrukcje wydruku
- **Użyj pliku**: `patterns/charuco_calibration_pattern_print_quality.png`
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
