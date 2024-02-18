#include "context.h"


#define STATE_STANDBY 0
#define STATE_ON 1
#define CTRL_P_MODE_OFF        0x00         
#define CTRL_P_MODE_ON         0x01         
#define CTRL_P_MODE_AUTO       0x02
#define CTRL_P_MODE_MASK       (CTRL_P_MODE_ON | CTRL_P_MODE_AUTO)

static int state = STATE_STANDBY;
static uint64_t timer = 0;


void initPumpe() {
  
    sys.pumpeMaxOn = 15000;
    sys.pumpeMinPause = 5000;
    timer = 0;
    state = STATE_STANDBY;
}


void checkPumpe() {

    int pMode = sys.control & CTRL_P_MODE_MASK;
    int flut = getFlut();
    
    if (pMode == CTRL_P_MODE_OFF) {
          setPumpe(0);
          state = STATE_STANDBY;
          timer = 0;
    } else {
        switch(state) {
          case STATE_STANDBY:   if (sys.now < timer) break;
                                if ((pMode == CTRL_P_MODE_ON) || ((pMode == CTRL_P_MODE_AUTO) && flut)){
                                    state = STATE_ON;
                                } else break;
                                timer = sys.now + sys.pumpeMaxOn;
                                setPumpe(1);
         case STATE_ON:         if (sys.now < timer) break;
                                setPumpe(0);
                                timer = sys.now + sys.pumpeMinPause;
                                state = STATE_STANDBY;
                                break;
        }
    }
  return;
}
