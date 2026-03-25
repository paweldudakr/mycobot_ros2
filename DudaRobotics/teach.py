import time, json
from pymycobot import MyCobot280

mc = MyCobot280('/dev/ttyUSB0', 115200)
FILENAME = "/ros2_ws/src/mycobot_ros2/DudaRobotics/trajectory.json"

def record():
    print("Rozluźniam silniki... Możesz teraz poruszać ramieniem ręką.")
    mc.release_all_servos()
    
    trajectory = []
    duration = 20 # sekundy nagrywania
    start_time = time.time()
    
    print(f"Nagrywanie rozpocznie się za 2 sekundy i potrwa {duration}s...")
    time.sleep(2)
    print(">>> NAGRYWANIE ROZPOCZĘTE! <<<")
    
    while time.time() - start_time < duration:
        # Pobieramy kąty wszystkich stawów
        angles = mc.get_angles()
        if angles:
            trajectory.append(angles)
        time.sleep(0.1) # Próbkowanie co 100ms
        
    print("Nagrywanie zakończone. Zapisuję do pliku...")
    with open(FILENAME, 'w') as f:
        json.dump(trajectory, f)
    
    # Blokujemy silniki z powrotem na ostatniej pozycji
    mc.send_angles(mc.get_angles(), 50)
    print("Gotowe. Silniki znów trzymają pozycję.")

def play():
    print("Wczytuję ruch z pliku...")
    with open(FILENAME, 'r') as f:
        trajectory = json.load(f)
    
    print("Odtwarzanie ruchu...")
    for angles in trajectory:
        mc.send_angles(angles, 80)
        time.sleep(0.1)
    print("Odtwarzanie zakończone.")

# WYBIERZ CO CHCESZ ZROBIĆ:
choice = input("Wpisz 'r' aby nagrać lub 'p' aby odtworzyć: ")
if choice == 'r':
    record()
elif choice == 'p':
    play()
