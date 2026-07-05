#include "sys.h"
#include "usart.h"	
////////////////////////////////////////////////////////////////////////////////// 	 
//如果使用ucos,则包�下面的头文件即可.
#if SYSTEM_SUPPORT_OS
#include "includes.h"					//ucos 使用	  
#endif
//////////////////////////////////////////////////////////////////////////////////	 
//�程序�供�习使用，未经作者�可，不得用于其它任何用�
//ALIENTEK STM32F4探索者开发板
//串口1初�化		   
//正点原子@ALIENTEK
//��论坛:www.openedv.com
//�改日�:2014/6/10
//版本：V1.5
//版权�有，盗版必究�
//Copyright(C) 广州市星翼电子�技有限�� 2009-2019
//All rights reserved
//********************************************************************************
//V1.3�改�明 
//�持�应不同频率下的串口波特率�置.
//加入了�printf的支�
//增加了串口接收命令功�.
//�正了printf���字�丢失的bug
//V1.4�改�明
//1,�改串口初始化IO的bug
//2,�改了USART_RX_STA,使得串口�大接收字节数�2�14次方
//3,增加了USART_REC_LEN,用于定义串口�大允许接收的字节�(不大�2�14次方)
//4,�改了EN_USART1_RX的使能方�
//V1.5�改�明
//1,增加了�UCOSII的支�
////////////////////////////////////////////////////////////////////////////////// 	  
 

//////////////////////////////////////////////////////////////////
//加入以下代码,�持printf函数,而不�要�择use MicroLIB	  
#if 1
#pragma import(__use_no_semihosting)             
//标准库需要的�持函�                 
struct __FILE 
{ 
	int handle; 
}; 

FILE __stdout;       
//定义_sys_exit()以避免使用半主机模式    
void _sys_exit(int x) 
{ 
	x = x; 
} 
//重定义fputc函数 
int fputc(int ch, FILE *file)
{
	uint32_t timeout = 20000;
	while(((USART1->SR&0X40)==0) && timeout) timeout--;//带超时保护的等待，防�串口�就绪导致单片机�机   
	USART1->DR = (u8) ch;  
	return ch;
}
#endif
 
#if EN_USART1_RX   //如果使能了接�
//串口1��服务程序
//注意,读取USARTx->SR能避免莫名其妙的错�   	
u8 USART_RX_BUF[USART_REC_LEN];     //接收缓冲,��USART_REC_LEN�字节.
//接收状�
//bit15�	接收完成标志
//bit14�	接收�0x0d
//bit13~0�	接收到的有效字节数目
u16 USART_RX_STA=0;       //接收状�标�	

//初�化IO 串口1 
//bound:波特�
void Usart1Init(u32 bound){
   //GPIO�口�置
  GPIO_InitTypeDef GPIO_InitStructure;
	USART_InitTypeDef USART_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA,ENABLE); //使能GPIOA时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1,ENABLE);//使能USART1时钟
 
	//串口1对应引脚复用映射
	GPIO_PinAFConfig(GPIOA,GPIO_PinSource9,GPIO_AF_USART1); //GPIOA9复用为USART1
	GPIO_PinAFConfig(GPIOA,GPIO_PinSource10,GPIO_AF_USART1); //GPIOA10复用为USART1
	
	//USART1�口配�
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9 | GPIO_Pin_10; //GPIOA9与GPIOA10
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;//复用功能
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;	//速度50MHz
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP; //推挽复用输出
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP; //上拉
	GPIO_Init(GPIOA,&GPIO_InitStructure); //初�化PA9，PA10

   //USART1 初�化设置
	USART_InitStructure.USART_BaudRate = bound;//波特率�置
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;//字长�8位数�格式
	USART_InitStructure.USART_StopBits = USART_StopBits_1;//��停��
	USART_InitStructure.USART_Parity = USART_Parity_No;//无�偶校验�
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;//无硬件数�流控�
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;	//收发模式
  USART_Init(USART1, &USART_InitStructure); //初�化串口1
	
  USART_Cmd(USART1, ENABLE);  //使能串口1 
	
	//USART_ClearFlag(USART1, USART_FLAG_TC);
	
#if EN_USART1_RX	
	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);//��相关��

	//Usart1 NVIC 配置
  NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;//串口1��通道
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=3;//抢占优先�3
	NVIC_InitStructure.NVIC_IRQChannelSubPriority =3;		//子优先级3
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
	NVIC_Init(&NVIC_InitStructure);	//根据指定的参数初始化VIC寄存器�

#endif
}

//void CopeCmdData(unsigned char ucData);

void USART1_IRQHandler(void)                	//串口1��服务程序
{
	u8 Res;
#if SYSTEM_SUPPORT_OS 		//如果SYSTEM_SUPPORT_OS为真，则�要支持OS.
	OSIntEnter();    
#endif
	if(USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)  //接收��(接收到的数据必须�0x0d 0x0a结尾)
	{
		Res =USART_ReceiveData(USART1);//(USART1->DR);	//读取接收到的数据
//		CopeCmdData(Res);
		if((USART_RX_STA&0x8000)==0)//接收�完成
		{
			if(USART_RX_STA&0x4000)//接收到了0x0d
			{
				if(Res!=0x0a)USART_RX_STA=0;//接收错�,重新��
				else USART_RX_STA|=0x8000;	//接收完成� 
			}
			else //还没收到0X0D
			{	
				if(Res==0x0d)USART_RX_STA|=0x4000;
				else
				{
					USART_RX_BUF[USART_RX_STA&0X3FFF]=Res ;
					USART_RX_STA++;
					if(USART_RX_STA>(USART_REC_LEN-1))USART_RX_STA=0;//接收数据错�,重新�始接�	  
				}		 
			}
		}   		 
  } 
#if SYSTEM_SUPPORT_OS 	//如果SYSTEM_SUPPORT_OS为真，则�要支持OS.
	OSIntExit();  											 
#endif
} 
#endif	

 




// ���Ͷ��������ݿ�
void USART1_SendBinary(uint8_t *data, uint16_t len) {
    uint16_t i;
    for(i=0; i<len; i++) {
        while((USART1->SR&0X40)==0); // �ȴ����ͽ���
        USART1->DR = data[i];
    }
}

