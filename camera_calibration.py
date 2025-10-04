#!/usr/bin/env python3
"""
System kalibracji kamery z ARUCO
Przeprowadza pełną kalibrację kamery używając wzorca ARUCO
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime

def calibrate_camera_with_aruco(camera_id=0, num_images=20, marker_size_mm=20):
    """
    Kalibruje kamerę używając wzorca ARUCO
    
    Args:
        camera_id: ID kamery (domyślnie 0)
        num_images: Liczba zdjęć do kalibracji
        marker_size_mm: Rozmiar markera w mm
    """
    print(f"=== Kalibracja kamery z ARUCO ===")
    print(f"Liczba zdjęć: {num_images}")
    print(f"Rozmiar markera: {marker_size_mm} mm")
    
    # Inicjalizacja kamery
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print("Błąd: Nie można otworzyć kamery!")
        return None
    
    # Parametry ARUCO
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    # Listy do przechowywania danych kalibracyjnych
    all_corners = []
    all_ids = []
    image_size = None
    
    print("\nInstrukcje:")
    print("1. Umieść wzorzec ARUCO przed kamerą")
    print("2. Naciśnij SPACJA aby zrobić zdjęcie")
    print("3. Naciśnij ESC aby zakończyć")
    print("4. Zmieniaj pozycję wzorca między zdjęciami")
    
    image_count = 0
    
    while image_count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("Błąd: Nie można odczytać obrazu z kamery!")
            break
        
        # Zapisz rozmiar obrazu
        if image_size is None:
            image_size = (frame.shape[1], frame.shape[0])
        
        # Wykryj markery ARUCO
        corners, ids, _ = detector.detectMarkers(frame)
        
        # Wyświetl wykryte markery
        frame_with_markers = frame.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame_with_markers, corners, ids)
            
            # Wyświetl informacje o wykrytych markerach
            cv2.putText(frame_with_markers, f"Wykryte markery: {len(ids)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame_with_markers, f"Zdjęcie: {image_count + 1}/{num_images}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Jeśli wykryto wystarczająco markerów, pokaż komunikat
            if len(ids) >= 4:
                cv2.putText(frame_with_markers, "Naciśnij SPACJA aby zrobić zdjęcie", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame_with_markers, "Nie wykryto markerów ARUCO", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame_with_markers, f"Zdjęcie: {image_count + 1}/{num_images}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('Kalibracja kamery ARUCO', frame_with_markers)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Spacja - zrób zdjęcie
            if ids is not None and len(ids) >= 4:
                all_corners.append(corners)
                all_ids.append(ids)
                image_count += 1
                print(f"Zdjęcie {image_count} zapisane. Wykryto {len(ids)} markerów.")
            else:
                print("Za mało markerów! Wymagane minimum 4 markery.")
        
        elif key == 27:  # ESC - zakończ
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if len(all_corners) < 5:
        print("Błąd: Za mało zdjęć do kalibracji! Wymagane minimum 5 zdjęć.")
        return None
    
    print(f"\nPrzetwarzanie {len(all_corners)} zdjęć...")
    
    # Przygotuj punkty 3D dla markerów ARUCO
    obj_points = []
    img_points = []
    
    # Rozmiar markera w jednostkach rzeczywistych (mm)
    marker_size = marker_size_mm / 1000.0  # Konwersja na metry
    
    for i in range(len(all_corners)):
        # Punkty 3D dla każdego markera (względem rogu markera)
        objp = np.zeros((4, 3), dtype=np.float32)
        objp[0] = [0, 0, 0]
        objp[1] = [marker_size, 0, 0]
        objp[2] = [marker_size, marker_size, 0]
        objp[3] = [0, marker_size, 0]
        
        # Dla każdego wykrytego markera
        for j in range(len(all_corners[i])):
            obj_points.append(objp)
            img_points.append(all_corners[i][j].reshape(-1, 2))
    
    # Konwersja na numpy arrays
    obj_points = np.array(obj_points, dtype=np.float32)
    img_points = np.array(img_points, dtype=np.float32)
    
    # Kalibracja kamery
    print("Wykonywanie kalibracji...")
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, image_size, None, None
    )
    
    if ret:
        print("Kalibracja zakończona pomyślnie!")
        
        # Oblicz błędy reprojekcji
        total_error = 0
        for i in range(len(obj_points)):
            imgpoints2, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], 
                                            camera_matrix, dist_coeffs)
            error = cv2.norm(img_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error
        
        mean_error = total_error / len(obj_points)
        print(f"Średni błąd reprojekcji: {mean_error:.3f} pikseli")
        
        # Zapisz wyniki kalibracji
        calibration_data = {
            'camera_matrix': camera_matrix.tolist(),
            'dist_coeffs': dist_coeffs.tolist(),
            'image_size': image_size,
            'marker_size_mm': marker_size_mm,
            'num_images': len(all_corners),
            'mean_reprojection_error': float(mean_error),
            'timestamp': datetime.now().isoformat()
        }
        
        save_calibration_results(calibration_data)
        
        return calibration_data
    else:
        print("Błąd podczas kalibracji!")
        return None

def save_calibration_results(calibration_data, filename="camera_calibration.json"):
    """
    Zapisuje wyniki kalibracji do pliku JSON
    """
    with open(filename, 'w') as f:
        json.dump(calibration_data, f, indent=2)
    print(f"Wyniki kalibracji zapisane jako: {filename}")
    
    # Zapisz również w formacie OpenCV XML
    xml_filename = filename.replace('.json', '.xml')
    fs = cv2.FileStorage(xml_filename, cv2.FILE_STORAGE_WRITE)
    fs.write('camera_matrix', calibration_data['camera_matrix'])
    fs.write('dist_coeffs', calibration_data['dist_coeffs'])
    fs.write('image_size', calibration_data['image_size'])
    fs.release()
    print(f"Wyniki kalibracji zapisane również jako: {xml_filename}")

def load_calibration_results(filename="camera_calibration.json"):
    """
    Ładuje wyniki kalibracji z pliku JSON
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Konwersja list na numpy arrays
        data['camera_matrix'] = np.array(data['camera_matrix'])
        data['dist_coeffs'] = np.array(data['dist_coeffs'])
        
        return data
    except FileNotFoundError:
        print(f"Plik {filename} nie istnieje!")
        return None

