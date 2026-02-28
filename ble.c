

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <dk_buttons_and_leds.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <stdint.h>
#include <zephyr/sys/printk.h>
#include "ble.h"

// this is needed for logging purposes
LOG_MODULE_REGISTER(ble, LOG_LEVEL_INF);

// // // Unique Company Identifier
// // #define COMPANY_CODE 0xFFFF // its test/reserved
static uint16_t manufacturer_code = 0xFFFF;



// May not even need the param function as there already is a API for speed: BT_LE_ADV_CONN_FAST_2

/* STEP 1 - Create an LE Advertising Parameters variable */
static const struct bt_le_adv_param *adv_param = BT_LE_ADV_PARAM(
		(BT_LE_ADV_OPT_CONNECTABLE |
	 BT_LE_ADV_OPT_USE_IDENTITY), /* Connectable advertising and use identity address */
			120, /* Min Advertising Interval 100ms */
			448, /* Max Advertising Interval 500.625ms (801*0.625ms) */
			NULL); /* Set to NULL for undirected advertising */



// // look at ble documentation but 0x17 coicides with https:
// static unsigned char url_data[] = {
//     0x17, // 25 bytes follow
//     '/','/',
//     'g','i','t','h','u','b','.','c','o','m',
//     '/','M','i','c','h','a','e','l','-','R','o','s','o','l'
// };

#define DEVICE_NAME CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)




#define RUN_STATUS_LED DK_LED1
#define RUN_LED_BLINK_INTERVAL 1000
#define NOTIFY_INTERVAL 500
#define CONNECTED_LED DK_LED2 


static struct k_work adv_work;


static const struct bt_data advertising[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)), //flag
	BT_DATA(BT_DATA_NAME_COMPLETE, DEVICE_NAME, DEVICE_NAME_LEN),
	/* STEP 3 - Include the Manufacturer Specific Data in the advertising packet. */
	BT_DATA(BT_DATA_MANUFACTURER_DATA, (unsigned char *)&manufacturer_code, sizeof(manufacturer_code)),
	//BT_DATA()




};

// static const struct bt_data scanning[] = {
// 	BT_DATA(BT_DATA_URI, url_data, sizeof(url_data)),
// };



static void adv_work_handler(struct k_work *work)
{
	// int err = bt_le_adv_start(adv_param, advertising, ARRAY_SIZE(advertising), scanning, ARRAY_SIZE(scanning));
	int err = bt_le_adv_start(adv_param, advertising, ARRAY_SIZE(advertising), NULL, 0);

	if (err) {
		printk("Advertising failed to start (err %d)\n", err);
		return;
	}

	printk("Advertising successfully started\n");
}
static void advertising_start(void)
{
	k_work_submit(&adv_work);
}
static void recycled_cb(void)
{
	printk("Connection object available from previous conn. Disconnect is complete!\n");
	advertising_start();
}

// Connection Process 

 // we set a led on the TR pos for connection
static void peripheral_connected(struct bt_conn *conn, uint8_t err) {
	if (err) {
		printk("Connection failed (err %u)\n", err);
		return;
	}

	bt_conn_set_security(conn, BT_SECURITY_L0);  // no encryption or authentication for now, we can change this later to increase security

	printk("Connected\n");

	dk_set_led_on(CONNECTED_LED); 
}

 static void peripheral_disconnected(struct bt_conn *conn, uint8_t reason) {

		printk("Disconnected (reason %u)\n", reason);

		dk_set_led_off(CONNECTED_LED);
 }


 /* STEP 5.2 Define the callback function security_changed() */
static void on_security_changed(struct bt_conn *conn, bt_security_t level, enum bt_security_err err)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

	if (!err) {
		LOG_INF("Security changed: %s level %u\n", addr, level);
	} else {
		LOG_INF("Security failed: %s level %u err %d\n", addr, level, err);
	}
}



 struct bt_conn_cb connection_callbacks = {
	.connected = peripheral_connected,
	.disconnected = peripheral_disconnected,
	.recycled = recycled_cb,
	.security_changed = on_security_changed,
};




// GATT Functionality 

//extern uint16_t capacitance; 

static bool notify_imu;

//static bool notify_capacitanceSensor;

static void imu_changed(const struct bt_gatt_attr * attr, uint16_t value) {

	notify_imu = ( value == BT_GATT_CCC_NOTIFY); // boolean value 
}


static ssize_t read_imu ( struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf,
			   uint16_t len, uint16_t offset) 
			  { 
						
					// get a pointer to button_state which is passed in the BT_GATT_CHARACTERISTIC() and stored in attr->user_data
					const uint16_t *value = attr->user_data;


					return bt_gatt_attr_read(conn, attr, buf, len, offset, value, sizeof(*value));


			   }



BT_GATT_SERVICE_DEFINE(data_svc,

	BT_GATT_PRIMARY_SERVICE(BT_UUID_DATA_SERVICE),


	// the CHRC READ - Reads the characteristic in this case the sensor
	BT_GATT_CHARACTERISTIC(BT_UUID_IMU_CHARACTERISTIC,  BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY, BT_GATT_PERM_READ , read_imu, NULL, imu_buf), 


	// a client characteristic configuration is used to enable notifications
	BT_GATT_CCC(imu_changed,BT_GATT_PERM_READ | BT_GATT_PERM_WRITE)
); 

// actual ble notify function 
void ble_notify_imu(void)
{
    if (!notify_imu) return;

    int err = bt_gatt_notify(NULL, &data_svc.attrs[2], imu_buf, sizeof(imu_buf));
    if (err) {
        printk("IMU notify failed: %d\n", err);
    }
}


int ble_init(void)
{
	
	int err;



	err = dk_leds_init();
	if (err) {
		LOG_ERR("LEDs init failed (err %d)\n", err);
		return -1;
	}

	// enable bluetooth call 
	err = bt_enable(NULL);
	if (err) {
		LOG_ERR("Bluetooth init failed (err %d)\n", err);
		return -1;
	}

	LOG_INF("Bluetooth initialized\n");



	// connection callback initalization
	bt_conn_cb_register(&connection_callbacks);


	// advertising parameter callback
	k_work_init(&adv_work, adv_work_handler);
	advertising_start();
	

	LOG_INF("Advertising successfully started\n");



	return 0; 
}
