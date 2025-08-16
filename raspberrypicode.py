import serial
import requests
import RPi.GPIO as GPIO
import time

# Pin setup (GND-triggered relays, active-low buzzer)
PASS_RELAY_PIN = 22  # OK LED
FAIL_RELAY_PIN = 27  # REJECT LED
BUZZER_PIN = 17      # Buzzer

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PASS_RELAY_PIN, GPIO.OUT)
GPIO.setup(FAIL_RELAY_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Initial condition: relays OFF (GPIO HIGH), buzzer OFF (GPIO HIGH)
GPIO.output(PASS_RELAY_PIN, GPIO.HIGH)
GPIO.output(FAIL_RELAY_PIN, GPIO.HIGH)
GPIO.output(BUZZER_PIN, GPIO.HIGH)

# Serial setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
print("Listening on /dev/ttyUSB0...")

try:
    while True:
        line_raw = ser.readline()
        line = line_raw.decode(errors='ignore').strip().replace('\x00', '')

        if not line:
            continue

        # Beep buzzer for 0.1 seconds when data is received (active-low)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(1)
        GPIO.output(BUZZER_PIN, GPIO.HIGH)

        print(f"Received raw: {line_raw}")
        print(f"Received cleaned: {line}")

        try:
            weight = float(line)
            print(f"Parsed weight: {weight:.2f}")
        except ValueError:
            print("Invalid float data")
            continue

        # API URL
        api_url = f"http://169.254.120.142:5000/send_weight?weight={weight:.2f}"
        print(f"Sending to API: {api_url}")

        try:
            response = requests.get(api_url, timeout=5)
            data = response.json()
            print("API Response JSON:", data)

            if data.get("result") == "pass":
                GPIO.output(PASS_RELAY_PIN, GPIO.LOW)   # Relay ON
                GPIO.output(FAIL_RELAY_PIN, GPIO.HIGH)  # Relay OFF
                print("Status: ✅ PASS")
                time.sleep(5)  # Keep LED on for 5 seconds
                GPIO.output(PASS_RELAY_PIN, GPIO.HIGH)  # Relay OFF
            else:
                GPIO.output(PASS_RELAY_PIN, GPIO.HIGH)  # Relay OFF
                GPIO.output(FAIL_RELAY_PIN, GPIO.LOW)   # Relay ON
                print("Status: ❌ FAIL")
                time.sleep(5)  # Keep LED on for 5 seconds
                GPIO.output(FAIL_RELAY_PIN, GPIO.HIGH)  # Relay OFF

        except Exception as e:
            print("API request failed:", e)

        time.sleep(1)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    GPIO.output(PASS_RELAY_PIN, GPIO.HIGH)
    GPIO.output(FAIL_RELAY_PIN, GPIO.HIGH)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    GPIO.cleanup()
    ser.close()
    print("Cleaned up and exited")