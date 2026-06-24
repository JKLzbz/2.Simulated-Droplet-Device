#ifndef __WIFISEND_H
#define __WIFISEND_H
#include "stdio.h"
#include "string.h"
#include "stdint.h"
#include "stdbool.h"
#include "sys.h"
#include "M8266HostIf.h"
#include "M8266WIFIDrv.h"
#include "M8266WIFI_ops.h"
#include "brd_cfg.h"

//指定操作系统对其数为1个字节，不浪费存储空间，节约传输带宽
#pragma pack(1) //操作系统32位（最大对齐数为4字节，对于double类型变量占2个最大对齐数），如果不加该语句下面的结构体占40个字节，及header1和header2总共4字节（空2字节），droplet：4字节，distance：4字节（空2字节），sum_acc：4+4字节，sum_gyro:4+4字节，temp:4字节，check:4字节（空3字节）
//协议头和协议结构
typedef struct {
    u8 header1;   		// 协议帧头1为0xAA
		u8 header2;			  // 协议帧头2为0xFF(5维传感器数据:1维飞沫+1维距离+1维合加速度+1维合角速度+1维温度)
    float droplet;    // droplet电容值
		u16  distance;		// 距离值
		float temp;       // 温度值
    u8 checksum; // 校验和
} WifiDataPacket;

void SendDataViaWiFi(float send_data[256]);//老版本的数据发送，不可靠
u8 SendBufferViaWiFi(u8 *data, u32 len);//WIFI发送函数封装
u8 CalculateChecksum(u8 *data, uint32_t len);//校验和计算
void StructData_Send(WifiDataPacket *send_data);////WIFI发送函数
#endif
