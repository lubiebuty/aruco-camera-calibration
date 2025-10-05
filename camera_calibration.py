#!/usr/bin/env python3
"""
Kalibracja kamery na ChArUco z pliku WIDEO – przetwarza **wszystkie klatki**.
Wzorzec zgodny z naszym wydrukiem:
- squares: 4x6
- square=40 mm, marker=32 mm (80%)
- dict=DICT_6X6_1000

Ustaw ścieżkę wideo w stałej SOURCE_PATH.
Wyniki zapisują się do ./calibration/ jako .npz, .json, .xml

Wymaga: opencv-contrib-python, numpy
"""

from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path
import time, json, sys

# ====== KONFIGURACJA ======
# >>> ŚCIEŻKA DO WIDEO (USTAWIONA NA STAŁE) <<<
SOURCE_PATH = "/Users/bartlomiejostasz/PYCH/nagrania/seria1/kalibracja .MOV"

# Parametry naszej planszy (dostosowane do rzeczywistego wzorca ChArUco)
SQUARES_X = 5  # 5 kolumn
SQUARES_Y = 6  # 6 rzędów
SQUARE_MM = 33.33  # Rozmiar kwadratu (100mm / 3 kwadraty = 33.33mm)
MARKER_MM = 26.67  # 80% pola
DICT_NAME = "DICT_6X6_1000"

# Minimalna liczba rogów ChArUco w klatce, aby ją użyć
MIN_CHARUCO = 4  # Zmniejszone z 8 na 4

# Debug - pokazuj postęp
DEBUG = True

# Flagi kalibracji (rozszerzony model dystorsji)
CALIB_FLAGS = cv2.CALIB_RATIONAL_MODEL

# Opcjonalne skalowanie wejścia (None = bez zmian)
RESIZE_WIDTH = None

# ====== Pomocnicze: kompatybilność API OpenCV ======
def _aruco_pkg():
    if not hasattr(cv2, "aruco"):
        sys.exit("Brak modułu cv2.aruco (zainstaluj opencv-contrib-python).")
    return cv2.aruco


def make_dictionary():
    aruco = _aruco_pkg()
    return aruco.getPredefinedDictionary(getattr(aruco, DICT_NAME))


def make_detector(dictionary):
    aruco = _aruco_pkg()
    # DetectorParameters – różne API w zależności od wersji
    if hasattr(aruco, "DetectorParameters"):
        params = aruco.DetectorParameters()
    else:
        params = aruco.DetectorParameters_create()
    
    # Bardzo agresywne parametry dla wykrywania markerów
    params.cornerRefinementMethod = getattr(aruco, "CORNER_REFINE_SUBPIX", 1)
    params.adaptiveThreshWinSizeMin = 3
    params.adaptiveThreshWinSizeMax = 23
    params.adaptiveThreshWinSizeStep = 10
    params.adaptiveThreshConstant = 7
    params.minMarkerPerimeterRate = 0.01  # Bardzo niskie minimum
    params.maxMarkerPerimeterRate = 8.0   # Bardzo wysokie maksimum
    params.polygonalApproxAccuracyRate = 0.1  # Bardziej tolerancyjne
    params.minCornerDistanceRate = 0.01   # Bardzo niskie minimum
    params.minDistanceToBorder = 1        # Bardzo niskie minimum
    params.minMarkerDistanceRate = 0.01   # Bardzo niskie minimum
    params.cornerRefinementWinSize = 5
    params.cornerRefinementMaxIterations = 30
    params.cornerRefinementMinAccuracy = 0.1
    params.markerBorderBits = 1
    params.perspectiveRemovePixelPerCell = 4
    params.perspectiveRemoveIgnoredMarginPerCell = 0.13
    params.maxErroneousBitsInBorderRate = 0.5  # Bardziej tolerancyjne
    params.minOtsuStdDev = 2.0            # Bardziej tolerancyjne
    params.errorCorrectionRate = 0.3     # Bardziej tolerancyjne
    
    # ArucoDetector (nowsze API) lub tuple dla starszego detectMarkers
    if hasattr(aruco, "ArucoDetector"):
        return aruco.ArucoDetector(dictionary, params), params
    return (dictionary, params), params


