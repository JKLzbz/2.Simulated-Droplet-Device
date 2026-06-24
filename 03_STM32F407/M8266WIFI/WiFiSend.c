#include "WiFiSend.h"

void SendDataViaWiFi(float send_data[256]){
    volatile u32 sent = 0;
    u16 tcp_packet_size = 1024;
    u16 loops = 0;
    u16 max_loops = 5000;
    u32 len = 256*sizeof(float);
    u16 status;
    for(sent=0, loops=0; (sent<len)&&(loops<=max_loops); loops++)
    {       
        sent+=M8266WIFI_SPI_Send_Data((u8 *)send_data+sent, ((len-sent)>tcp_packet_size)?tcp_packet_size:(len-sent), 0, &status);
        if(sent>=len)  break;
        if( (status&0xFF) == 0x00)
        {
            loops = 0;
        }
        else
        {
            if(((status&0xFF) == 0x14)                     // 0x14 = connection of link_no not present (Chinese: 该套接字不存在)
            || ((status&0xFF) == 0x15))                    // 0x15 = connection of link_no closed(Chinese: 该套接字已经关闭或断开)
            {
                M8266HostIf_delay_us(99);
                //need to re-establish the socket connection (Chinese: 需要重建建立套接字)
            }
            else if((status&0xFF) == 0x18)                 // 0x18 = TCP server in listening states and no tcp clients have connected. (Chinese: 这个TCP服务器还没有客户端连接着它)
            {
                M8266HostIf_delay_us(100);
            }
             else
            {
                M8266HostIf_delay_us(250);
            }
        }
    }            
}

u8 SendBufferViaWiFi(u8 *data, u32 len){
	volatile u32 sent = 0;
    u16 tcp_packet_size = 1024;//每个包的最大大小
    u16 loops = 0;
    u16 max_loops = 40;  // 批处理模式下每50ms才发送一次，允许最高阻塞40*250us=10ms，避免因模块偶尔忙碌而丢弃整个批次
    u16 status;
	for (sent = 0, loops = 0; (sent < len) && (loops <= max_loops); loops++) {
        // 计算当前发送的数据长度，最多发送tcp_packet_size大小的数据((len - sent) > tcp_packet_size) ? tcp_packet_size : (len - sent)
        // 调用 M8266WIFI_SPI_Send_Data 发送数据
        sent += M8266WIFI_SPI_Send_Data(data + sent, ((len - sent) > tcp_packet_size) ? tcp_packet_size : (len - sent), 0, &status);
        if (sent >= len) break;
        // 根据status判断是否发送成功，或者套接字处于什么状态
        if ((status & 0xFF) == 0x00) {
            loops = 0;  // 发送成功，重置重试次数
        }
		else{
            // 如果发送失败，检查特定的错误码
            if (((status & 0xFF) == 0x14) || ((status & 0xFF) == 0x15)) {
                // 连接不存在或连接关闭，需要重新建立套接字
                M8266HostIf_delay_us(99);
                // 需要重新建立连接
            } else if ((status & 0xFF) == 0x18) {
                // TCP发送缓冲区满，等待片刻后重试
                M8266HostIf_delay_us(99);
            }
             else
            {
                M8266HostIf_delay_us(250);
            }
        }
    }
    return (sent >= len) ? 1 : 0;
}

u8 CalculateChecksum(u8 *data, uint32_t len)//校验和计算
{
    uint32_t i;
    u8 ucCheck = 0;
    for(i=0; i<len; i++) ucCheck += *(data + i);
    return ucCheck;
}

void StructData_Send(WifiDataPacket *send_data){
	//计算校验和
    u8 data_for_crc[sizeof(WifiDataPacket) - 1]; // 去掉校验和字节
	memcpy(data_for_crc, send_data, sizeof(WifiDataPacket) - 1);
	send_data->checksum = CalculateChecksum(data_for_crc,sizeof(data_for_crc));
	//发送结构体数据
	SendBufferViaWiFi((u8*)send_data, sizeof(WifiDataPacket));
}
