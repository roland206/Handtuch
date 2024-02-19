#include "context.h"

#define BUFFER_SIZE 300
static char buffer[BUFFER_SIZE+2];

static int nChars;

void initHost() {
    nChars = 0;
}


void interpreteCmd(char *msg) {
  char cmd;
  
  while(*msg) {
    cmd = *(msg++);
    if (*(msg++) != ':') return;
    switch(cmd) {
    case  'M': sys.control  = atoi(msg); break;
    case  'T': sys.timeOffset = atoi(msg) - sys.epoch + sys.timeOffset; break;
    case  'P': sys.pumpeMaxOn = atoi(msg) * 1000; break;
    case  'p': sys.pumpeMinPause = atoi(msg) * 1000; break;
    case  'g': sys.wasserMarsch = atoi(msg); break;
    case  'G': sys.maxWeight = atoi(msg); break;
    case  'U': sys.weightUp = atoi(msg); break;
    case  'D': sys.weightDown = atoi(msg); break;
    case  'V': sys.tWater = atoi(msg)*1000; break;
    case  'v': sys.tWaterWait = atoi(msg)* 1000; break;
    case  'Z': sys.maxWaterCycles = atoi(msg); break;
    case  'A': sys.rampStopWeight = atoi(msg); break;
    case  'K': sys.timeRamp = atoi(msg) * 1000; break;
    case  'W': sys.timePause = atoi(msg) * 1000; break;
    case  'C': calibrateSensors(atoi(msg)); break;
    case  'X': cmdWater(atoi(msg)); break;
    case  'a': sys.zero1  = atoi(msg); break;
    case  'b': sys.scale1 = atof(msg); break;
    case  'c': sys.zero2  = atoi(msg); break;
    case  'd': sys.scale2 = atof(msg); break;
    case  'r': sys.ruheVon = atoi(msg); break;
    case  's': sys.ruheBis = atoi(msg); break;
    case  't': sys.ausVon  = atoi(msg); break;
    case  'u': sys.ausBis  = atoi(msg); break;
    case  'e': sys.enDebug = atoi(msg); break;
    case  'F': generateEvent(1); break;
    }
    while((*msg != ':') && (*msg))
      msg++;
    if (*msg == ':') msg++;
  }
}

void checkHost() { 

  while(Serial.available() > 0) {
      char cc = Serial.read();
      if (cc == '\n') {
          interpreteCmd(buffer) ;
          nChars = 0;
          return;
      }
      buffer[nChars++] = cc;
      buffer[nChars] = 0;
      if (nChars >= BUFFER_SIZE) nChars = BUFFER_SIZE - 1;
  }
}

void generateEvent(int forced) {

    static int lastState, lastTime, lastTemp, lastHum, lastWeight;
    int minT = 5, minTH = 500, minW = 100;

    if (sys.control & CTRL_HIGH_RES) {
        minT = 1; minTH = 100; minW = 10;
    }

    if (lastState!= sys.state) forced = 1;
    if ((sys.epoch - lastTime) > minT) {
        if (abs(lastTemp   - sys.temp1)     > minTH) forced = 1;
        if (abs(lastHum    - sys.humidity1) > minTH) forced = 1;
        if (abs(lastWeight - sys.weight)    >  minW) forced = 1;
    }
    if (forced == 0) return;
    lastState  = sys.state;
    lastTime   = sys.epoch;
    lastTemp   = sys.temp1;
    lastHum    = sys.humidity1;
     if (abs(lastWeight - sys.weight)    >  1000) {
        Serial.printf("sens1 %d, sens2 %d, w1 %d, w2 %d zeor1 %d, sc1 %f, z2 %d sc2 %f\n", sys.readSensor1, sys.readSensor1, sys.weight1, sys.weight2, sys.zero1, sys.scale1, sys.zero2, sys.scale2);
     }
    lastWeight = sys.weight;
    Serial.printf("W:%d:S:%d:T:%d:H:%d:G:%d:Z:%d\n",lastTime, lastState, lastTemp, lastHum, lastWeight, sys.wasserMarsch);
  
}

void sendDebugMSG(char *msg) {
    if (sys.enDebug <= 0) return;
    sys.enDebug--;
    Serial.printf("e:%s\n",msg);
}