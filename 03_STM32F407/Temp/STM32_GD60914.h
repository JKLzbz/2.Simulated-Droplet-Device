#ifndef STM32_GD60914_H
#define STM32_GD60914_H

#include "sys.h"
#include "usart.h"
#include "delay.h"
#include "stm32f4xx.h"
#define ACK	 0
#define	NACK 1

#define SMBUS_PORT	    GPIOB
#define SMBUS_SCK		GPIO_Pin_8
#define SMBUS_SDA		GPIO_Pin_9

#define RCC_AHB1Periph_SMBUS_PORT	RCC_AHB1Periph_GPIOB

#define SMBUS_SCK_H()	    SMBUS_PORT->BSRRL = SMBUS_SCK
#define SMBUS_SCK_L()	    SMBUS_PORT->BSRRH = SMBUS_SCK
#define SMBUS_SDA_H()	    SMBUS_PORT->BSRRL = SMBUS_SDA
#define SMBUS_SDA_L()	    SMBUS_PORT->BSRRH = SMBUS_SDA

#define SMBUS_SDA_PIN()	    SMBUS_PORT->IDR & SMBUS_SDA //读取引脚电平

void SMBus_Init(void);
void SMBus_StartBit(void);
void SMBus_StopBit(void);
u8 SMBus_SendByte(u8 Tx_buffer);
void SMBus_SendBit(u8 bit_out);
u8 SMBus_ReceiveBit(void);
u8 SMBus_ReceiveByte(u8 ack_nack);
void SMBus_Delay(u16 time);
s16 tempe_read(uint16_t reg);
s16 GD60914_ReadTemp(void);
#endif
