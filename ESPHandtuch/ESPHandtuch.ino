#include "context.h"

System sys;

void initIO();
void initPumpe();
void initSensors();
void initTempSensors();
void initWasser();
void initHost();

void readTempSensors();
void checkPumpe();
void checkSensors();
void checkWasser();
void setRelais();
void generateEvent();
void checkHost();

void setStatus(int mask, int value);
void setPumpe(int state);
void setWater(int state);
void flutWasser();

void setup() {
    Serial.begin(115200);
    delay(400);

    initIO();
    initPumpe();
    initSensors();
    initTempSensors();
    initWasser();
    initHost();
    sys.timeOffset = 1234;
    Serial.printf("ESP booted");
}


void loop() {
    static int nextTemp = 0;
    
    sys.now   = millis();
    sys.epoch = (int)(sys.now / 1000) + sys.timeOffset;

    if (sys.now > nextTemp) {
      nextTemp = sys.now + 50000;
      readTempSensors();
    }

    checkPumpe();
    checkSensors();
    checkWasser();
    setRelais();
    generateEvent(0);
    checkHost();
 }
