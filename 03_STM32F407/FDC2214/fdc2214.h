#ifndef __FDC2214_H
#define __FDC2214_H
#include "sys.h"
//IO方向设置
#define FDC_SDA_IN()  {GPIOB->MODER&=~(3<<(11*2));GPIOB->MODER|=0<<11*2;delay_us(2);}//PB11输入模式
#define FDC_SDA_OUT() {GPIOB->MODER&=~(3<<(11*2));GPIOB->MODER|=1<<11*2;delay_us(2);}//PB11输出模式

#define FDC_IIC_SCL   PBout(10)    //SCL
#define FDC_IIC_SDA   PBout(11)    //SDA
#define FDC_READ_SDA  PBin(11)     //SDA

/*FDC2214    iic从地址
 *ADDR = L , I2C Address = 0x2A
 *ADDR = H , I2C Address = 0x2B*/
#define FDC2214_ADDR 0x2A

/*FDC2214各个寄存器地址*/
#define DATA_CH0 0x00     				//数据寄存器
#define DATA_LSB_CH0 0x01
#define DATA_CH1 0x02
#define DATA_LSB_CH1 0x03
#define DATA_CH2 0x04
#define DATA_LSB_CH2 0x05
#define DATA_CH3 0x06
#define DATA_LSB_CH3 0x07
#define RCOUNT_CH0 0x08    //
#define RCOUNT_CH1 0x09
#define RCOUNT_CH2 0x0A
#define RCOUNT_CH3 0x0B
//#define OFFSET_CH0 0x0C  //FDC2114
//#define OFFSET_CH1 0x0D
//#define OFFSET_CH2 0x0E
//#define OFFSET_CH3 0x0F
#define SETTLECOUNT_CH0 0x10
#define SETTLECOUNT_CH1 0x11
#define SETTLECOUNT_CH2 0x12
#define SETTLECOUNT_CH3 0x13
#define CLOCK_DIVIDERS_C_CH0 0x14       //时钟分频
#define CLOCK_DIVIDERS_C_CH1 0x15
#define CLOCK_DIVIDERS_C_CH2 0x16
#define CLOCK_DIVIDERS_C_CH3 0x17
#define STATUS 0x18                     //状态寄存器
#define ERROR_CONFIG 0x19 				//错误报告设置
#define CONFIG 0x1A  
#define MUX_CONFIG 0x1B
#define RESET_DEV 0x1C
#define DRIVE_CURRENT_CH0 0x1E          //电流驱动
#define DRIVE_CURRENT_CH1 0x1F
#define DRIVE_CURRENT_CH2 0x20
#define DRIVE_CURRENT_CH3 0x21
#define MANUFACTURER_ID   0x7E      //读取值：0x5449
#define DEVICE_ID 0x7F            //读取值：0x3055

//IIC所有操作函数
void FDC_IIC_Delay(void);
void FDC_IIC_Init(void);
void FDC_IIC_Stop(void);
u8 FDC_IIC_Wait_Ack(void);
void FDC_IIC_Ack(void);
void FDC_IIC_NAck(void);
void FDC_IIC_Send_Byte(u8 txd);
u8 FDC_IIC_Read_Byte(unsigned char ack);

//相关函数申明
u8 Set_FDC2214(u8 reg,u8 MSB,u8 LSB);
u16 FDC2214_Read(u8 reg);
u32 FCD2214_ReadCH(u8 index);
u8 FDC2214_Init(void);
float Cap_Calculate(u8 index);
#endif