def make_charuco_detector(board):
    aruco = _aruco_pkg()
    # OpenCV 4.7+ provides a dedicated CharucoDetector API
    if hasattr(aruco, "CharucoDetector"):
        try:
            return aruco.CharucoDetector(board)
        except Exception:
            return None
    return None


def detect_markers(detector, gray):
    aruco = _aruco_pkg()
    if isinstance(detector, tuple):
        dictionary, params = detector
        return aruco.detectMarkers(gray, dictionary, parameters=params)
    return detector.detectMarkers(gray)


def make_charuco_board():
    aruco = _aruco_pkg()
    dic = make_dictionary()

    # 1) Starsze API (funkcja modułu): cv2.aruco.CharucoBoard_create(...)
    if hasattr(aruco, "CharucoBoard_create"):
        return aruco.CharucoBoard_create(
            SQUARES_X, SQUARES_Y, SQUARE_MM, MARKER_MM, dic
        )

    # 2) Nowsze API (metoda klasy): cv2.aruco.CharucoBoard.create(...)
    if hasattr(aruco, "CharucoBoard") and hasattr(aruco.CharucoBoard, "create"):
        return aruco.CharucoBoard.create(
            SQUARES_X, SQUARES_Y, SQUARE_MM, MARKER_MM, dic
        )

    # 3) Alternatywne wiązanie konstruktora (niektóre buildy Pythona):
    try:
        # niektóre wersje akceptują rozmiar jako krotkę (cols, rows)
        return aruco.CharucoBoard((SQUARES_X, SQUARES_Y), SQUARE_MM, MARKER_MM, dic)
    except Exception as e:
        raise AttributeError(
            "Nie można utworzyć CharucoBoard w tej wersji OpenCV. Zainstaluj opencv-contrib-python (np. pip install --upgrade opencv-contrib-python)."
        ) from e


def calibrate_charuco(charuco_corners, charuco_ids, board, image_size):
    aruco = _aruco_pkg()
    if hasattr(aruco, "calibrateCameraCharucoExtended"):
        return aruco.calibrateCameraCharucoExtended(
            charucoCorners=charuco_corners,
            charucoIds=charuco_ids,
            board=board,
            imageSize=image_size,
            cameraMatrix=None,
            distCoeffs=None,
            flags=CALIB_FLAGS,
        )
    # starsze API
    retval, K, D, rvecs, tvecs = aruco.calibrateCameraCharuco(
        charucoCorners=charuco_corners,
        charucoIds=charuco_ids,
        board=board,
        imageSize=image_size,
        cameraMatrix=None,
        distCoeffs=None,
        flags=CALIB_FLAGS,
    )
    return retval, K, D, rvecs, tvecs, None, None, None


