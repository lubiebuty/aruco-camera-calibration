#!/usr/bin/env python3
"""
Kalibracja kamery na wzorcu ChArUco (szachownica + ArUco).
- Wejście: wideo (.mp4/.mov), kamera (np. --source 0), albo katalog/plik glob obrazów.
- Wykrywanie: cv2.aruco.CharucoDetector (OpenCV 4.x) z subpikselem i parametrami pod małe markery.
- Wyjście: plik .npz z K (cameraMatrix), D (distCoeffs), RMS, flags, a także testowy undistort.jpg.

Domyślna plansza: 4×6 pól, square=40 mm, marker=32 mm (80%), DICT_6X6_1000, LEGACY pattern (True).
Druk i generator planszy: użyj wygenerowanej planszy, druk 100% i sprawdź pasek 100 mm.

Uruchomienia (przykłady):
  python charuco_calibrate.py --source /ścieżka/do/kalibracja.MOV -o calib_out
  python charuco_calibrate.py --source 0 --show
  python charuco_calibrate.py --source "/data/imgs/*.jpg" --min-corners 20 --max-frames 200

Wymaga: opencv-contrib-python (4.x), numpy.
"""

from __future__ import annotations
import cv2
import numpy as np
import argparse, sys, os, glob, time
from pathlib import Path
from typing import List, Tuple

# ---------- Domyślne parametry planszy ----------
SQUARES_X = 4             # kolumny
SQUARES_Y = 6             # wiersze
SQUARE_MM = 40.0          # mm
MARKER_FRAC = 0.80        # 80% pola => 32 mm
DICT_NAME = 'DICT_6X6_1000'
LEGACY_PATTERN = True     # zalecane przy parzystych wymiarach i zgodności z 3.x

# ---------- Kryteria jakości ujęć ----------
MIN_CORNERS = 12          # min. liczba rogów ChArUco, żeby zaakceptować klatkę
MIN_FRAMES = 12           # min. liczba zaakceptowanych klatek do kalibracji
FRAME_STEP = 1            # co którą klatkę analizować (1=każdą)
MAX_FRAMES = 500          # górny limit analizowanych klatek/zdjęć

# ---------- Flagi kalibracji ----------
# RATIONAL_MODEL stabilizuje dystorsję, ZERO_TANGENT często ok;
# możesz zmienić wg potrzeb (np. FIX_K3 itd.)
CALIB_FLAGS = (
    cv2.CALIB_RATIONAL_MODEL |
    cv2.CALIB_ZERO_TANGENT_DIST
)

# ---------- Pomocnicze ----------

