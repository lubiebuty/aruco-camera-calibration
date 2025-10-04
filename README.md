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
- Rozdzielczość 300 DPI dla wysokiej jakości wydruku
- Markery ARUCO o rozmiarze 20 mm
- Wzorzec skali 100 mm na dole kartki
- Automatyczne obliczenie optymalnej liczby markerów

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
- Rozmiar markera: 20 mm
- Marginesy: 10 mm
- Odstęp między markerami: 5 mm
- Wzorzec skali: 100 mm

## Pliki wyjściowe
- `aruco_calibration_pattern.png` - wzorzec gotowy do wydruku
- `camera_calibration.json` - parametry kalibracji (JSON)
- `camera_calibration.xml` - parametry kalibracji (OpenCV XML)

## Proces kalibracji
1. Wydrukuj wzorzec ARUCO (`python generate_aruco_pattern.py`)
2. Uruchom kalibrację (`python camera_calibration.py`)
3. Umieść wzorzec przed kamerą
4. Zmieniaj pozycję wzorca między zdjęciami
5. Naciśnij SPACJA aby zrobić zdjęcie (minimum 5 zdjęć)
6. Naciśnij ESC aby zakończyć
7. Program automatycznie obliczy parametry kamery

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
