
// Protocol goes as follows:
// TG-bot sends string, which contains two characters:
// COMMAND [PARAMETER]
//
// COMMAND:
// r = read (currently only led status)
// w = write (currently only led state)
//
// PARAMETER: (only used with write)
// 1 = set led on
// 0 = set led off
//
// Result consist of two characters:
// RESULT [ATTRIBUTE]
//
// RESULT:
// A = answer to read query
// S = write successful
// F = write failed
//
// ATTRIBUTE:
// A: led state (0 or 1)
// S: 0 in all cases
// F: 0 = ledState could not be parsed
//    1 = command character unknown

#define ledpin 8
char toggle;
String result;
int ledState = LOW;

void setup() {
  pinMode(ledpin, OUTPUT);
  Serial.begin(115200);
  Serial.setTimeout(1);
}

void loop() {
  while (!Serial.available());
  result = Serial.readString();

  if (result.charAt(0) == 'r') {
    if (ledState == HIGH) {
      Serial.print("A1");
    } else {
      Serial.print("A0");
    }
  } else if (result.charAt(0) == 'w') {
    toggle = result.charAt(1);
    if (toggle == '1') {
      ledState = HIGH;
      Serial.print("S0");
    } else if (toggle == '0') {
      ledState = LOW;
      Serial.print("S0");
    } else {
      ledState = LOW;
      Serial.print("F0");
    }
    digitalWrite(ledpin, ledState);
  } else {
    Serial.print("F1");
  }
}
