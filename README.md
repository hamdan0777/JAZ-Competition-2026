#  Gesture-Controlled Hazardous Environment Reconnaissance Vehicle


                        <img width="394" height="278" alt="image" src="https://github.com/user-attachments/assets/0c647ad4-567a-47d5-a806-e3d8463813e7" />


A two-subsystem IoT robotics project built for competition. A wireless gesture glove controls a sensor-equipped ground vehicle that streams live environmental telemetry to a ThingSpeak cloud dashboard — with full bidirectional control.

---

##  Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Hardware](#hardware)
- [Wiring](#wiring)
- [Software](#software)
- [ThingSpeak Setup](#thingspeak-setup)
- [IR Command Map](#ir-command-map)
- [Gesture Map](#gesture-map)
- [Hazard Logic](#hazard-logic)
- [Installation](#installation)
- [Usage](#usage)
- [Known Issues](#known-issues)
- [Future Improvements](#future-improvements)

---

## Overview

Hazardous environments such as fire scenes, chemical spill zones, and explosive disposal sites pose extreme risks to human personnel. This project presents a remotely operated reconnaissance vehicle capable of entering these zones, collecting environmental data, and streaming it live to a cloud dashboard — while the operator retains full control from a safe distance.

**Key features:**
- Tilt-based gesture control via MPU-6050 glove
- IR remote backup override
- Diagonal gesture detection (simultaneous drive + steer)
- Auto-stop on obstacle detection (< 13cm)
- Live ThingSpeak dashboard with 8 data channels
- Remote emergency kill switch via ThingSpeak
- Composite hazard score (0–100) via MATLAB
- RGB hazard indicator (green / yellow / red)
- Latching buzzer alarm with remote clear
- Heat index and dew point calculated via MATLAB visualizations

---

## System Architecture

```
┌─────────────────────┐         ┌──────────────────────────────────┐
│   GESTURE GLOVE     │         │           VEHICLE                │
│                     │         │                                  │
│  MPU-6050 (I2C)     │         │  HX1838 IR receiver              │
│  Pico 2             │──IR──►  │  Arduino Uno R3                  │
│  IR LED (940nm)     │         │  L293D + DC motor + servo        │
│  9V → PSU → 5V      │         │  DHT11, HC-SR04, PIR, sound      │
│                     │         │  RGB LED, buzzer, LED            │
└─────────────────────┘         └──────────────┬───────────────────┘
                                               │ USB + extension cable
                                ┌──────────────▼───────────────────┐
        ┌───────────────────────│       PYTHON BRIDGE              │
        │  ThingSpeak commands  │  pyserial + requests             │
        │◄──────────────────────│  reads serial → ThingSpeak       │
        │                       │  polls ThingSpeak → Arduino      │
        │                       └──────────────────────────────────┘
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                      THINGSPEAK DASHBOARD                         │
│  field1 Temperature    field5 Sound level                        │
│  field2 Humidity       field6 Kill switch (read)                 │
│  field3 Distance       field7 Manual alarm (read)               │
│  field4 Motion         field8 Temp threshold (read)             │
│                                                                   │
│  MATLAB: Heat index · Dew point · Hazard score gauge · Graphs    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Hardware

### Glove Controller
| Component | Role | Notes |
|---|---|---|
| Raspberry Pi Pico 2 | Main controller | MicroPython |
| MPU-6050 | Gesture sensing | I2C, 6-axis IMU |
| IR LED (extracted) | IR transmission | 940nm, NEC protocol |
| 9V battery | Power supply | Via breadboard PSU |
| Breadboard PSU module | Voltage regulation | 9V → 5V |
| Resistor 100Ω | IR LED current limit | |

### Vehicle
| Component | Role | Notes |
|---|---|---|
| Arduino Uno R3 | Main MCU | All vehicle logic |
| HX1838 IR receiver | Receives commands | Pin 3 |
| L293D motor driver | Controls DC motor | 600mA per channel |
| DC motor (RC axle) | Drive (fwd/back) | 3–6V |
| SG90 servo | Front steering | 4.8–6V, 180° |
| DHT11 | Temp + humidity | ±2°C, ±5% RH |
| HC-SR04 | Obstacle detection | 2–400cm |
| HC-SR501 PIR | Motion detection | 3–7m range |
| Sound sensor | Acoustic detection | Analog output |
| RGB LED | Hazard indicator | Common cathode |
| Active buzzer | Local alert | 5V, latching |
| LED | Status/headlight | 5mm |
| 9V battery | Motor supply | L293D Vmotor |
| 100µF capacitors (×2) | Motor noise filter | Across motor terminals |
| 100nF capacitors (×2) | Motor noise filter | Across motor terminals |

### Connection
| Component | Role |
|---|---|
| USB-B cable | Arduino to USB extension |
| USB-A extension (3–5m) | Operating radius tether |

---

## Wiring

### Glove — Pico 2 Pin Map
```
GP0  → MPU-6050 SDA
GP1  → MPU-6050 SCL
GP3  → IR LED (+ 100Ω resistor → GND)
3.3V → MPU-6050 VCC
GND  → MPU-6050 GND
VSYS → PSU 5V out
```

### Vehicle — Arduino Pin Map
```
Pin 2  → Active buzzer
Pin 3  → HX1838 IR receiver
Pin 4  → PIR sensor
Pin 5  → SG90 servo signal
Pin 6  → DHT11 data
Pin 7  → L293D IN1 (motor direction)
Pin 8  → L293D IN2 (motor direction)
Pin 9  → L293D EN1 (motor enable)
Pin 10 → HC-SR04 TRIG
Pin 12 → HC-SR04 ECHO
Pin 13 → LED
A0    → Sound sensor analog out
A1    → RGB LED red
A2    → RGB LED green
A3    → RGB LED blue
5V    → L293D pin 16 (logic), SG90 VCC, sensors VCC
GND   → All GND (shared)
```

### L293D Power
```
L293D pin 8  → 9V battery (+)
L293D pin 16 → Arduino 5V
All GND      → common ground (Arduino GND + 9V battery -)
```

---

## Software

### File Structure
```
project/
├── vehicle/
│   └── vehicle.ino        Arduino vehicle code
├── glove/
│   └── glove.py           MicroPython glove code (Pico 2)
├── bridge/
│   ├── bridge.py          Python serial bridge
│   └── .env               API keys (not committed)
└── thingspeak/
    ├── heat_index.m        MATLAB dual axis visualization
    ├── dew_point.m         MATLAB dual axis visualization
    └── hazard_score.m      MATLAB gauge visualization
```

### Dependencies

**Python bridge:**
```
pip install pyserial requests python-dotenv
```

**Arduino libraries:**
```
DHT sensor library (Adafruit)
IRremote
Servo (built-in)
```

**Pico 2 MicroPython:**
```
ir_tx library (NEC)
machine (built-in)
```

---

## ThingSpeak Setup

### Channel Fields
| Field | Name | Direction | Type |
|---|---|---|---|
| field1 | Temperature | Send | °C |
| field2 | Humidity | Send | % |
| field3 | Distance | Send | cm |
| field4 | Motion | Send | 0/1 |
| field5 | Sound | Send | 0–1023 |
| field6 | Kill Switch | Read | 0/1 |
| field7 | Manual Alarm | Read | 0/1 |
| field8 | Temp Threshold | Read | °C |

### Environment Variables (.env)
```
THINGSPEAK_WRITE_KEY=your_write_api_key
THINGSPEAK_READ_KEY=your_read_api_key
THINGSPEAK_CHANNEL_ID=your_channel_id
```

### MATLAB Visualizations
| File | Template | Shows |
|---|---|---|
| heat_index.m | Dual Y-axis | Temperature + Heat Index |
| dew_point.m | Dual Y-axis | Temperature + Dew Point |
| hazard_score.m | Custom gauge | Live 0–100 Hazard Score |

---

## IR Command Map

| Button | CMD | HEX | Action |
|---|---|---|---|
| UP | 24 | 0xE718FF00 | Forward |
| DOWN | 82 | 0xAD52FF00 | Backward |
| RIGHT | 90 | 0xA55AFF00 | Steer right |
| LEFT | 8 | 0xF708FF00 | Steer left |
| OK | 64 | 0xEA15FF00 | Stop + centre |
| STAR (*) | 22 | 0xE916FF00 | Clear alarm |
| HASH (#) | 13 | 0xF20DFF00 | Toggle LED |

---

## Gesture Map

| Gesture | AcY | AcX | Command |
|---|---|---|---|
| Tilt forward | < -7000 | — | Forward |
| Tilt backward | > 7000 | — | Backward |
| Tilt right | — | < -7000 | Steer right |
| Tilt left | — | > 7000 | Steer left |
| Tilt fwd + right | < -7000 | < -7000 | Forward + right |
| Tilt fwd + left | < -7000 | > 7000 | Forward + left |
| Tilt back + right | > 7000 | < -7000 | Backward + right |
| Tilt back + left | > 7000 | > 7000 | Backward + left |
| Flat | — | — | Stop |

---

## Hazard Logic

### RGB Indicator + Buzzer
| Condition | RGB | Buzzer |
|---|---|---|
| temp ≥ 40°C OR sound ≥ 800 OR humidity ≥ 77% | 🔴 Red | Latches ON |
| temp > 35°C OR sound > 680 | 🟡 Yellow | OFF |
| All clear | 🟢 Green | OFF |

### Hazard Score Weighting
```
Temperature  → 0–40 points
Sound        → 0–30 points
Humidity     → 0–20 points
Motion       → 0 or 10 points
Total        → 0–100
```

### ThingSpeak Commands (Python → Arduino)
| Command | Effect |
|---|---|
| KILL | Emergency stop, sets remoteKill flag |
| RESUME | Clears remoteKill flag |
| BUZZER_ON | Triggers buzzer latch |
| BUZZER_OFF | Clears buzzer latch |
| TEMP_THRESH:XX | Updates temperature threshold |

---

## Installation

**1. Flash Pico 2:**
```
Download MicroPython UF2 for Pico 2
Flash via BOOTSEL mode
Copy glove.py via Thonny or rshell
Install ir_tx library
```

**2. Upload Arduino sketch:**
```
Open vehicle.ino in Arduino IDE
Install DHT, IRremote libraries
Select Arduino Uno + correct COM port
Upload
```

**3. Set up Python bridge:**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install pyserial requests python-dotenv
cp .env.example .env
# fill in your ThingSpeak API keys
python bridge.py
```

**4. ThingSpeak:**
```
Create channel with 8 fields
Set up 3 MATLAB visualizations
Note channel ID and API keys
Add to .env file
```

---

## Usage

**Starting the system:**
```
1. Connect 9V battery to L293D on vehicle
2. Connect USB extension from Arduino to laptop
3. Power glove from 9V battery via PSU
4. Run: python bridge.py
5. Open ThingSpeak dashboard in browser
6. Point glove at vehicle IR receiver
7. Tilt to control
```

**ThingSpeak control:**
```
field6 = 1  → emergency kill
field6 = 0  → resume
field7 = 1  → trigger alarm
field7 = 0  → clear alarm
field8 = XX → set temp threshold
```

---

## Known Issues

| Issue | Cause | Status |
|---|---|---|
| IR line of sight required | IR physics | By design — use remote override |
| USB tether limits range | No WiFi module | Reframed as EOD-style tethered link |
| Kill switch 2–7s latency | ThingSpeak polling interval | Mitigated — IR remote instant override |
| DHT11 ±2°C accuracy | Sensor spec | Sufficient for threshold detection |
| Single direction auto-stop | HC-SR04 forward only | Reverse always allowed |

---

## Future Improvements

```
→ Camera module for visual telemetry
→ DHT22 for improved sensor accuracy
→ HC-05 Bluetooth for wireless tether elimination
→ Gas sensor (MQ-2/MQ-135) for chemical hazard detection
→ GPS module for position logging to ThingSpeak
→ PID line following mode
→ Automatic obstacle avoidance mode
→ Battery level monitoring
```

---

## Real World Parallel

> Like real EOD robots (iRobot PackBot) and nuclear inspection vehicles, this system maintains a wired telemetry link for reliable data transmission from the hazardous zone — a deliberate design choice prioritising communication reliability over full wireless operation.

---

*Built for IoT competition — Arduino Uno + Raspberry Pi Pico 2 + ThingSpeak*
