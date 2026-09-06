from machine import I2C, Pin
from time import sleep
from ir_tx.nec import NEC

irled = NEC(Pin(3))
imu = Pin(4, Pin.IN)
MPU_addr = 0x68
i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=400000)
i2c.writeto_mem(MPU_addr, 0x6B, b'\x00')


def read_raw(addr):
    high, low = i2c.readfrom_mem(MPU_addr, addr, 2)
    value = high << 8 | low
    
    if value > 32767:
        value -= 65536
    return value

while True:
    AcX = read_raw(0x3B)
    AcY = read_raw(0x3D)
    AcZ = read_raw(0x3F)

    temp = read_raw(0x41) / 340.0 + 36.53
    GyX = read_raw(0x43)
    GyY = read_raw(0x45)
    GyZ = read_raw(0x47)
    print(f"AcX: {AcX} AcY: {AcY} AcZ: {AcZ} \nGyX: {GyX} GyY: {GyY} GyZ:{GyZ} \tTemp: {temp}°C")
    sleep(0.3)
    if AcY > -7000:
        irled.transmit(0x00, 24) #up
    elif AcY < 7000:
        irled.transmit(0x00, 82) #down
    elif AcX > -7000:
        irled.transmit(0x00, 90) #right
    elif AcX < 7000:
        irled.transmit(0x00, 8) #left
    else:
        irled.value(0) #off