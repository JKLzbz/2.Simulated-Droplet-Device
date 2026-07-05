#ifndef __USART_H
#define __USART_H
#include "stdio.h"	
#include "stm32f4xx_conf.h"
#include "sys.h" 
//////////////////////////////////////////////////////////////////////////////////	 
//�程序�供�习使用，未经作者�可，不得用于其它任何用�
//Mini STM32�发板
//串口1初�化		   
//正点原子@ALIENTEK
//��论坛:www.openedv.csom
//�改日�:2011/6/14
//版本：V1.4
//版权�有，盗版必究�
//Copyright(C) 正点原子 2009-2019
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
////////////////////////////////////////////////////////////////////////////////// 	
#define USART_REC_LEN  			200  	//定义�大接收字节数 200
#define EN_USART1_RX 			1		//使能�1�/禁��0）串�1接收
	  	
extern u8  USART_RX_BUF[USART_REC_LEN]; //接收缓冲,��USART_REC_LEN�字节.�字节为换行� 
extern u16 USART_RX_STA;         		//接收状�标�	
//如果想串口中�接收，�不要注释以下宏定义
void Usart1Init(u32 bound);
void USART1_SendBinary(uint8_t *data, uint16_t len);
#endif


