#include "IIC_Hardware.h"

u32 ulTimeOut_Time;


void IIC_Config(void)
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

    /*I2C1 configuration*/
    GPIO_PinAFConfig(GPIOB, GPIO_PinSource10, GPIO_AF_I2C2); //注意，此处不能合并写成GPIO_PinSource10|GPIO_PinSource11
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
    I2C_InitStructure.I2C_OwnAddress1 = 0x00;	//主机地址
    I2C_InitStructure.I2C_Ack = I2C_Ack_Enable;//使能应答
    I2C_InitStructure.I2C_ClockSpeed = 400000;//IIC速度
    I2C_InitStructure.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;//7位地址模式
    I2C_Init(I2C2, &I2C_InitStructure);

    /* I2C Initialize */
    I2C_Cmd(I2C2, ENABLE);
		
		I2C_AcknowledgeConfig(I2C1,ENABLE);//把硬件自动应答打开
    /*超时设置*/
    RCC_GetClocksFreq(&rcc_clocks);
    ulTimeOut_Time = (rcc_clocks.SYSCLK_Frequency /10000); 
}

u8 I2C_ByteWrite(uint8_t REG_Address,uint8_t REG_data1,uint8_t REG_data2)
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

		I2C_SendData(I2C2,REG_Address);
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

		I2C_SendData(I2C2,REG_data1);
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;
		
		I2C_SendData(I2C2,REG_data2);
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

		I2C_GenerateSTOP(I2C2,ENABLE);
		
		return I2C_Err;
}

/*
 * 函数名：I2C_ByteRead
 * 描述  ：从IIC设备寄存器中读取两个字节
 * 输入  ：REG_Address 读取数据的寄存器的地址 
 * 输出  ：无
 * 返回  ：无
 * 调用  ：内部调用 
*/
u16 I2C_ByteRead(uint8_t REG_Address)
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

		I2C_Send7bitAddress(I2C2,((FDC2214_ADDR<<1)|0),I2C_Direction_Transmitter);//发送设备地址+写信号
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2,I2C_EVENT_MASTER_TRANSMITTER_MODE_SELECTED)));
    if(tmr==0) I2C_Err = 1;

		I2C_SendData(I2C2,REG_Address);//发送存储单元地址，从0开始
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2,I2C_EVENT_MASTER_BYTE_TRANSMITTED)));
    if(tmr==0) I2C_Err = 1;

		I2C_GenerateSTART(I2C2,ENABLE);//起始信号
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_MODE_SELECT)));
    if(tmr==0) I2C_Err = 1;

		I2C_Send7bitAddress(I2C2,((FDC2214_ADDR<<1)|0),I2C_Direction_Receiver);//发送设备地址+读信号
		tmr = ulTimeOut_Time;
    while((--tmr)&&(!I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_RECEIVER_MODE_SELECTED)));
    if(tmr==0) I2C_Err = 1; 

		tmr = ulTimeOut_Time;
    while((--tmr)&&(!(I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_RECEIVED))));  /*第一个高字节*/
    if(tmr==0) I2C_Err = 1;
		REG_data=I2C_ReceiveData(I2C2)<<8;//读出寄存器数据

		I2C_AcknowledgeConfig(I2C2,DISABLE);//关闭应答使能
		I2C_GenerateSTOP(I2C2,ENABLE);

		tmr = ulTimeOut_Time;
    while((--tmr)&&(!(I2C_CheckEvent(I2C2, I2C_EVENT_MASTER_BYTE_RECEIVED))));  /*第二个低字节*/
    if(tmr==0) I2C_Err = 1;
		REG_data|=I2C_ReceiveData(I2C2);//读出寄存器数据
			
		I2C_AcknowledgeConfig(I2C2, ENABLE);
		while(I2C_Err);
		return REG_data;

}

u8 FDC_Init(void)
{
	u16 res;
	IIC_Config();
	res=I2C_ByteRead(MANUFACTURER_ID);
	if(res==0x5449)
	{
		I2C_ByteWrite(RCOUNT_CH0, 0x01, 0x00); //(极速)
//      I2C_ByteWrite(RCOUNT_CH0,0x02,0x58);
		I2C_ByteWrite(SETTLECOUNT_CH0,0x00,0x14);//(SETTLECOUNT_CHx*16)/Frefx）转换前保持稳定的时间 ts0=settlecount*16/fref=0x14*16/(40*10e6)=8us
//		I2C_ByteWrite(RESET_DEV,0x06,0x00);
//		I2C_ByteWrite(OFFSET_CH0,0x06,0x00);
		I2C_ByteWrite(CLOCK_DIVIDERS_C_CH0,0x20,0x01);//Fin=43.4Mhz,Fref=21.7M(单端2分频)
        I2C_ByteWrite(CLOCK_DIVIDERS_C_CH0, 0x10, 0x01);
//		I2C_ByteWrite(DRIVE_CURRENT_CH0,0x78,0x00);//0.146mA（传感器时钟建立+转换时间的驱动电流）
		I2C_ByteWrite(ERROR_CONFIG,0x00,0x00);//全部禁止错误汇报
		//I2C_ByteWrite(MUX_CONFIG,0x82,0x0D);//双通道
		I2C_ByteWrite(CONFIG, 0x14, 0x01);//内部时钟
//      I2C_ByteWrite(CONFIG,0x16,0x01);//低功耗+外部时钟
		return 0;
	}
	else return 1;
}


u32 FCD_ReadCH(u8 index){
	u32 result;
	switch(index)
	{
		case 0:
		  result = I2C_ByteRead(DATA_CH0)&0x0FFF;
		  result = (result<<16)|(I2C_ByteRead(DATA_LSB_CH0));
			break;
		case 1:
			result = I2C_ByteRead(DATA_CH1)&0x0FFF;
		  result = (result<<16)|(I2C_ByteRead(DATA_LSB_CH1));
			break;
		case 2:
			result = I2C_ByteRead(DATA_CH2)&0x0FFF;
		  result = (result<<16)|(I2C_ByteRead(DATA_LSB_CH2));
			break;
		case 3:
			result = I2C_ByteRead(DATA_CH3)&0x0FFF;
		  result = (result<<16)|(I2C_ByteRead(DATA_LSB_CH3));
			break;
		default:break;
	}
	result =result&0x0FFFFFFF;
	return result;
}



u32 FDC_Data;

float Calculate_Cap(u8 index)
{
	float Cap;
	FDC_Data = FCD_ReadCH(index);
	Cap = 125873344.207639/(FDC_Data);
//	Cap = 125873344.207639/(FDC_Data);   //40M外部晶振	  0x6194  0x2001 测量基于10ms,稳定时间SETTLECOUNT_CH0=0x14
//	Cap = 116012298.808884/(FDC_Data);	 //43.4M内部晶振  0x69df  0x2001
//	Cap = 251746688.415279/(FDC_Data);   //20M外部晶振（2分频）    0x30c0  0x2002
//	Cap = 232024597.617768/(FDC_Data);	 //21.7M内部晶振（2分频）  0x34e2  0x2002
	
	return (Cap*Cap);
}

