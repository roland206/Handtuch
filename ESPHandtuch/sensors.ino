#include "context.h"
#include "HX711.h"

HX711 sensor1, sensor2;
static int valid = 0;

void initSensors()
{
  sensor1.begin(SDA1_PIN, SCL1_PIN);
  sensor2.begin(SDA2_PIN, SCL2_PIN);
  while (valid < 3)
    checkSensors();
}

void calibrateSensors(int value) {

  if (value == 0) {
    sys.zero1 = sys.readSensor1;
    sys.zero2 = sys.readSensor2;
  } else {
    sys.scale1 = (float)(value / 2.0) / (float)(sys.readSensor1 - sys.zero1);
    sys.scale2 = (float)(value / 2.0) / (float)(sys.readSensor2 - sys.zero2);
    sys.scale2 = (float)(value / 2.0) / (float)(sys.readSensor1 - sys.zero1);
  }
  Serial.printf("Z1:%d:S1:%f:Z2:%d:S2:%f\n", sys.zero1, sys.scale1, sys.zero2, sys.scale2);
}

void checkSensors() {

  if (sensor1.is_ready()) {
    valid |= 1;
    sys.readSensor1 = sensor1.read();
    sys.weight1 = (int)(sys.scale1 * (float)(sys.readSensor1 - sys.zero1));
    sys.weight = sys.weight1 + sys.weight2;
  }
  if (sensor2.is_ready()) {
    valid |= 2;
    sys.readSensor2 = sensor2.read();
    sys.weight2 = (int)(sys.scale2 * (float)(sys.readSensor2 - sys.zero2));
    sys.weight = sys.weight1 + sys.weight2;
  }

}
