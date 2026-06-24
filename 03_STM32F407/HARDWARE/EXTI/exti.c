#include "exti.h"
#include "WiFiReceive.h"


#define  RECV_DATA_MAX_SIZE  1024  //如果使用较大的数组，记得确保有足够大的系统堆栈来容纳这个大数组变量. 否则，单片机程序可能会因为堆栈溢出越界而跳入“hardware fault"系统异常
u8  RecvData[RECV_DATA_MAX_SIZE];
u16 received_length = 0; //函数的返回值，为当前接收数据的长度
u32 totalreceived_length = 0;//接收数据的总长度
u32 MBytes = 0;
extern int recognize_result;
	 
void WIFI_INT_Init(){
	GPIO_InitTypeDef  GPIO_InitStructure;
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);//使能GPIOC时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4; //WIFI_INT对应引脚
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN;//普通输入模式
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;//50M
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_DOWN ;//下拉
	GPIO_Init(GPIOC, &GPIO_InitStructure);//初始化GPIOC4
}

//外部中断初始化程序
void EXTIX_Init(void)
{
	NVIC_InitTypeDef   NVIC_InitStructure;
	EXTI_InitTypeDef   EXTI_InitStructure;

	WIFI_INT_Init(); //WIFI_INT_IO口初始化

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_SYSCFG, ENABLE);//使能SYSCFG时钟
	SYSCFG_EXTILineConfig(EXTI_PortSourceGPIOC, EXTI_PinSource4);//PC4 连接到中断线4

	/* 配置EXTI_Line4 */
	EXTI_InitStructure.EXTI_Line = EXTI_Line4;
	EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;//中断事件
	EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising; //上降沿触发
	EXTI_InitStructure.EXTI_LineCmd = ENABLE;//中断线使能
	EXTI_Init(&EXTI_InitStructure);//配置

	NVIC_InitStructure.NVIC_IRQChannel = EXTI4_IRQn;//外部中断4
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0x01;//抢占优先级1
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0x01;//子优先级2
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;//使能外部中断通道
	NVIC_Init(&NVIC_InitStructure);//配置
}

//外部中断4服务程序
void EXTI4_IRQHandler(void)
{
	u16 received_length;
	if(EXTI_GetITStatus(EXTI_Line4)!=RESET){//判断某个线上的中断是否发生
		received_length=ReceiveDataViaWiFi();
		recognize_result = WIFIDataIn(RecvData,received_length);
	}
	 EXTI_ClearITPendingBit(EXTI_Line4);//清除LINE4上的中断标志位
}

