#include "context.h"
#include <DHT.h>

#define BUFFER_SIZE 16
typedef struct  {int n; float data[BUFFER_SIZE]; float mean;} Buffer;

DHT dht1(DHT_PIN1, DHT22);
Buffer temp1_Buffer, hum1_Buffer;

#ifdef DHT_PIN2
DHT dht2(DHT_PIN2, DHT22);
Buffer temp2_Buffer, hum2_Buffer;
#endif


static void insertData(Buffer *buf, float data);
static void calcMean(Buffer *buf);

static void calcMean(Buffer *buf) {

  float ym = 0;
  float weight  = 1;
  float wSum = 0.0;

  if (buf->n <1) {
    buf->mean = 0;
    return;
  }
  for(int i=0; i<buf->n; i++){
    ym += weight * buf->data[i];
    wSum += weight;
    weight += 1.0;
  }

  buf->mean = ym / wSum;
  #ifdef DEBUG
    Serial.printf("New mean %5.2f\n", buf->mean);
  #endif
}

static void insertData(Buffer *buf, float data)
{
  if (buf->n < BUFFER_SIZE) {
    buf->data[buf->n] = data;
    buf->n++;
  } else {

    float *src = buf->data;
    for(int i=0; i< (BUFFER_SIZE - 1); i++) {
      *src = *(src+1);
      src++;
    }
    *src = data;
  }
  calcMean(buf);
}

///////////////////////////////////////////////////////////////////////////////////////////
void initTempSensors() {

  dht1.begin();
  temp1_Buffer.n = hum1_Buffer.n = 0;

#ifdef DHT_PIN2
  dht2.begin();
  temp2_Buffer.n = hum2_Buffer.n = 0;
#endif

}

/////////////////////////////////////////////////////////////////////////////////////////////
void readTempSensors() {

  insertData(&hum1_Buffer,  dht1.readHumidity());
  insertData(&temp1_Buffer, dht1.readTemperature());
  sys.temp1 = (int)(1000 * temp1_Buffer.mean);
  sys.humidity1 = (int)(1000 * hum1_Buffer.mean);

#ifdef DHT_PIN2
  insertData(&hum2_Buffer,  dht2.readHumidity());
  insertData(&temp2_Buffer, dht2.readTemperature());
  sys.temp2 = (int)(1000 * temp2_Buffer.mean);
  sys.humidity2 = (int)(1000 * hum2_Buffer.mean);
#endif
}