def test_calibration(camera_id=0, calibration_file="camera_calibration.json"):
    """
    Testuje kalibrację kamery wyświetlając obraz z korekcją zniekształceń
    """
    calibration_data = load_calibration_results(calibration_file)
    if calibration_data is None:
        return
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print("Błąd: Nie można otworzyć kamery!")
        return
    
    camera_matrix = calibration_data['camera_matrix']
    dist_coeffs = calibration_data['dist_coeffs']
    
    print("Test kalibracji - wyświetlanie obrazu z korekcją zniekształceń")
    print("Naciśnij ESC aby zakończyć")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Korekcja zniekształceń
        undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
        
        # Wyświetl oryginalny i skorygowany obraz obok siebie
        combined = np.hstack((frame, undistorted))
        
        cv2.putText(combined, "Oryginalny", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(combined, "Skorygowany", (frame.shape[1] + 10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Test kalibracji kamery', combined)
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
    
    cap.release()
    cv2.destroyAllWindows()

def validate_calibration(calibration_file="camera_calibration.json"):
    """
    Waliduje wyniki kalibracji i wyświetla szczegóły
    """
    calibration_data = load_calibration_results(calibration_file)
    if calibration_data is None:
        return
    
    print("=== WALIDACJA KALIBRACJI ===")
    print(f"Rozmiar obrazu: {calibration_data['image_size']}")
    print(f"Rozmiar markera: {calibration_data['marker_size_mm']} mm")
    print(f"Liczba zdjęć: {calibration_data['num_images']}")
    print(f"Data kalibracji: {calibration_data['timestamp']}")
    print(f"Średni błąd reprojekcji: {calibration_data['mean_reprojection_error']:.3f} pikseli")
    
    # Ocena jakości kalibracji
    error = calibration_data['mean_reprojection_error']
    if error < 1.0:
        print("✅ BARDZO DOBRA KALIBRACJA")
    elif error < 2.0:
        print("✅ DOBRA KALIBRACJA")
    else:
        print("⚠️  KALIBRACJA WYMAGA POPRAWY")
    
    print("\n=== PARAMETRY KAMERY ===")
    camera_matrix = calibration_data['camera_matrix']
    print(f"Macierz kamerowa:")
    print(f"  fx = {camera_matrix[0,0]:.2f}")
    print(f"  fy = {camera_matrix[1,1]:.2f}")
    print(f"  cx = {camera_matrix[0,2]:.2f}")
    print(f"  cy = {camera_matrix[1,2]:.2f}")
    
    dist_coeffs = calibration_data['dist_coeffs']
    print(f"\nWspółczynniki zniekształceń:")
    print(f"  k1 = {dist_coeffs[0]:.6f}")
    print(f"  k2 = {dist_coeffs[1]:.6f}")
    print(f"  p1 = {dist_coeffs[2]:.6f}")
    print(f"  p2 = {dist_coeffs[3]:.6f}")
    print(f"  k3 = {dist_coeffs[4]:.6f}")

def main():
    """
    Główna funkcja programu kalibracji
    """
    print("=== System kalibracji kamery ARUCO ===")
    print("1. Kalibracja kamery")
    print("2. Test kalibracji")
    print("3. Walidacja kalibracji")
    
    choice = input("\nWybierz opcję (1/2/3): ").strip()
    
    if choice == "1":
        print("\nRozpoczynanie kalibracji kamery...")
        marker_size = float(input("Podaj rozmiar markera w mm (domyślnie 20): ") or "20")
        num_images = int(input("Podaj liczbę zdjęć do kalibracji (domyślnie 20): ") or "20")
        
        calibrate_camera_with_aruco(marker_size_mm=marker_size, num_images=num_images)
        
    elif choice == "2":
        print("\nTestowanie kalibracji...")
        test_calibration()
        
    elif choice == "3":
        print("\nWalidacja kalibracji...")
        validate_calibration()
        
    else:
        print("Nieprawidłowy wybór!")

if __name__ == "__main__":
    main()
