import RPi.GPIO as GPIO
import time
import requests

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP) ## Data from sensor up
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) ## Data from sensor down
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) ## Data from button up
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) ## Data from button down

##PIN Output for relay
GPIO.setup(18, GPIO.OUT) ## Relay L1
GPIO.setup(23, GPIO.OUT) ## Relay L2
GPIO.setup(24, GPIO.OUT) ## Relay L3
GPIO.setup(25, GPIO.OUT) ## Relay L4


try:
    while True:
        input_state_up = GPIO.input(4)
        if input_state_up == False:
            ## request to API (POST)
            url = 'https://scar.tierkun.my.id/api/internal/count'
            myobj = {'location': 'Warehouse 1', 'type': 'enter'}

            x = requests.post(url, data=myobj)
            print(x.text)
            
            if x.text == 'success':
                print('User has exited')
            else:
                print('Error')
            
            time.sleep(0.2)
            
        input_state_down = GPIO.input(22)
        if input_state_down == False:
            ## request to API (POST)
            url = 'https://scar.tierkun.my.id/api/internal/count'
            myobj = {'location': 'Warehouse 1', 'type': 'exit'}

            x = requests.post(url, data=myobj)
            print(x.text)
            
            if x.text == 'success':
                print('User has entered')
            else:
                print('Error')
            
            time.sleep(0.2)
        
        input_state_button_up = GPIO.input(17)
        if input_state_button_up == False:
            ## request to API (POST)
            url = 'https://scar.tierkun.my.id/api/internal/mancount'
            myobj = {'location': 'Warehouse 1', 'type': 'enter'}

            x = requests.post(url, data=myobj)
            print(x.text)
            
            if x.text == 'success':
                print('User has exited')
            else:
                print('Error')
            
            time.sleep(0.2)
            
        input_state_button_down = GPIO.input(27)
        if input_state_button_down == False:
            ## request to API (POST)
            url = 'https://scar.tierkun.my.id/api/internal/mancount'
            myobj = {'location': 'Warehouse 1', 'type': 'exit'}

            x = requests.post(url, data=myobj)
            print(x.text)
            
            if x.text == 'success':
                print('User has entered')
            else:
                print('Error')
            
            time.sleep(0.2)        
    
except KeyboardInterrupt:
    print("Program interrupted")
    GPIO.cleanup()