This project demonstrates a multitasking embedded system developed using the Raspberry Pi Pico and MicroPython. The system simultaneously monitors environmental and proximity parameters using multiple sensors and displays the collected data on an I2C LCD display. By utilizing the uasyncio library, multiple sensor-reading tasks run concurrently, enabling efficient real-time monitoring without blocking program execution.

Features
Real-time temperature and humidity monitoring using the DHT22 sensor.
Ambient light intensity measurement using an LDR sensor.
Distance measurement using an HC-SR04 ultrasonic sensor.
Simultaneous execution of multiple tasks using MicroPython's uasyncio.
Live display of sensor readings on a 16x2 I2C LCD.
Modular and non-blocking code structure suitable for embedded applications.
Hardware Components
Raspberry Pi Pico
DHT22 Temperature and Humidity Sensor
LDR (Light Dependent Resistor)
HC-SR04 Ultrasonic Sensor
16x2 I2C LCD Display
Connecting wires and breadboard
Software Requirements
MicroPython Firmware for Raspberry Pi Pico
Thonny IDE or any MicroPython-compatible IDE
Required Libraries:
uasyncio
dht
pico_i2c_lcd
Working Principle

The system creates independent asynchronous tasks for temperature/humidity sensing, light sensing, distance measurement, and LCD updates. Sensor values are continuously updated in shared variables and displayed on the LCD in real time. This approach demonstrates cooperative multitasking in embedded systems, improving responsiveness and resource utilization.

Applications
Smart home monitoring systems
Environmental monitoring
Industrial parameter monitoring
IoT and embedded systems learning projects
Real-time sensor data acquisition systems
Learning Outcomes
Understanding asynchronous programming in MicroPython.
Sensor interfacing with Raspberry Pi Pico.
Real-time embedded system design.
LCD communication using the I2C protocol.
Efficient multitasking using uasyncio.

Author: Madhusudhan K V
Platform: Raspberry Pi Pico + MicroPython
Domain: Embedded Systems & Internet of Things (IoT)
