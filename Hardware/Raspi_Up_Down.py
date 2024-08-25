import RPi.GPIO as GPIO
import time
import requests
import threading

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Data from sensor up 1
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Data from sensor down 1
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Data from sensor up 2
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Data from sensor down 2
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Data from button up
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Data from button down

# PIN Output for relay
GPIO.setup(18, GPIO.OUT)  # Relay L1
GPIO.setup(23, GPIO.OUT)  # Relay L2
GPIO.setup(24, GPIO.OUT)  # Relay L3
GPIO.setup(25, GPIO.OUT)  # Relay L4

def handle_input(channel, url, myobj):
    print(f"Detected on channel {channel}")
    x = requests.post(url, data=myobj)
    print(x.text)
    if x.text == 'success':
        print(f"{myobj['type'].capitalize()} success for {myobj['location']}")
    else:
        print("Error")
    time.sleep(0.2)  # Debounce delay

def setup_thread(channel, url, myobj):
    def thread_func(channel):
        while True:
            input_state = GPIO.input(channel)
            if input_state == False:
                handle_input(channel, url, myobj)
            time.sleep(0.1)
    thread = threading.Thread(target=thread_func, args=(channel,))
    thread.daemon = True  # Ensures thread exits when main program exits
    thread.start()

try:
    setup_thread(5, 'https://scar.tierkun.my.id/api/internal/count', {'location': 'Warehouse 1', 'type': 'entrance'})
    setup_thread(6, 'https://scar.tierkun.my.id/api/internal/count', {'location': 'Warehouse 1', 'type': 'exit'})
    setup_thread(11, 'https://scar.tierkun.my.id/api/internal/count', {'location': 'Warehouse 1', 'type': 'entrance'})
    setup_thread(9, 'https://scar.tierkun.my.id/api/internal/count', {'location': 'Warehouse 1', 'type': 'exit'})
    setup_thread(13, 'https://scar.tierkun.my.id/api/internal/mancount', {'location': 'Warehouse 1', 'type': 'entrance'})
    setup_thread(19, 'https://scar.tierkun.my.id/api/internal/mancount', {'location': 'Warehouse 1', 'type': 'exit'})
    
    # Keep the main program running to keep the threads alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted")
    GPIO.cleanup()

