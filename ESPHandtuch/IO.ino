#include "context.h"


void initIO() {
  
      pinMode(FAN_1_PIN, OUTPUT);
      pinMode(FAN_2_PIN, OUTPUT);
      pinMode(WATER_PIN, OUTPUT);
      pinMode(UVC_PIN, OUTPUT);
      pinMode(PUMPE_PIN, OUTPUT);
      pinMode(FLUT_PIN, INPUT_PULLUP);
      
      digitalWrite(FAN_1_PIN, 1);
      digitalWrite(FAN_2_PIN, 1);
      digitalWrite(WATER_PIN, 1);
      digitalWrite(UVC_PIN, 1);
      setWater(0);
      setPumpe(0);
}

int checkRuhe(int von, int bis) {
// +60 for local time vs London time
  int minToday = (int(sys.epoch/60) % (24*60)) + 60;

  if ((minToday < von) || (minToday >= bis)) return 0;
  return 1;
}

void setRelais() {
    int fanRuhe = checkRuhe(sys.ruheVon, sys.ruheBis);
    int UVCaus  = checkRuhe(sys.ausVon,  sys.ausBis);
    
    if (sys.control & CTRL_FAN1_AUTO)
       digitalWrite(FAN_1_PIN, fanRuhe);
    else 
       digitalWrite(FAN_1_PIN, (sys.control & CTRL_FAN1)  == 0);
       
    if (sys.control & CTRL_FAN2_AUTO)
       digitalWrite(FAN_2_PIN, fanRuhe);
    else 
       digitalWrite(FAN_2_PIN, (sys.control & CTRL_FAN2)  == 0);
       
    if (sys.control & CTRL_UVC_AUTO)
       digitalWrite(UVC_PIN, UVCaus);
    else 
       digitalWrite(UVC_PIN, (sys.control & CTRL_UVC)  == 0);
    

      setStatus(STATUS_FAN1, digitalRead(FAN_1_PIN) == 0);
      setStatus(STATUS_FAN2, digitalRead(FAN_2_PIN) == 0);
      setStatus(STATUS_UVC,  digitalRead(UVC_PIN)   == 0);
}

void setStatus(int mask, int value) {
  if (value)
    sys.state |= mask;
  else
    sys.state &= ~mask;
    
}

static uint64_t flutDebounce = 0;
int getFlut() {
  
    int last = (sys.state & STATUS_FLUT) != 0;

    if (sys.now < flutDebounce) return last;
    
    int flutPin = digitalRead(FLUT_PIN) == 0;
    if (flutPin != last) {
        flutDebounce = sys.now + 500;
        if (flutPin) flutWasser();
     }
    setStatus(STATUS_FLUT, flutPin);
    return flutPin;
}

void setPumpe(int state) {
  setStatus(STATUS_PUMPE, state);
  digitalWrite(PUMPE_PIN, state != 0);
}

void setWater(int state) {
  setStatus(STATUS_WATER, state);
  digitalWrite(WATER_PIN, state == 0);
}
