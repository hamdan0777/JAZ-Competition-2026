#include <DHT.h>
#include <Servo.h>
#include <IRremote.h>

const int dht_sda = 6;
#define DHT_TYPE DHT11
DHT dht(dht_sda, DHT_TYPE);

const int servoPin = 5;
Servo myServo;

const int irReceiver = 3;

const int trig = 13;
const int echo = 12;
const int pir = 4;
const int sound = A0;
const int buzzer = 2;
const int led = 9;

const int motorA_en  = 11;
const int motorA_in1 = 7;
const int motorA_in2 = 8;

const int red = A1;
const int green = A2;
const int blue = A3;

float temp = 0;
float humidity = 0;
int soundLevel = 0;
float distance = 0;
bool motion = false;
bool autoStop = false;
bool buzzerLatch = false;

unsigned long lastDHTRead = 0;
unsigned long lastSent = 0;

//features
int soundThreshold = 800;
int warnSound = 680;
float tempThreshold = 40.0;
float warnTemp = 35.0;

void setRGB(bool r, bool g, bool b) {
  digitalWrite(red, r ? HIGH : LOW);
  digitalWrite(green, g ? HIGH : LOW);
  digitalWrite(blue, b ? HIGH : LOW);
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  myServo.attach(servoPin);
  myServo.write(90);
  IrReceiver.begin(irReceiver, DISABLE_LED_FEEDBACK);
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  pinMode(pir, INPUT);
  pinMode(sound, INPUT);
  pinMode(buzzer, OUTPUT);
  pinMode(led, OUTPUT);
  pinMode(motorA_en,  OUTPUT);
  pinMode(motorA_in1, OUTPUT);
  pinMode(motorA_in2, OUTPUT);
  pinMode(red, OUTPUT);
  pinMode(green, OUTPUT);
  pinMode(blue, OUTPUT);
}

void loop() {

  // DHT11 — max once per 2 seconds
  if (millis() - lastDHTRead >= 2000) {
    temp = dht.readTemperature();
    humidity = dht.readHumidity();
    if (isnan(temp) || isnan(humidity)) { temp = -1; humidity = -1; }
    lastDHTRead = millis();
  }

  // HC-SR04 — 30ms timeout
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long duration = pulseIn(echo, HIGH, 30000);
  distance = (duration == 0) ? -1 : duration / 58.0;

  // PIR
  motion = digitalRead(pir);

  // Sound
  soundLevel = analogRead(sound);

  if (millis() - lastSent >= 2000) {
    Serial.print("Temp: ");     Serial.print(temp);      Serial.print(" | ");
    Serial.print("Humidity: "); Serial.print(humidity);  Serial.print(" | ");
    Serial.print("Distance: "); Serial.print(distance);  Serial.print(" | ");
    Serial.print("Motion: ");   Serial.print(motion);    Serial.print(" | ");
    Serial.print("Sound: ");    Serial.println(soundLevel);
    lastSent = millis();
  }
  // IR
  if (IrReceiver.decode()) {
    digitalWrite(motorA_en, HIGH);
    unsigned long hex_code = IrReceiver.decodedIRData.decodedRawData;
    int cmd = IrReceiver.decodedIRData.command;

    if (cmd == 24 || hex_code == 0xE718FF00) {        // UP
      myServo.write(90);
      if (!autoStop) {
        digitalWrite(motorA_in1, HIGH);
        digitalWrite(motorA_in2, LOW);
      }
    }
    else if (cmd == 82 || hex_code == 0xAD52FF00) {   // DOWN
      myServo.write(90);
      digitalWrite(motorA_in1, LOW);
      digitalWrite(motorA_in2, HIGH);
    }
    else if (cmd == 90 || hex_code == 0xA55AFF00) {   // RIGHT
      myServo.write(120);
    }
    else if (cmd == 8 || hex_code == 0xF708FF00) {    // LEFT
      myServo.write(60);
    }
    else {
      digitalWrite(motorA_in1, LOW);
      digitalWrite(motorA_in2, LOW);
    }
    IrReceiver.resume();
  }
 
  if (temp >= tempThreshold || humidity >= 77 || soundLevel >= soundThreshold) { 
    buzzerLatch = true;
    setRGB(0, 1, 1);
  }
  else if (soundLevel > warnSound || temp > warnTemp) {
    setRGB(1, 1, 0);
  } 
  else {
    setRGB(1, 0, 0);
  }

  //auto stop
  if (distance <=13 && distance!= -1) {
    autoStop = true;
    digitalWrite(motorA_in1, LOW);
    digitalWrite(motorA_in2, LOW);
  }
  else {
    autoStop = false;
  }
}