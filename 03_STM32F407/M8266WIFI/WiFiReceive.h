#include "stdint.h"
#include "stdbool.h"
#include "sys.h"
#include "WiFiSend.h"
#include "M8266HostIf.h"
#include "M8266WIFIDrv.h"
#include "M8266WIFI_ops.h"
#include "brd_cfg.h"

u16 ReceiveDataViaWiFi(void);//WIFI接收函数封装
int WIFIDataIn(u8* receive_data,u16 received_length);//对接收的数据进行解包

