
#define ledpin 8
int toggle;

void setup() {
  pinMode(ledpin, OUTPUT);
  Serial.begin(115200);
  Serial.setTimeout(1);
}

void loop() {
  while (!Serial.available());
  toggle = Serial.readString().toInt();

  if(toggle==1){
    digitalWrite(ledpin, HIGH);
  } else {
    digitalWrite(ledpin, LOW);
  }
  Serial.print('S');
}
