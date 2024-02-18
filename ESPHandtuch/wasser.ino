#include "context.h"


#define WATER_STATE_OFF     0
#define WATER_STATE_STANDBY 1
#define WATER_STATE_FILL    2
#define WATER_STATE_WAIT    3
int waterState = 0;
static uint64_t waterTimer;

void initWasser() {
  setWater(0);
  waterState = WATER_STATE_OFF;
  sys.histerese = 500;
}

void flutWasser() {

    if (waterState == WATER_STATE_OFF) return;
    setWater(0);
    sys.wasserMarsch -= sys.weightDown;
    if (sys.wasserMarsch < 0){
      sys.wasserMarsch = 0;
      waterState = WATER_STATE_OFF;
    } else {
      waterState = WATER_STATE_WAIT;
    }
    waterTimer = sys.now + sys.timePause;
    setStatus(STATUS_MODE_RAMP, 0);
}

void cmdWater(int cmd) {

  waterState = (cmd != 0) ? WATER_STATE_STANDBY : WATER_STATE_OFF;
  setStatus(STATUS_MODE_RAMP, cmd == 1);

}

void checkWasser() {
    static int nCyclesToDo;
    static int flutHappened = 0;
    int ramp = sys.state & STATUS_MODE_RAMP;
    int stopWater = (sys.weight - sys.histerese) > sys.wasserMarsch;

    flutHappened |= sys.state & STATUS_FLUT;
    
    switch(waterState) {
      
      case WATER_STATE_OFF:
              waterCycler(0);
              break;
              
      case WATER_STATE_STANDBY:
              if (((sys.weight < sys.wasserMarsch)   && !ramp) ||
                  ((sys.weight < sys.rampStopWeight) &&  ramp)) {
                    waterState = WATER_STATE_FILL;
                    nCyclesToDo = sys.maxWaterCycles;
                    waterTimer = sys.now + sys.timeRamp;
                  }
              waterCycler(0);
              break;
              
      case WATER_STATE_FILL:
              nCyclesToDo -= waterCycler(1);
              if (ramp) {
                if (sys.weight > sys.rampStopWeight) stopWater = 2;
                if (sys.now > waterTimer) stopWater = 3;
              } else {
                if (nCyclesToDo <= 0)  stopWater = 1;
              }
              if (stopWater) {
                waterState = WATER_STATE_WAIT;
                setStatus(STATUS_MODE_RAMP, 0);
                waterTimer = sys.now + sys.timePause;
              }
              break;
      case WATER_STATE_WAIT:
              waterCycler(0);
              if (sys.state & STATUS_FLUT) waterTimer = sys.now + sys.timePause;
              if (sys.now < waterTimer) break;
              if (!flutHappened) sys.wasserMarsch  = min(sys.wasserMarsch + sys.weightUp, sys.maxWeight);
              waterState = WATER_STATE_STANDBY;
              break;
    }

    setStatus(STATUS_MODE_RUN,   waterState != WATER_STATE_OFF);
    setStatus(STATUS_MODE_WATER, waterState == WATER_STATE_FILL);
    setStatus(STATUS_MODE_WAIT,  waterState == WATER_STATE_WAIT);

}


int waterCycler(int mode) {
  static int cycleState = 0;
  static uint64_t cycleTimer;
  int cycleDone = 0;
  
  if (mode == 0) {
    cycleState = 0;
    setWater(0);
  } else {

      switch(cycleState) {
        case 0: cycleTimer = sys.now + sys.tWater;
                cycleState = 1;
                setWater(1);
        case 1: if (sys.now < cycleTimer) break;
                cycleTimer = sys.now + sys.tWaterWait;
                cycleState = 2;
                setWater(0);
                cycleDone = 1;
        case 2: if (sys.now >cycleTimer) cycleState = 0;
                break;
      }
  }
  return cycleDone;  
}
