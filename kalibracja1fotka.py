#!/usr/bin/env python3
"""
Batch ocena zdjęć do kalibracji ChArUco (szachownica + ArUco).
- Dla każdego obrazu w katalogu: wykrywa ChArUco, liczy rogi i udział BB rogów w kadrze,
  zapisuje overlay i wypisuje ACCEPT/REJECT.
- Na końcu drukuje podsumowanie + (opcjonalnie) zapisuje CSV.

Domyślne:
  --dir /Users/bartlomiejostasz/PYCH/nagrania/zdj
  Plansza: 4×6, DICT_6X6_1000, legacy pattern = True
  Progi: min_corners=12, min_area_frac=0.08 (8%)
"""

from __future__ import annotations
import sys, os, argparse, csv
from pathlib import Path
import cv2
import numpy as np

# ---- Ustawienia domyślne ----
DEFAULT_DIR = "/Users/bartlomiejostasz/PYCH/nagrania/zdj"
DEFAULT_OUT = "calib_eval_out"
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp', '.pbm', '.pgm', '.ppm'}

# Plansza
SQUARES_X, SQUARES_Y = 4, 6
DICT_NAME = 'DICT_6X6_1000'
LEGACY_PATTERN = True

# Progi
DEF_MIN_CORNERS = 12
DEF_MIN_AREA_FRAC = 0.08  # 8%

def get_dictionary(name: str):
    aruco = cv2.aruco
    return aruco.getPredefinedDictionary(getattr(aruco, name)) if hasattr(aruco,'getPredefinedDictionary') \
           else aruco.Dictionary_get(getattr(aruco, name))

def create_board(dict_):
    aruco = cv2.aruco
    board = None
    # nowe API
    try:
        board = aruco.CharucoBoard((SQUARES_X, SQUARES_Y), 40.0, 32.0, dict_)
    except Exception:
        pass
    # fallback API
    if board is None and hasattr(aruco, 'CharucoBoard_create'):
        board = aruco.CharucoBoard_create(SQUARES_X, SQUARES_Y, 40.0, 32.0, dict_)
    if board is None:
        raise RuntimeError("Brak CharucoBoard w cv2.aruco (zainstaluj opencv-contrib-python).")
    if LEGACY_PATTERN and hasattr(board, 'setLegacyPattern'):
        try:
            board.setLegacyPattern(True)
        except Exception:
            pass
    return board

def make_detector_params():
    aruco = cv2.aruco
    DP = getattr(aruco, 'DetectorParameters', None)
    det = DP() if DP is not None and callable(DP) else aruco.DetectorParameters_create()
    # czułość pod mniejsze markery
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
    det.cornerRefinementMethod = getattr(aruco, 'CORNER_REFINE_SUBPIX', 1)
    det.cornerRefinementWinSize = 5
    det.cornerRefinementMaxIterations = 50
    det.cornerRefinementMinAccuracy = 0.01
    return det

def list_images(root: Path, recursive: bool) -> list[str]:
    if recursive:
        files = [str(p) for p in root.rglob("*") if p.suffix.lower() in IMG_EXTS]
    else:
        files = [str(p) for p in root.iterdir() if p.suffix.lower() in IMG_EXTS]
    files.sort()
    return files

