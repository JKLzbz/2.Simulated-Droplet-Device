#include "WiFiReceive.h"
#include "usart.h"
#include "exti.h"


#define  RECV_DATA_MAX_SIZE  1024  //如果使用较大的数组，记得确保有足够大的系统堆栈来容纳这个大数组变量. 否则，单片机程序可能会因为堆栈溢出越界而跳入“hardware fault"系统异常
#define  ONEM_BYTE (1024*1024)   //1M字节的数据大小
extern u8  RecvData[];
u16 status = 0;//执行出错时，返回的状态码的指针，方便故障诊断
u8  link_no=0;//服务链接号，返回当前读取数据所来源的服务链接号
extern u32 totalreceived_length;//接收数据的总长度
extern u32 MBytes;

u16 ReceiveDataViaWiFi()//WIFI接收函数封装
{
  u16 received_length; //函数的返回值，为当前接收数据的长度
  received_length = M8266WIFI_SPI_RecvData(RecvData, RECV_DATA_MAX_SIZE, 5*1000, &link_no, &status);
	//如果WIFI模组当前所收到的TCP包的数据长度小于等于max_len时，该函数在读取了完毕这个TCP包后会立刻返回，此时在status里会返回0x0000。
	if( (status&0xFF)!= 0 )  
	{
		if((status&0xFF)==0x22)      //0x22:表示没有数据包
		{  
			M8266HostIf_delay_us(250); 
		}
		else if((status&0xFF)==0x23) //0x23:表示此次读取的数据片段需要接续前面读取得到的数据片段，去组成一个完整的TCP包，直到这个TCP包的数据片段全部读取完毕。
		{   												 //可以在这里做一些工作，比如将一次接收缓冲区和做大长度上限加大。
      printf("current receive data needs to continue with the data fragment earlier!");                           
		}
		else if((status&0xFF)==0x24)       
		{                            //0x24:模组所接收到而正在被读取的这个包的长度，超过了这里的max_len参数所指定的长度。通常是因为远端阵发发送或路由器等阻塞时出现了大面积粘包导致到达模块的包过长，
																 // 或者远端实际发送的就是一个长包，其长度超过了这里所指定的最大长度上限。如果是前者的原因，建议暂停远端TCP通信一段时间。如果是后者，建议加大max_len的数值或者
																 //不做任何处理，不做处理时，单片机侧这边接收到的长包会被拆成多个小包需要自行再次破解。
			printf("receive data length exceed max size!");//这里一般不会超过最大长度，因为上位机发送过来的数据长度很小，如果超过了，定义一个超过标志，然后主函数中继续加上接收数据函数即可。
		}
		else
		{
			printf("NO 0x22、0x23、0x24,please check further!");	 
			//(非0x22、0x23、0x24: 其他异常,需参考手册做进一步处理
		}
	}
	totalreceived_length += received_length;//计算总的接收长度
	if(totalreceived_length>=ONEM_BYTE){
		totalreceived_length = totalreceived_length%(ONEM_BYTE);
    MBytes++;//计算接收了多少Mbyte数据
	}
	return received_length;
}

int WIFIDataIn(u8* receive_data,u16 received_length)//对接收的数据进行解包：0xAA+0xFE+data(4字节)+checksum(1字节)，共7字节
{		  																							//上位机发送的判定结果也必须按照此协议
	int data;
	u8 receive_checksum;
	u8 checksum;
	if(received_length<7){
		printf("Error: Data length is too short\r\n");
		return -1;
	}
	if(receive_data[0]!=0xAA && receive_data[1]!=0xFE){
		printf("Error: Invalid frame headers\r\n");
		return -1;
	}
	memcpy(&data, receive_data + 2, sizeof(int));  // 从位置2开始读取4个字节的整数
	receive_checksum = RecvData[6];
	checksum = CalculateChecksum(RecvData,6);
	if (checksum != receive_checksum) {
		printf("Error: Checksum mismatch\n");
		return -1;
	}
	printf("Checksum valid, Received data: %d\n", data);
	return data;
}       
