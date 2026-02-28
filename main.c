// /*
//  * Copyright (c) 2016 Intel Corporation
//  *
//  * SPDX-License-Identifier: Apache-2.0
//  */



#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>
#include <logging/log_rpc.h>
#include <dk_buttons_and_leds.h>
#include "ble/ble.h"
#include <stdint.h>

/* ---------------------------------------------------------
 * I2C Setup
 * --------------------------------------------------------- */
#define I2C_NODE DT_NODELABEL(i2c1)
static const struct device *i2c_dev = DEVICE_DT_GET(I2C_NODE);

/* ---------------------------------------------------------
 * Seesaw Defines (Your original device)
 * --------------------------------------------------------- */
// #define STEMMAADDRESS      0x36
// #define BASEREGISTER       0x0F
// #define FUNCTIONREGISTER   0x10

/* ---------------------------------------------------------
 * MPU6050 Registers
 * --------------------------------------------------------- */
#define MPU6050_ADDR       0x68
#define MPU_PWR_MGMT_1     0x6B
#define MPU_ACCEL_XOUT_H   0x3B

/* BLE/IMU Value */
int16_t imu_buf[6] = {0};

/* ---------------------------------------------------------
 * MPU6050 Low-Level Write
 * --------------------------------------------------------- */
static int mpu6050_write_reg(uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = { reg, val };
    return i2c_write(i2c_dev, buf, 2, MPU6050_ADDR);
}

/* ---------------------------------------------------------
 * MPU6050 Init
 * --------------------------------------------------------- */
static void mpu6050_init(void)
{
    if (!device_is_ready(i2c_dev)) {
        printk("I2C not ready!\n");
        return;
    }

    int ret = mpu6050_write_reg(MPU_PWR_MGMT_1, 0x00); // Wake IMU
    printk("MPU6050 Init ret = %d\n", ret);
}

/* ---------------------------------------------------------
 * Full IMU Read (Accel + Gyro)
 * --------------------------------------------------------- */
static void mpu6050_read_all(void)
{
    int ret;
    uint8_t reg = MPU_ACCEL_XOUT_H;

    /* Select first register (Accel X High byte) */
    ret = i2c_write(i2c_dev, &reg, 1, MPU6050_ADDR);
    if (ret != 0) {
        printk("MPU reg select failed: %d\n", ret);
        imu_buf[6] = 420;
        return;
    }

    uint8_t data[14];
    ret = i2c_read(i2c_dev, data, 14, MPU6050_ADDR);
    if (ret != 0) {
        printk("MPU read failed: %d\n", ret);
        imu_buf[6] = 420;
        return;
    }

/* Parse accelerometer */
int16_t ax = (data[0] << 8) | data[1];
int16_t ay = (data[2] << 8) | data[3];
int16_t az = (data[4] << 8) | data[5];

/* Parse gyroscope */
int16_t gx = (data[8]  << 8) | data[9];
int16_t gy = (data[10] << 8) | data[11];
int16_t gz = (data[12] << 8) | data[13];

/* Convert to real units (scaled x1000 to avoid floats) */
/* Convert to real units (scaled x1000) */
int32_t ax_g = (int32_t)ax * 1000 / 16384;
int32_t ay_g = (int32_t)ay * 1000 / 16384;
int32_t az_g = (int32_t)az * 1000 / 16384;

int32_t gx_dps = (int32_t)gx * 1000 / 131;
int32_t gy_dps = (int32_t)gy * 1000 / 131;
int32_t gz_dps = (int32_t)gz * 1000 / 131;

printk("ACC(g): %d.%03d %d.%03d %d.%03d | GYRO(dps): %d.%03d %d.%03d %d.%03d\n",
       ax_g / 1000, abs(ax_g % 1000),
       ay_g / 1000, abs(ay_g % 1000),
       az_g / 1000, abs(az_g % 1000),
       gx_dps / 1000, abs(gx_dps % 1000),
       gy_dps / 1000, abs(gy_dps % 1000),
       gz_dps / 1000, abs(gz_dps % 1000));

/* You still send "imu_buf[6]" to BLE */
uint32_t mag = abs(ax) + abs(ay) + abs(az);
imu_buf[0] = (int16_t)(ax * 1000 / 16384);
imu_buf[1] = (int16_t)(ay * 1000 / 16384);
imu_buf[2] = (int16_t)(az * 1000 / 16384);
imu_buf[3] = (int16_t)(gx * 1000 / 131);
imu_buf[4] = (int16_t)(gy * 1000 / 131);
imu_buf[5] = (int16_t)(gz * 1000 / 131);
}

/* ---------------------------------------------------------
 * I2C Bus Scanner (your original)
 * --------------------------------------------------------- */
void scan_i2c_bus(const struct device *dev)
{
    printk("Starting I2C scan...\n");
    for (uint8_t addr = 0x03; addr <= 0x77; addr++) {
        if (i2c_write(dev, NULL, 0, addr) == 0) {
            printk("Device found at 0x%02X\n", addr);
        }
    }
    printk("I2C scan done\n");
}

/* ---------------------------------------------------------
 * MAIN LOOP
 * --------------------------------------------------------- */
int main(void)
{
    int ret;

    ble_init();
    mpu6050_init();

    scan_i2c_bus(i2c_dev);

    if (!device_is_ready(i2c_dev)) {
        printk("i2c_dev not ready\n");
    }

    while (1) {

        /* Read MPU6050 accelerometer + gyro */
        mpu6050_read_all();
		
		
		ble_notify_imu();   // replaces ble_notify_capacitance()


        k_sleep(K_MSEC(150));
    }

    return 0;
}