# ====== Pipeline kalibracji z WSZYSTKICH KLATEK ======
def calibrate_from_video(source_path: str):
    p = Path(source_path)
    if not p.exists():
        sys.exit(f"Plik wideo nie istnieje: {p}")

    aruco = _aruco_pkg()
    dictionary = make_dictionary()
    board = make_charuco_board()
    detector, _ = make_detector(dictionary)
    charuco_detector = make_charuco_detector(board)

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        sys.exit(f"Nie można otworzyć wideo: {p}")

    charuco_corners_all, charuco_ids_all = [], []
    image_size = None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    used_frames = 0
    processed_frames = 0
    print(f"Źródło: {p}")
    print(f"Klatek w pliku: {total_frames if total_frames>0 else '?'} (przetwarzam wszystkie)")
    print(f"Szukam minimum {MIN_CHARUCO} rogów ChArUco na klatkę")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if RESIZE_WIDTH and frame.shape[1] > RESIZE_WIDTH:
            scale = RESIZE_WIDTH / frame.shape[1]
            frame = cv2.resize(frame, (RESIZE_WIDTH, int(frame.shape[0]*scale)))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        processed_frames += 1
        if DEBUG and processed_frames % 30 == 0:  # co 30 klatek
            print(f"Przetworzono {processed_frames} klatek, użyto {used_frames}")

        if hasattr(aruco, "interpolateCornersCharuco"):
            # Klasyczna ścieżka: detectMarkers -> subpix -> interpolateCornersCharuco
            corners, ids, _ = detect_markers(detector, gray)
            if ids is None or len(ids) == 0:
                if DEBUG and processed_frames % 30 == 0:
                    print(f"  Klatka {processed_frames}: brak markerów ARUCO")
                continue
            
            if DEBUG and processed_frames % 30 == 0:
                print(f"  Klatka {processed_frames}: znaleziono {len(ids)} markerów ARUCO")
                if len(ids) > 0:
                    print(f"    ID markerów: {ids.flatten()[:5]}...")  # Pierwsze 5 ID
            try:
                cv2.cornerSubPix(
                    gray, corners, (5, 5), (-1, -1),
                    (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-4)
                )
            except cv2.error:
                pass
            _, ch_corners, ch_ids = aruco.interpolateCornersCharuco(corners, ids, gray, board)
        else:
            # Fallback dla wersji bez interpolateCornersCharuco: użyj CharucoDetector
            if charuco_detector is None:
                sys.exit("Twoja wersja OpenCV nie ma ani interpolateCornersCharuco ani CharucoDetector. Zaktualizuj opencv-contrib-python.")
            ch_corners, ch_ids, _, _ = charuco_detector.detectBoard(gray)

        if ch_corners is None or ch_ids is None or len(ch_corners) < MIN_CHARUCO:
            if DEBUG and processed_frames % 30 == 0:
                corners_found = len(ch_corners) if ch_corners is not None else 0
                print(f"  Klatka {processed_frames}: znaleziono {corners_found} rogów ChArUco (minimum: {MIN_CHARUCO})")
            continue

        charuco_corners_all.append(ch_corners)
        charuco_ids_all.append(ch_ids)
        used_frames += 1

        if DEBUG and processed_frames % 30 == 0:
            print(f"  Klatka {processed_frames}: ✓ użyto ({len(ch_corners)} rogów)")

        if image_size is None:
            image_size = (gray.shape[1], gray.shape[0])

    cap.release()

    if used_frames < 4:
        sys.exit("Za mało dobrych klatek z rogami ChArUco (>=4 wymagane).")

    print(f"Użyte klatki: {used_frames}")
    print("Kalibracja…")
    retval, K, D, rvecs, tvecs, *_ = calibrate_charuco(charuco_corners_all, charuco_ids_all, board, image_size)

    print(f"RMS reprojection error: {retval:.4f}")
    print("K=\n", K)
    print("D=", D.ravel())

    # ===== Zapis wyników =====
    out_dir = Path.cwd() / "calibration"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = p.with_suffix("").name

    npz_path = out_dir / f"calib_charuco_{base}_{stamp}.npz"
    json_path = out_dir / f"calib_charuco_{base}_{stamp}.json"
    xml_path = out_dir / f"calib_charuco_{base}_{stamp}.xml"

    np.savez(npz_path,
             K=K, D=D, rvecs=rvecs, tvecs=tvecs, rms=retval,
             image_size=image_size, squares=(SQUARES_X, SQUARES_Y),
             square_mm=SQUARE_MM, marker_mm=MARKER_MM, dict=DICT_NAME,
             frames_used=used_frames)

    meta = {
        "rms": float(retval),
        "camera_matrix": K.tolist(),
        "dist_coeffs": D.tolist(),
        "image_size": image_size,
        "squares": [SQUARES_X, SQUARES_Y],
        "square_mm": SQUARE_MM,
        "marker_mm": MARKER_MM,
        "dict": DICT_NAME,
        "frames_used": used_frames,
        "timestamp": stamp,
        "source": str(p)
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    fs = cv2.FileStorage(str(xml_path), cv2.FILE_STORAGE_WRITE)
    fs.write("camera_matrix", K); fs.write("dist_coeffs", D); fs.release()

    print(f"Zapisano: {npz_path}")
    print(f"Zapisano: {json_path}")
    print(f"Zapisano: {xml_path}")

    return retval, K, D


if __name__ == "__main__":
    calibrate_from_video(SOURCE_PATH)
