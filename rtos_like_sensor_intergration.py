import uasyncio as asyncio
from machine import Pin, ADC, I2C
from pico_i2c_lcd import I2cLcd
import dht
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
i2c_addr = i2c.scan()[0]

lcd = I2cLcd(i2c, i2c_addr, 2, 16)
lcd.backlight_on()
lcd.clear()
ldr = ADC(26)

trig = Pin(3, Pin.OUT)
echo = Pin(2, Pin.IN)

dht_sensor = dht.DHT11(Pin(15))


temperature = 0
humidity = 0
light = 0
distance = 0


def get_distance():
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    while echo.value() == 0:
        pass
    start = time.ticks_us()

    while echo.value() == 1:
        pass
    end = time.ticks_us()

    duration = time.ticks_diff(end, start)
    return (duration * 0.0343) / 2



async def temp_task():
    global temperature, humidity
    while True:
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()

        except Exception as e:
            print("DHT22 Error:", e)

        await asyncio.sleep(2)

async def light_task():
    global light
    while True:
        light = ldr.read_u16()
        await asyncio.sleep(0.5)

async def distance_task():
    global distance
    while True:
        distance = get_distance()
        await asyncio.sleep(0.7)

async def display_task():
    while True:
        lcd.clear()

        lcd.move_to(0, 0)
        lcd.putstr("T:{}C H:{}%".format(temperature, humidity))

        lcd.move_to(0, 1)
        lcd.putstr("L:{}D:{:.1f}CM".format(light, distance))

        await asyncio.sleep(1)


async def main():
    asyncio.create_task(temp_task())
    asyncio.create_task(light_task())
    asyncio.create_task(distance_task())
    asyncio.create_task(display_task())

    while True:
        await asyncio.sleep(1)

asyncio.run(main())