def is_camera_index(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False

def create_detector_params():
    aruco = cv2.aruco
    # Zgodność z różnymi buildami
    params = getattr(aruco, 'DetectorParameters', None)
    if params is not None and callable(params):
        det = params()
    else:
        det = aruco.DetectorParameters_create()

    # Parametry lepsze dla mniejszych markerów i różnego oświetlenia:
    det.adaptiveThreshWinSizeMin = 3
    det.adaptiveThreshWinSizeMax = 23
    det.adaptiveThreshWinSizeStep = 10
    det.adaptiveThreshConstant = 7
    det.minMarkerPerimeterRate = 0.02
    det.maxMarkerPerimeterRate = 4.0
    det.polygonalApproxAccuracyRate = 0.03
    det.minCornerDistanceRate = 0.05
    det.minOtsuStdDev = 5.0
    det.perspectiveRemovePixelPerCell = 8
    det.perspectiveRemoveIgnoredMarginPerCell = 0.33
    det.cornerRefinementMethod = getattr(cv2.aruco, 'CORNER_REFINE_SUBPIX', 1)
    det.cornerRefinementWinSize = 5
    det.cornerRefinementMaxIterations = 50
    det.cornerRefinementMinAccuracy = 0.01
    return det

def create_charuco_params():
    # W nowszym API istnieje CharucoParameters(); jeśli brak, zwracamy None.
    CP = getattr(cv2.aruco, 'CharucoParameters', None)
    if CP is not None and callable(CP):
        cp = CP()
        cp.tryRefineMarkers = True  # przydaje się, żeby dointerpolować rogi
        return cp
    return None

def get_dictionary(name: str):
    aruco = cv2.aruco
    if hasattr(aruco, 'getPredefinedDictionary'):
        return aruco.getPredefinedDictionary(getattr(aruco, name))
    return aruco.Dictionary_get(getattr(aruco, name))

def create_board(sx: int, sy: int, square_mm: float, marker_mm: float, dictionary):
    aruco = cv2.aruco
    # Uwaga: jednostka długości może być mm — skala wpływa na translacje, nie na K,D.
    board = None
    try:
        board = aruco.CharucoBoard((sx, sy), float(square_mm), float(marker_mm), dictionary)
    except Exception:
        pass
    if board is None and hasattr(aruco, 'CharucoBoard_create'):
        board = aruco.CharucoBoard_create(sx, sy, float(square_mm), float(marker_mm), dictionary)
    if board is None:
        raise RuntimeError("Nie udało się utworzyć CharucoBoard (sprawdź opencv-contrib-python).")
    if LEGACY_PATTERN and hasattr(board, 'setLegacyPattern'):
        try:
            board.setLegacyPattern(True)
        except Exception:
            pass
    return board

def make_charuco_detector(board):
    aruco = cv2.aruco
    det_params = create_detector_params()
    ch_params = create_charuco_params()
    CD = getattr(aruco, 'CharucoDetector', None)
    if CD is None:
        # fallback – będziemy wykrywać markery ArUco i interpolować rogi manualnie
        return None, det_params, ch_params
    return CD(board, ch_params, det_params), det_params, ch_params

def gather_images_from_source(source: str) -> List[str] | None:
    # Jeśli katalog lub glob – zwróć listę obrazów
    p = Path(source)
    if any(ch in source for ch in ['*', '?', '[']):
        files = sorted(glob.glob(source))
        return [f for f in files if Path(f).is_file()]
    if p.exists() and p.is_dir():
        exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
        files = sorted([str(fp) for fp in p.iterdir() if fp.suffix.lower() in exts])
        return files
    if p.exists() and p.is_file():
        # pojedynczy obraz – potraktujemy jak listę 1-elementową
        return [str(p)]
    return None

def draw_debug(frame, charuco_corners, charuco_ids, marker_corners=None, marker_ids=None):
    vis = frame.copy()
    if marker_corners is not None and marker_ids is not None and len(marker_corners) > 0:
        cv2.aruco.drawDetectedMarkers(vis, marker_corners, marker_ids)
    if charuco_corners is not None and charuco_ids is not None and len(charuco_corners) > 0:
        # rysuj numerki rogów
        for i, (pt, idx) in enumerate(zip(charuco_corners, charuco_ids)):
            c = tuple(int(v) for v in pt[0])
            cv2.circle(vis, c, 3, (0, 255, 0), -1)
            cv2.putText(vis, str(int(idx)), (c[0]+3, c[1]-3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1, cv2.LINE_AA)
    return vis

# ---------- Główna logika ----------

def main():
    ap = argparse.ArgumentParser(description="Kalibracja kamery ChArUco (OpenCV 4.x).")
    ap.add_argument("--source", default="/Users/bartlomiejostasz/PYCH/nagrania/seria1/kalibracja .MOV",
                    help="Źródło: indeks kamery (np. 0) lub ścieżka do wideo/obrazu/katalogu (glob też). Domyślnie 0.")
    ap.add_argument("-o", "--outdir", default="calib_out", help="Folder wyjściowy (.npz, podglądy).")
    ap.add_argument("--dict", default=DICT_NAME, help="Słownik ArUco, np. DICT_6X6_1000.")
    ap.add_argument("--sx", type=int, default=SQUARES_X, help="Liczba pól w poziomie (kolumny).")
    ap.add_argument("--sy", type=int, default=SQUARES_Y, help="Liczba pól w pionie (wiersze).")
    ap.add_argument("--square-mm", type=float, default=SQUARE_MM, help="Rozmiar pola [mm].")
    ap.add_argument("--marker-frac", type=float, default=MARKER_FRAC, help="Udział markera w polu [0..1].")
    ap.add_argument("--legacy", action="store_true", default=LEGACY_PATTERN, help="Wymuś legacy pattern.")
    ap.add_argument("--min-corners", type=int, default=MIN_CORNERS, help="Min rogów ChArUco na klatkę.")
    ap.add_argument("--min-frames", type=int, default=MIN_FRAMES, help="Min zaakceptowanych klatek.")
    ap.add_argument("--frame-step", type=int, default=FRAME_STEP, help="Co którą klatkę analizować.")
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES, help="Limit analizowanych klatek/zdjęć.")
    ap.add_argument("--show", action="store_true", help="Pokaż podgląd detekcji.")
    args = ap.parse_args()

    # Normalizacja źródła: domyślnie kamera 0, rozwiń ewentualne '~'
    if args.source is None or str(args.source).strip() == "":
        args.source = "0"
    args.source = os.path.expanduser(str(args.source))
    if args.source == "0":
        print("[INFO] --source nie podano; używam kamery 0 (domyślne).")

    # Jeżeli ścieżka nie istnieje, spróbuj skorygować ewentualną spację przed kropką rozszerzenia
    if not Path(args.source).exists():
        src_try = args.source
        if ' .' in src_try:
            src_try2 = src_try.replace(' .', '.')
            if Path(src_try2).exists():
                print(f"[INFO] Skorygowano ścieżkę źródła: '{src_try}' -> '{src_try2}'")
                args.source = src_try2

    os.makedirs(args.outdir, exist_ok=True)

    # Plansza i słownik
    dictionary = get_dictionary(args.dict)
    marker_mm = args.square_mm * args.marker_frac
    board = create_board(args.sx, args.sy, args.square_mm, marker_mm, dictionary)

    # Detector
    charuco_detector, det_params, ch_params = make_charuco_detector(board)

    # Zbieracze
    all_corners: List[np.ndarray] = []
    all_ids: List[np.ndarray] = []
    imsize: Tuple[int, int] | None = None
    accepted = 0

    # Źródło: kamera/wideo czy obrazy?
    image_list = gather_images_from_source(args.source)

    def process_frame(bgr) -> Tuple[int, np.ndarray | None]:
        nonlocal accepted, imsize
        if imsize is None:
            h, w = bgr.shape[:2]
            imsize = (w, h)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Detekcja
        if charuco_detector is not None:
            # Nowy API: zwraca już zinterpolowane rogi ChArUco
            charucoCorners, charucoIds, markerCorners, markerIds = charuco_detector.detectBoard(gray)
        else:
            # Fallback: wykryj markery, potem interpoluj rogi ChArUco
            markerCorners, markerIds, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=det_params)
            charucoCorners, charucoIds = None, None
            if markerIds is not None and len(markerIds) > 0:
                charucoCorners, charucoIds, _ = cv2.aruco.interpolateCornersCharuco(
                    markerCorners, markerIds, gray, board)

        n_c = int(charucoCorners.shape[0]) if (charucoCorners is not None) else 0
        vis = draw_debug(bgr, charucoCorners, charucoIds,
                         markerCorners if 'markerCorners' in locals() else None,
                         markerIds if 'markerIds' in locals() else None)

        if n_c >= args.min_corners:
            all_corners.append(charucoCorners)
            all_ids.append(charucoIds)
            accepted += 1
            status = 1
            cv2.putText(vis, f"ACCEPT [{n_c} corners]", (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 210, 0), 2, cv2.LINE_AA)
        else:
            status = 0
            cv2.putText(vis, f"REJECT [{n_c} corners < {args.min_corners}]", (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 210), 2, cv2.LINE_AA)

        return status, vis

    if image_list is not None:
        # Tryb obrazów
        for i, fp in enumerate(image_list):
            if i >= args.max_frames:
                break
            bgr = cv2.imread(fp, cv2.IMREAD_COLOR)
            if bgr is None:
                print(f"[WARN] Nie mogę odczytać {fp}")
                continue
            status, vis = process_frame(bgr)
            if args.show:
                cv2.imshow("ChArUco detect", vis)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        if args.show:
            cv2.destroyAllWindows()

    elif is_camera_index(args.source) or Path(args.source).suffix.lower() in {'.mp4', '.mov', '.mkv', '.avi'} or Path(args.source).exists():
        # Tryb kamera/wideo
        cap = cv2.VideoCapture(0 if is_camera_index(args.source) else args.source)
        if not cap.isOpened():
            print(f"[ERROR] Nie otwarto źródła: {args.source}")
            sys.exit(1)
        frame_idx = 0
        used = 0
        while True:
            ret, bgr = cap.read()
            if not ret:
                break
            if (frame_idx % args.frame_step) != 0:
                frame_idx += 1
                continue
            status, vis = process_frame(bgr)
            used += 1
            if args.show:
                cv2.imshow("ChArUco detect", vis)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            if used >= args.max_frames:
                break
            frame_idx += 1
        cap.release()
        if args.show:
            cv2.destroyAllWindows()
    else:
        print(f"[ERROR] Nie rozpoznaję źródła: {args.source}")
        sys.exit(1)

    # --- Kalibracja ---
    if accepted < max(args.min_frames, 4):
        print(f"[ERROR] Za mało dobrych klatek ({accepted}) – potrzeba >= {max(args.min_frames, 4)}.")
        sys.exit(2)

    print(f"[INFO] Kalibracja… ujęć: {accepted}, obraz: {imsize}")
    # Uwaga: squareSize w jednostkach boardu (tu mm) – skala translacji.
    # calibrateCameraCharucoExtended zwraca też per-view errors i odchylenia.
    rms, K, D, rvecs, tvecs, stdInt, stdExt, perViewErrors = \
        cv2.aruco.calibrateCameraCharucoExtended(
            charucoCorners=all_corners,
            charucoIds=all_ids,
            board=board,
            imageSize=imsize,
            cameraMatrix=None,
            distCoeffs=None,
            flags=CALIB_FLAGS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
        )

    print(f"[OK] RMS reprojection error: {rms:.4f}")
    # Zapis wyników
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_npz = Path(args.outdir) / f"charuco_calib_{ts}.npz"
    np.savez_compressed(
        out_npz,
        K=K, D=D, rvecs=rvecs, tvecs=tvecs,
        stdIntrinsics=stdInt, stdExtrinsics=stdExt, perViewErrors=perViewErrors,
        rms=rms, image_size=np.array(imsize),
        squares=np.array([args.sx, args.sy]),
        square_mm=args.square_mm, marker_mm=marker_mm,
        dict=args.dict, legacy=args.legacy, flags=int(CALIB_FLAGS),
        accepted_frames=accepted, min_corners=args.min_corners
    )
    print(f"[SAVE] {out_npz}")

    # Podgląd undistort na ostatniej ramce wejściowej (lub syntetycznej)
    # Wygenerujemy czysty widok siatki z newK dla podglądu:
    if imsize is not None:
        w, h = imsize
        newK, roi = cv2.getOptimalNewCameraMatrix(K, D, (w, h), alpha=0.0)  # pełne usunięcie dystorsji
        # Stwórz syntetyczną kratkę dla podglądu (łatwiej zauważyć krzywizny)
        grid = np.full((h, w, 3), 255, np.uint8)
        step = max(40, min(w, h)//20)
        for x in range(0, w, step):
            cv2.line(grid, (x, 0), (x, h-1), (220, 220, 220), 1)
        for y in range(0, h, step):
            cv2.line(grid, (0, y), (w-1, y), (220, 220, 220), 1)
        map1, map2 = cv2.initUndistortRectifyMap(K, D, None, newK, (w, h), cv2.CV_16SC2)
        und = cv2.remap(grid, map1, map2, interpolation=cv2.INTER_LINEAR)
        out_jpg = Path(args.outdir) / f"undistort_preview_{ts}.jpg"
        cv2.imwrite(str(out_jpg), und)
        print(f"[SAVE] {out_jpg}")

if __name__ == "__main__":
    main()
