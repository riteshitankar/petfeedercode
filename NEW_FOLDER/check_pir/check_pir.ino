#include <Servo.h>

Servo myServo; // Create a servo object
int pirPin = D5; // PIR sensor connected to GPIO14 (D5 on NodeMCU)
bool motionDetected = false;

void setup() {
  myServo.attach(D4); // Attach the servo to GPIO2 (D4 on NodeMCU)
  pinMode(pirPin, INPUT);
  Serial.begin(9600); // Begin serial communication
}

void loop() {
  // Check for motion from the PIR sensor
  if (digitalRead(pirPin) == HIGH && !motionDetected) {
    motionDetected = true;
    Serial.println("motion_detected"); // Notify the Python script
    delay(2000); // Prevent multiple triggers
    motionDetected = false;
  }

  // Handle servo control commands from the Python script
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      myServo.write(180); // Rotate servo to 90 degrees
      delay(3000);       // Wait for 5 seconds
      myServo.write(0);  // Return servo to 0 degrees
    }
  }
}
