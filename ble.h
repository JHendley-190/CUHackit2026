#ifndef BLE_H
#define BLE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <zephyr/types.h>


// Custom UUID: C42D5A1B-D4D4-45B7-AC3A-945929C7A758

// We need a service UUID and a characteristic UUID

// Data Service UUID
//#define BT_UUID_DATA_SERVICE_VAL BT_UUID_128_ENCODE(0x00001523, 0x1212, 0xefde, 0x1523, 0x785feabcd123) NORDIC

#define BT_UUID_DATA_SERVICE_VAL BT_UUID_128_ENCODE(0x4998E78C, 0x5B56, 0x4D31, 0xBAA0, 0xB46EDDC6E573)

// converts the raw UUID format into a type useable by GATT opeations (Final MACRO)
#define BT_UUID_DATA_SERVICE  BT_UUID_DECLARE_128(BT_UUID_DATA_SERVICE_VAL)

// Capactitance Characteristic UUID
#define BT_UUID_IMU_CHARACTERISTIC_VAL BT_UUID_128_ENCODE(0x861a4d03, 0x44e2, 0x4877, 0x8557, 0x671e08abb546) 

#define BT_UUID_IMU_CHARACTERISTIC 	BT_UUID_DECLARE_128(BT_UUID_IMU_CHARACTERISTIC_VAL)




    
// Initializes BLE stack and services
int ble_init(void);
//void ble_notify_capacitance(void);
extern int16_t imu_buf[6];
void ble_notify_imu(void);

// You can add other service APIs here, like for battery level, status, etc.

#ifdef __cplusplus
}
#endif

#endif // BLE_H
