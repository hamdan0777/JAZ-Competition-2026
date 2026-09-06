import serial # Read serial data from Arduino
import requests # Send data to ThingSpeak via HTTP requests

import time # For timing ThingSpeak updates

from dotenv import load_dotenv # Load environment variables from .env file
import os # For environment variables (ThingSpeak API key)

load_dotenv()
SERIAL_PORT = "COM10" # Match the port your Arduino is connected to (e.g., "COM3" on Windows or "/dev/ttyUSB0" on Linux)
BAUD_RATE = 9600 # Match the baud rate set in your Arduino sketch
THINGSPEAK_API_KEY = os.environ["THINGSPEAK_API_KEY"]
THINGSPEAK_READ_API_KEY = os.environ["THINGSPEAK_READ_API_KEY"]
THINGSPEAK_CHANNEL_ID = os.environ["THINGSPEAK_CHANNEL_ID"]

THINGSPEAK_URL = "https://api.thingspeak.com/update"
THINGSPEAK_READ_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields"

min_interval = 15  # ThingSpeak free tier limit: 1 update per 15 seconds
cmd_check_interval = 5 # Check for serial commands every 5 seconds

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print(f"Listening on {SERIAL_PORT}, logging to ThingSpeak...")

last_post = 0.0 # Non-blocking timing for ThingSpeak updates
last_cmd_check = 0.0 # Non-blocking timing for command checking

def send_to_serial(cmd):
    try: 
        ser.write(f"{cmd}\n".encode()) # Send the command followed by a newline character to indicate the end of the command. Encoding it to bytes is necessary for serial communication. 
    except serial.SerialException as e:  # serial.SerialException is a specific exception type for serial communication errors, which allows us to catch and handle errors related to the serial port more effectively. By catching this exception, we can provide a more informative error message if something goes wrong with the serial communication, such as the port being unavailable or disconnected.
        print(f"  -> Serial error: {e}")

def read_thingspeak_field(field):
    try:
        response = requests.get(f"{THINGSPEAK_READ_URL}/{field}/last.json?api_key={THINGSPEAK_READ_API_KEY}", timeout=5) # Make a GET request to the ThingSpeak API to read the last value of the specified field. The URL is constructed using the base read URL, the field number, and the read API key for authentication. A timeout of 5 seconds is set to prevent hanging if the request takes too long.
        if response.status_code == 200: 
            return response.json().get("field"+str(field), None)  # Return the value of the specified field (e.g., "field6" for field 6) from the JSON response dictionary. If the field is not found, return None.
    except Exception as e:
        print(f"  -> ThingSpeak read error: {e}")
    return None     

while True:
    line = ser.readline().decode("utf-8", errors="replace").rstrip()
    if not line:
        continue
    print(line)

    parts = line.split()
    if len(parts) < 14: # Expecting at least 14 parts based on the serial output format
        continue
    # Extract values based on the expected format: "Temp: X | Humidity: Y | Distance: Z | Motion: A | Sound: B"
    temp = parts[1]
    humidity = parts[4]
    distance = parts[7]
    motion = parts[10]
    sound = parts[13]

    now = time.time()
    if now - last_post < min_interval: # Too soon to post again, skip this reading
        continue

    response = requests.get(f"{THINGSPEAK_URL}?api_key={THINGSPEAK_API_KEY}&field1={temp}&field2={humidity}&field3={distance}&field4={motion}&field5={sound}")
    if response.status_code == 200 and response.text != "0":
        print(f"  -> Posted Temp={temp}, Humidity={humidity}, Distance={distance}, Motion={motion}, Sound={sound} (entry {response.text})") #response.text contains the entry number of the update, which is useful for confirming that the data was logged successfully
    else:
        print(f"  -> Thingspeak error: {response.status_code} {response.text}") # If the response status code is not 200 (OK) or if the response text is "0" (indicating an error in logging), print an error message with the status code and response text for debugging.
    
    last_post = now

    #read commands from ThingSpeak every 5 seconds
    if now - last_cmd_check >=cmd_check_interval:
        kill = read_thingspeak_field(6)
        if kill == "1":
            send_to_serial("KILL")
        elif kill == "0":
            send_to_serial("RESUME")
        
        alarm = read_thingspeak_field(7)
        if alarm == "1":
            send_to_serial("BUZZER_ON")
        elif alarm == "0":
            send_to_serial("BUZZER_OFF")
        
        temp_threshold = read_thingspeak_field(8)
        if temp_threshold:
            send_to_serial(f"TEMP_THRESH: {temp_threshold}")
