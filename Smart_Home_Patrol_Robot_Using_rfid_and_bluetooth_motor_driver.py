from machine import Pin, ADC, UART, PWM, I2C
import time
import dht
import network
import urequests
from pico_i2c_lcd import I2cLcd
from mfrc522 import MFRC522
from time import sleep


SSID = "your_wifi_ssid_here"
PASSWORD = "your_wifi_password_here"
AIO_USERNAME = "your_adafruit_username_here"
AIO_KEY = "your_adafruit_key_here"

last_upload = 0
UPLOAD_INTERVAL = 20000
light = Pin(5, Pin.OUT)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        print("Connecting WiFi...")
        time.sleep(1)

    print("WiFi Connected")
    light.value(1)
    sleep(1)
    light.value(0)

connect_wifi()


i2c = I2C(1, scl=Pin(27), sda=Pin(26))
lcd = I2cLcd(i2c, 0x27, 2, 16)


rfid_reader= MFRC522(spi_id=0, sck=18, miso=16, mosi=19, cs=17, rst=20)

AUTHORIZED_UID=1548903522


btn_auto = Pin(14, Pin.IN, Pin.PULL_DOWN)
btn_manual = Pin(15, Pin.IN, Pin.PULL_DOWN)


ldr = ADC(28)



dht_sensor = dht.DHT11(Pin(13))


uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))


left1 = Pin(6, Pin.OUT)
left2 = Pin(7, Pin.OUT)
right1 = Pin(8, Pin.OUT)
right2 = Pin(9, Pin.OUT)


trig = Pin(3, Pin.OUT)
echo = Pin(2, Pin.IN)


servo = PWM(Pin(4))
servo.freq(50)

mode = None


def forward():
    left1.value(1); left2.value(0)
    right1.value(1); right2.value(0)

def backward():
    left1.value(0); left2.value(1)
    right1.value(0); right2.value(1)

def stop():
    left1.value(0); left2.value(0)
    right1.value(0); right2.value(0)

def turn_left():
    left1.value(0); left2.value(0)
    right1.value(1); right2.value(0)
    sleep(0.5)

def turn_right():
    left1.value(1); left2.value(0)
    right1.value(0); right2.value(0)
    sleep(0.5)

def rotate_right():
    left1.value(1); left2.value(0)
    right1.value(0); right2.value(1)
    sleep(1)

def get_distance():
    trig.low(); time.sleep_us(2)
    trig.high(); time.sleep_us(10)
    trig.low()

    while echo.value() == 0:
        pass
    start = time.ticks_us()

    while echo.value() == 1:
        pass
    end = time.ticks_us()

    return (time.ticks_diff(end, start) * 0.0343) / 2

def set_angle(angle):
    duty = int(1000 + (angle / 180) * 8000)
    servo.duty_u16(duty)

def check_light():
    value=ldr.read_u16()
    if value<10000:      
        light.value(1)
        return "ON"
    else:
        light.value(0)
        return "OFF"

def read_dht():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
        sleep(2)
    except:
        return 0, 0

def send_to_adafruit(temp, hum, light_status):
    try:
        headers = {"X-AIO-Key": AIO_KEY}

        # -------- TEMPERATURE --------
        res = urequests.post(
            f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/tempo.temperature/data",
            json={"value": temp},
            headers=headers
        )
        res.close()
        time.sleep(1)

        # -------- HUMIDITY --------
        res = urequests.post(
            f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/tempo.humidity/data",
            json={"value": hum},
            headers=headers
        )
        res.close()
        time.sleep(1)

        # -------- LIGHT --------
        res = urequests.post(
            f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/tempo.light-status/data",
            json={"value": light_status},
            headers=headers
        )
        res.close()

        print("Uploaded:", temp, hum, light_status)

    except Exception as e:
        print("Upload failed:", e)

def read_rfid():
    rfid_reader.init()
    status,_= rfid_reader.request(rfid_reader.REQIDL)
    if status == rfid_reader.OK:
        status, uid = rfid_reader.SelectTagSN()
        if status == rfid_reader.OK:
            return int.from_bytes (bytes (uid), "little")
        return None

# -------- AUTH --------
while True:
    uid = read_rfid()
    lcd.clear()

    if uid == AUTHORIZED_UID:
        lcd.putstr("Hello Madhu\nSelect Mode")
        time.sleep(2)
        break
    else:
        lcd.putstr("Unknown Card!")
        time.sleep(1)

# -------- MODE SELECT --------
while mode is None:
    lcd.move_to(0,0)
    lcd.putstr("1:Auto2:Manual")

    if btn_auto.value():
        mode = "AUTO"
    elif btn_manual.value():
        mode = "MANUAL"

# -------- MAIN LOOP --------
while True:
    light_status = check_light()
    temp, hum = read_dht()

    # Upload to cloud
    now = time.ticks_ms()
    if time.ticks_diff(now, last_upload) > UPLOAD_INTERVAL:
        send_to_adafruit(temp, hum,light_status)
        last_upload = now

    lcd.clear()
    lcd.putstr(f"{mode[:4]} L:{light_status[:3]}\nT:{temp} H:{hum}")

    if mode == "AUTO":
        front = get_distance()

        if front > 20:
            forward()
        else:
            stop()
            backward()
            time.sleep(0.5)
            stop()

            set_angle(150); time.sleep(0.3)
            left = get_distance()

            set_angle(30); time.sleep(0.3)
            right = get_distance()

            set_angle(90)

            if left > right:
                turn_left()
            else:
                turn_right()

            time.sleep(0.6)
            stop()

    elif mode == "MANUAL":
        if get_distance() < 20:
            backward()
            time.sleep(0.5)
            stop()
            continue

        if uart.any():
            cmd = uart.read().decode().strip()

            if cmd == 'F': forward() print("Forward")
            elif cmd == 'B': backward() print("Backward")
            elif cmd == 'L': turn_left() print("Left")
            elif cmd == 'R': turn_right() print("Right")
            elif cmd == 'S': stop() print("stop")

    time.sleep(0.2)
