from machine import Pin, ADC, UART, PWM, I2C
import time
import dht
import network
import urequests
from pico_i2c_lcd import I2cLcd
from mfrc522 import MFRC522
from time import sleep

SSID = ""
PASSWORD = ""
THINGSPEAK_API_KEY = ""

last_upload = 0
UPLOAD_INTERVAL = 20000 

light = Pin(5, Pin.OUT)

# -------- WIFI --------
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
rfid_reader = MFRC522(spi_id=0, sck=18, miso=16, mosi=19, cs=17, rst=20)
AUTHORIZED_UID = 1548903522
btn_auto = Pin(14, Pin.IN, Pin.PULL_DOWN)
btn_manual = Pin(15, Pin.IN, Pin.PULL_DOWN)
ldr = ADC(28)
dht_sensor = dht.DHT11(Pin(13))
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
trig = Pin(3, Pin.OUT)
echo = Pin(2, Pin.IN)
servo = PWM(Pin(4))
servo.freq(50)

mode = None
def stop():
    print("Motors Stopped")

def forward():
    print("Forward")

def backward():
    print("Backward")

def left():
    print("Left")

def right():
    print("Right")

def get_distance():
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    timeout = time.ticks_us()

    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return 999

    start = time.ticks_us()

    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > 30000:
            return 999

    end = time.ticks_us()

    return (time.ticks_diff(end, start) * 0.0343) / 2

def set_angle(angle):
    duty = int(1000 + (angle / 180) * 8000)
    servo.duty_u16(duty)

def check_light():
    value = ldr.read_u16()
    if value < 10000:
        light.value(1)
        return 1   
    else:
        light.value(0)
        return 0

def read_dht():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        sleep(2)
        return temp, hum
    except:
        return 0, 0

def send_to_thingspeak(temp, hum, light_val):
    import socket
    import gc
    gc.collect()
    try:
        addr = socket.getaddrinfo("api.thingspeak.com", 80)[0][-1]
        request = (
            "GET /update?api_key={}&field1={}&field2={}&field3={} HTTP/1.1\r\n"
            "Host: api.thingspeak.com\r\n"
            "Connection: close\r\n\r\n"
        ).format(THINGSPEAK_API_KEY, temp, hum, light_val)

        print("Sending via socket...")

        s = socket.socket()
        s.connect(addr)
        s.send(request.encode())

        response = s.recv(1024)
        print("Response:", response)

        s.close()
        print("Upload Success")

    except Exception as e:
        print("Upload failed:", e)

def read_rfid():
    rfid_reader.init()
    status, _ = rfid_reader.request(rfid_reader.REQIDL)

    if status == rfid_reader.OK:
        status, uid = rfid_reader.SelectTagSN()
        if status == rfid_reader.OK:
            return int.from_bytes(bytes(uid), "little")
    return None


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

while mode is None:
    lcd.move_to(0,0)
    lcd.putstr("1:Auto2:Manual")

    if btn_auto.value():
        mode = "AUTO"
    elif btn_manual.value():
        mode = "MANUAL"


while True:
    temp, hum = read_dht()
    light_val = check_light()
    lcd.clear()
    lcd.putstr(f"{mode[:4]} L:{light_val}\nT:{temp} H:{hum}")
    if mode == "AUTO":
        front = get_distance()

        if front > 10:
            forward()
        else:
            stop()
            backward()
            time.sleep(0.5)

            set_angle(150)
            time.sleep(0.3)
            left_dist = get_distance()

            set_angle(30)
            time.sleep(0.3)
            right_dist = get_distance()

            set_angle(90)

            if left_dist > right_dist:
                left()
            else:
                right()

            time.sleep(0.5)
            stop()
    elif mode == "MANUAL":
        if get_distance() < 10:
            stop()
            backward()
            stop()
            continue

        if uart.any():
            cmd = uart.read().decode().strip()

            if cmd == 'F': forward()
            elif cmd == 'B': backward()
            elif cmd == 'L': left()
            elif cmd == 'R': right()
            elif cmd == 'S': stop()
    now = time.ticks_ms()
    if time.ticks_diff(now, last_upload) > UPLOAD_INTERVAL:
        send_to_thingspeak(temp, hum, light_val)
        last_upload = now

    time.sleep(0.2)