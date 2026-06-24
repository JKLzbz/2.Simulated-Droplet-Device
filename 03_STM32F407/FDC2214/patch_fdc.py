import io
import os

c_file = r'D:\02Projects\01Simulated-Droplet-Device\03_STM32F407\FDC2214\fdc2214.c'
with io.open(c_file, 'r', encoding='gbk', errors='ignore') as f:
    content = f.read()

hw_i2c_code = """
#include "stm32f4xx_i2c.h"

u32 ulTimeOut_Time;

// 初始化硬件IIC I/O口
void FDC_IIC_Init(void)
{					     
    GPIO_InitTypeDef  GPIO_InitStructure;
    I2C_InitTypeDef I2C_InitStructure;
    RCC_ClocksTypeDef   rcc_clocks;

    /* GPIO Peripheral clock enable */
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);
    /* Reset I2Cx IP */
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C2, ENABLE);
    /* Release reset signal of I2Cx IP */
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C2, DISABLE);

    /*I2C2 configuration*/
    GPIO_PinAFConfig(GPIOB, GPIO_PinSource10, GPIO_AF_I2C2); 
    GPIO_PinAFConfig(GPIOB, GPIO_PinSource11, GPIO_AF_I2C2);

    //PB10: I2C2_SCL  PB11: I2C2_SDA
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10|GPIO_Pin_11;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_OType = GPIO_OType_OD;
    GPIO_InitStructure.GPIO_PuPd  = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    /* I2C Struct Initialize */
    I2C_DeInit(I2C2);
    I2C_InitStructure.I2C_Mode = I2C_Mode_I2C;  //IIC模式
    I2C_InitStructure.I2C_DutyCycle = I2C_DutyCycle_2;//50%占空比
    I2C_InitStructure.I2C_OwnAddress1 = 0x00;	//地址
    I2C_InitStructure.I2C_Ack = I2C_Ack_Enable;//使能应答
    I2C_InitStructure.I2C_ClockSpeed = 400000;//IIC速度400KHz
    I2C_InitStructure.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;//7位地址模式
    I2C_Init(I2C2, &I2C_InitStructure);

    /* I2C Initialize */
    I2C_Cmd(I2C2, ENABLE);
    I2C_AcknowledgeConfig(I2C2,ENABLE);//硬件自动应答
    
    /*时钟计算超时时间*/
    RCC_GetClocksFreq(&rcc_clocks);
    ulTimeOut_Time = (rcc_clocks.SYSCLK_Frequency / 10000); 
}

/*FDC2214设置函数 (硬件I2C实现)*/
u8 Set_FDC2214(u8 reg,u8 MSB,u8 LSB) 				 
{ 
    u32 tmr;
    u8 I2C_Err=0;
    tmr = ulTimeOut_Time;
    while((--tmr)&&I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY));
    if(tmr==0) I2C_Err = 1;
    I2C_GenerateSTART(I2C2,ENABLE);
    
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_MODE_SELECT))); 
    if(tmr==0) I2C_Err = 1;

    I2C_Send7bitAddress(I2C2,((FDC2214_ADDR<<1)|0),I2C_Direction_Transmitter);
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_TRANSMITTER_MODE_SELECTED)));
    if(tmr==0) I2C_Err = 1;

    I2C_SendData(I2C2,reg);
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

    I2C_SendData(I2C2,MSB);
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;
    
    I2C_SendData(I2C2,LSB);
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

    I2C_GenerateSTOP(I2C2,ENABLE);
    delay_ms(5); // 保持原版兼容的延迟
    return I2C_Err;
}

/*读取FDC2214寄存器数据 (硬件I2C实现)*/
u16 FDC2214_Read(u8 reg)
{
    u16 REG_data;
    u32 tmr;
    u8 I2C_Err=0;
    tmr = ulTimeOut_Time;
    while((--tmr)&&I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY));
    if(tmr==0) I2C_Err = 1;

    I2C_GenerateSTART(I2C2,ENABLE);//起始信号
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_MODE_SELECT)));
    if(tmr==0) I2C_Err = 1;

    I2C_Send7bitAddress(I2C2,((FDC2214_ADDR<<1)|0),I2C_Direction_Transmitter);//设备地址+写信号
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2,I2C_EVENT_MASTER_TRANSMITTER_MODE_SELECTED)));
    if(tmr==0) I2C_Err = 1;

    I2C_SendData(I2C2,reg);//发寄存器地址
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2,I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

    I2C_GenerateSTART(I2C2,ENABLE);//再次起始信号
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_MODE_SELECT)));
    if(tmr==0) I2C_Err = 1;

    I2C_Send7bitAddress(I2C2,((FDC2214_ADDR<<1)|1),I2C_Direction_Receiver);//设备地址+读信号
    tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_RECEIVER_MODE_SELECTED)));
    if(tmr==0) I2C_Err = 1; 

    tmr = ulTimeOut_Time;
    while((--tmr)&&(!(I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_RECEIVED))));  /*第一字节*/
    if(tmr==0) I2C_Err = 1;
    REG_data=I2C_ReceiveData(I2C2)<<8;//寄存器高八位

    I2C_AcknowledgeConfig(I2C2,DISABLE);//关闭应答使能,准备停止
    I2C_GenerateSTOP(I2C2,ENABLE);

    tmr = ulTimeOut_Time;
    while((--tmr)&&(!(I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_RECEIVED))));  /*第二字节*/
    if(tmr==0) I2C_Err = 1;
    REG_data|=I2C_ReceiveData(I2C2);//寄存器低八位
        
    I2C_AcknowledgeConfig(I2C2, ENABLE); //恢复应答
    if(I2C_Err) return 0xFFFF; // 如果超时出错返回错误码
    return REG_data;
}

"""

start_idx = content.find('//FDC_I2C')
end_idx = content.find('u8 FDC2214_Init(void)')

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + hw_i2c_code + content[end_idx:]
    with io.open(c_file, 'w', encoding='gbk') as f:
        f.write(new_content)
    print('Successfully patched fdc2214.c with hardware I2C!')
else:
    print('Failed to find insertion points!')
