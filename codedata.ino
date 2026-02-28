#include <Wire.h>

const uint8_t MPU_ADDR = 0x68;
#define ACCEL_XOUT_H 0x3B
#define TEMP_OUT_H   0x41
#define GYRO_XOUT_H  0x43
#define PWR_MGMT_1   0x6B

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(100);

  // wake up sensor
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(PWR_MGMT_1);
  Wire.write(0);
  Wire.endTransmission();

  // CSV header
  Serial.println("t_ms,ax_g,ay_g,az_g,gx_deg_s,gy_deg_s,gz_deg_s,temp_C");
}

int16_t read16(uint8_t reg) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)2);
  int16_t val = 0;
  if (Wire.available() >= 2) {
    val = (Wire.read() << 8) | Wire.read();
  }
  return val;
}

unsigned long lastMillis = 0;

void loop() {
  unsigned long t = millis();

  int16_t ax = read16(ACCEL_XOUT_H);
  int16_t ay = read16(ACCEL_XOUT_H + 2);
  int16_t az = read16(ACCEL_XOUT_H + 4);

  int16_t tempRaw = read16(TEMP_OUT_H);

  int16_t gx = read16(GYRO_XOUT_H);
  int16_t gy = read16(GYRO_XOUT_H + 2);
  int16_t gz = read16(GYRO_XOUT_H + 4);

  float ax_g = ax / 16384.0;
  float ay_g = ay / 16384.0;
  float az_g = az / 16384.0;

  float gx_dps = gx / 131.0;
  float gy_dps = gy / 131.0;
  float gz_dps = gz / 131.0;

  float tempC = (tempRaw / 340.0) + 36.53;

  // CSV row
  Serial.print(t); Serial.print(',');
  Serial.print(ax_g, 4); Serial.print(',');
  Serial.print(ay_g, 4); Serial.print(',');
  Serial.print(az_g, 4); Serial.print(',');
  Serial.print(gx_dps, 3); Serial.print(',');
  Serial.print(gy_dps, 3); Serial.print(',');
  Serial.print(gz_dps, 3); Serial.print(',');
  Serial.println(tempC, 2);

  // control sample rate (adjust delay as needed)
  delay(17); // ~10 Hz
}