def eval_image(path: str, dictionary, board, det_params, outdir: Path,
               min_corners: int, min_area_frac: float) -> tuple[bool,int,float,str]:
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        print(f"[SKIP] Nie mogę odczytać: {path}")
        return False, 0, 0.0, ""

    H, W = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    aruco = cv2.aruco

    CD = getattr(aruco, 'CharucoDetector', None)
    if CD is not None:
        charuco_detector = CD(board, None, det_params)
        charucoCorners, charucoIds, markerCorners, markerIds = charuco_detector.detectBoard(gray)
    else:
        markerCorners, markerIds, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)
        charucoCorners, charucoIds = None, None
        if markerIds is not None and len(markerIds) > 0:
            charucoCorners, charucoIds, _ = aruco.interpolateCornersCharuco(
                markerCorners, markerIds, gray, board)

    n = int(charucoCorners.shape[0]) if (charucoCorners is not None) else 0

    # udział pola BB rogów
    area_frac = 0.0
    if n > 0:
        xs = charucoCorners[:,0,0]; ys = charucoCorners[:,0,1]
        x0, x1 = float(np.min(xs)), float(np.max(xs))
        y0, y1 = float(np.min(ys)), float(np.max(ys))
        bw, bh = max(0.0, x1-x0), max(0.0, y1-y0)
        area_frac = (bw*bh) / float(W*H)

    ok = (n >= min_corners) and (area_frac >= min_area_frac)

    # overlay
    vis = bgr.copy()
    if 'markerCorners' in locals() and markerCorners is not None and len(markerCorners) > 0:
        aruco.drawDetectedMarkers(vis, markerCorners, markerIds)
    if charucoCorners is not None and n > 0:
        for pt in charucoCorners:
            c = tuple(int(v) for v in pt[0])
            cv2.circle(vis, c, 3, (0,255,0), -1)

    color = (0,200,0) if ok else (0,0,230)
    label = f"{'ACCEPT' if ok else 'REJECT'}  corners={n}  area={area_frac:.3f}"
    cv2.putText(vis, label, (10,24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    cv2.putText(vis, f"min_corners={min_corners}  min_area={min_area_frac:.3f}", (10,50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20,20,20), 2, cv2.LINE_AA)

    out_img = outdir / (Path(path).stem + "_charuco_debug.jpg")
    cv2.imwrite(str(out_img), vis)

    print(f"[EVAL] {path}: corners={n} area={area_frac:.3f} -> {'ACCEPT' if ok else 'REJECT'}")
    return ok, n, area_frac, str(out_img)

def main():
    ap = argparse.ArgumentParser(description="Batch ocena zdjęć do kalibracji ChArUco.")
    ap.add_argument("--dir", default=DEFAULT_DIR, help="Katalog ze zdjęciami.")
    ap.add_argument("-o", "--outdir", default=DEFAULT_OUT, help="Folder wyjściowy na debug overlay.")
    ap.add_argument("--recursive", action="store_true", help="Rekurencyjnie po podkatalogach.")
    ap.add_argument("--min-corners", type=int, default=DEF_MIN_CORNERS, help="Minimalna liczba rogów.")
    ap.add_argument("--min-area-frac", type=float, default=DEF_MIN_AREA_FRAC, help="Minimalny udział BB rogów [0..1].")
    ap.add_argument("--csv", default=None, help="Opcjonalna ścieżka do CSV z wynikami.")
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.dir))
    if not root.exists():
        print(f"[ERR] Katalog nie istnieje: {root}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    dictionary = get_dictionary(DICT_NAME)
    board = create_board(dictionary)
    det_params = make_detector_params()

    files = list_images(root, args.recursive)
    if not files:
        print(f"[ERR] Brak obrazów w: {root}")
        sys.exit(2)

    total, accepted = 0, 0
    rows = []

    for fp in files:
        total += 1
        ok, n, area, out_img = eval_image(fp, dictionary, board, det_params, outdir,
                                          args.min_corners, args.min_area_frac)
        if ok:
            accepted += 1
        rows.append([fp, ok, n, round(area, 6), out_img])

    print("\n========== SUMMARY ==========")
    print(f"Evaluated: {total}   ACCEPTED: {accepted}   REJECTED: {total-accepted}")
    print(f"Criteria : min_corners={args.min_corners}, min_area_frac={args.min_area_frac:.3f}")

    if args.csv:
        csv_path = Path(args.csv)
        with csv_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["file", "accepted", "corners", "area_frac", "debug_image"])
            w.writerows(rows)
        print(f"[SAVE] CSV: {csv_path}")

if __name__ == "__main__":
    main()