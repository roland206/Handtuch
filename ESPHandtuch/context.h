#ifndef CONTEXT_H
#define CONTEXT_H

#define FAN_1_PIN 19
#define FAN_2_PIN 18
#define WATER_PIN 17
#define UVC_PIN   16
#define SDA1_PIN  21
#define SCL1_PIN  22
#define SDA2_PIN  23
#define SCL2_PIN  25
#define FLUT_PIN  14
#define PUMPE_PIN 26

#define DHT_PIN2x  33
#define DHT_PIN1   33

#define CTRL_P_MODE_OFF       0x00         

#define CTRL_P_MODE_ON        0x01         
#define CTRL_P_MODE_AUTO      0x02
#define CTRL_P_MODE_MASK       (CTRL_P_MODE_ON | CTRL_P_MODE_AUTO)
#define CTRL_FAN1             0x04
#define CTRL_FAN1_AUTO        0x08
#define CTRL_FAN2             0x10
#define CTRL_FAN2_AUTO        0x20
#define CTRL_UVC              0x40
#define CTRL_UVC_AUTO         0x80
#define CTRL_MODE_RAMP        0x100
#define CTRL_MODE_ON          0x200
#define CTRL_HIGH_RES         0x400

#define STATUS_WATER          0x01
#define STATUS_PUMPE          0x02
#define STATUS_FAN1           0x04
#define STATUS_FAN2           0x08
#define STATUS_UVC            0x10
#define STATUS_MODE_RAMP      0x20
#define STATUS_MODE_RUN       0x40
#define STATUS_MODE_WATER     0x80
#define STATUS_MODE_WAIT     0x100
#define STATUS_FLUT          0x200

typedef struct System {
  int   pumpeMaxOn, pumpeMinPause;   // Pumpen control
  int   readSensor1, readSensor2, weight, weight1, weight2, zero1, zero2, temp1, humidity1, temp2, humidity2;
  float scale1, scale2;
  int   rampStopWeight, wasserMarsch;
  int   maxWeight, weightUp, weightDown, timeRamp, histerese;
  int   maxWaterCycles, tWater, tWaterWait, timePause;
  int   control, state, timeOffset, epoch, enDebug;
  int   ruheVon, ruheBis, ausVon, ausBis;
  uint64_t now;
};
























#endif
