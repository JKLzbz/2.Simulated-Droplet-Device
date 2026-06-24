#include "STM32_GD60914.h"

unsigned char temperat_BC_flag = 0;
float temp_bf1,temp_BC2;
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/
/*******************************************************************************
* Function Name  : SMBus_Init
* Description    : SMBus初始化
* Input          : None
* Output         : None
* Return         : None
*******************************************************************************/
void SMBus_Init()  //IIC初始化
{

//  GPIO_InitTypeDef    GPIO_InitStructure;
//	/* Enable SMBUS_PORT clocks */
//	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_SMBUS_PORT, ENABLE);

//    GPIO_InitStructure.GPIO_Pin = SMBUS_SCK | SMBUS_SDA;
//    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;         //输出模式
//    GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;        //推挽输出
//    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_100MHz;    //IO口速度为100MHz
//    GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;          //上拉
//    GPIO_Init(SMBUS_PORT, &GPIO_InitStructure);

//    SMBUS_SCK_H();
//    SMBUS_SDA_H();
	  GPIO_InitTypeDef  GPIO_InitStructure;

  RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);//使能GPIOB时钟

  //GPIOB8,B9初始化设置
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8 | GPIO_Pin_9;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;//普通输出模式
  GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;//推挽输出
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;//100MHz
  GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;//上拉
  GPIO_Init(GPIOB, &GPIO_InitStructure);//初始化
	SMBUS_SCK_H();
	SMBUS_SDA_H();
//		IIC_SCL=1;
//		IIC_SDA=1;
}
/*******************************************************************************
* Function Name  : SMBus_StartBit
* Description    : Generate START condition on SMBus
* Input          : None
* Output         : None
* Return         : None
*******************************************************************************/

void SMBus_StartBit(void)	//产生IIC的起始条件
{
    SMBUS_SDA_H();		// Set SDA line
    SMBus_Delay(5);	    // Wait a few microseconds
    SMBUS_SCK_H();		// Set SCL line
    SMBus_Delay(5);	    // Generate bus free time between Stop
    SMBUS_SDA_L();		// Clear SDA line
    SMBus_Delay(5);	    // Hold time after (Repeated) Start
    // Condition. After this period, the first clock is generated.
    //(Thd:sta=4.0us min)
    SMBUS_SCK_L();	    // Clear SCL line
    SMBus_Delay(5);	    // Wait a few microseconds
}

/*******************************************************************************
* Function Name  : SMBus_StopBit
* Description    : Generate STOP condition on SMBus
* Input          : None
* Output         : None
* Return         : None
*******************************************************************************/
void SMBus_StopBit(void)   //产生IIC的停止条件
{
    SMBUS_SCK_L();		// Clear SCL line
    SMBus_Delay(5);	    // Wait a few microseconds
    SMBUS_SDA_L();		// Clear SDA line
    SMBus_Delay(5);	    // Wait a few microseconds
    SMBUS_SCK_H();		// Set SCL line
    SMBus_Delay(5);	    // Stop condition setup time(Tsu:sto=4.0us min)
    SMBUS_SDA_H();		// Set SDA line
}

/*******************************************************************************
* Function Name  : SMBus_SendByte 主机发送数据
* Description    : Send a byte on SMBus
* Input          : Tx_buffer
* Output         : None
* Return         : None  主机接收的应答
*******************************************************************************/
u8 SMBus_SendByte(u8 Tx_buffer)  
{
    u8	Bit_counter;
    u8	Ack_bit;
    u8	bit_out;

    for(Bit_counter=8; Bit_counter; Bit_counter--)
    {
        if (Tx_buffer&0x80)
        {
            bit_out=1;   // If the current bit of Tx_buffer is 1 set bit_out
        }
        else
        {
            bit_out=0;  // else clear bit_out
        }
        SMBus_SendBit(bit_out);		// Send the current bit on SDA
        Tx_buffer<<=1;				// Get next bit for checking
    }

    Ack_bit=SMBus_ReceiveBit();		// Get acknowledgment bit
    return	Ack_bit;
}

/*******************************************************************************
* Function Name  : SMBus_SendBit
* Description    : Send a bit on SMBus 82.5kHz
* Input          : bit_out
* Output         : None
* Return         : None
*******************************************************************************/
void SMBus_SendBit(u8 bit_out)   //发送一个位到SMBus
{
    if(bit_out==0)
    {
        SMBUS_SDA_L();
    }
    else
    {
        SMBUS_SDA_H();
    }
    SMBus_Delay(2);					// Tsu:dat = 250ns minimum
    SMBUS_SCK_H();					// Set SCL line
    SMBus_Delay(6);					// High Level of Clock Pulse
    SMBUS_SCK_L();					// Clear SCL line
    SMBus_Delay(3);					// Low Level of Clock Pulse
//	SMBUS_SDA_H();				    // Master release SDA line ,
    return;
}

/*******************************************************************************
* Function Name  : SMBus_ReceiveBit
* Description    : Receive a bit on SMBus
* Input          : None
* Output         : None
* Return         : Ack_bit
*******************************************************************************/
u8 SMBus_ReceiveBit(void)  //SMBus接收一个位
{
    u8 Ack_bit;

    SMBUS_SDA_H();          //引脚靠外部电阻上拉，当作输入
		SMBus_Delay(2);			// High Level of Clock Pulse
    SMBUS_SCK_H();			// Set SCL line
    SMBus_Delay(5);			// High Level of Clock Pulse
    if (SMBUS_SDA_PIN())
    {
        Ack_bit=1;
    }
    else
    {
        Ack_bit=0;
    }
    SMBUS_SCK_L();			// Clear SCL line
    SMBus_Delay(3);			// Low Level of Clock Pulse

    return	Ack_bit;
}

/*******************************************************************************
* Function Name  : SMBus_ReceiveByte  // 主机接收数据
* Description    : Receive a byte on SMBus
* Input          : ack_nack
* Output         : None
* Return         : RX_buffer
*******************************************************************************/
u8 SMBus_ReceiveByte(u8 ack_nack)  
{
    u8 	RX_buffer;
    u8	Bit_Counter;

    for(Bit_Counter=8; Bit_Counter; Bit_Counter--)
    {
        if(SMBus_ReceiveBit())			// Get a bit from the SDA line
        {
           RX_buffer <<= 1;			// If the bit is HIGH save 1  in RX_buffer
           RX_buffer |=0x01;
        }
        else
        {
           RX_buffer <<= 1;			// If the bit is LOW save 0 in RX_buffer
           RX_buffer &=0xfe;
        }
    }
    SMBus_SendBit(ack_nack);			// Sends acknowledgment bit
    return RX_buffer;
}

/*******************************************************************************
* Function Name  : SMBus_Delay
* Description    : 延时  一次循环约1us
* Input          : time
* Output         : None
* Return         : None
*******************************************************************************/
void SMBus_Delay(u16 time)  // 延时函数，一次循环约1us
{
//    u16 i, j;
//    for (i=0; i<400; i++)
//    {
//        for (j=0; j<time; j++);
//    }  
	while(time--)
    {
			delay_us(100);
    }
}



s16 tempe_read(uint16_t reg)
{
	u8 data1L;
  u8 data1H;
 
	s16 data;
	
	 SMBus_StartBit();
	 SMBus_SendByte(0X30);
 
	SMBus_SendByte(reg); 

  SMBus_StartBit();
	SMBus_SendByte(0X31); 
	data1L = SMBus_ReceiveByte(ACK);
	data1H = SMBus_ReceiveByte(1);
  SMBus_StopBit();
	data =data1H <<8|data1L;
	return data;	
}
//s16 GD60914_Cal35Temp(void)   //校准35度  
//{   
//	s16 tvalue;
//	Delay_ms(10);
//	tvalue=tempe_read(0x58);
//	Delay_ms(3000);
//	tvalue=tempe_read(0x1C);
//	Delay_ms(10);
// 	return tvalue;
//}
//s16 GD60914_Cal42Temp(void)     //校准42度
//{   
//	s16 tvalue;
//	Delay_ms(10);
//	tvalue=tempe_read(0x62);
//	Delay_ms(3000);
//	tvalue=tempe_read(0x1C);
//	Delay_ms(10);
// 	return tvalue;
//}
//s16 GD60914_ClearDefault(void)  //清除校准   
//{   
//	s16 tvalue;
//	Delay_ms(10);
//	tvalue=tempe_read(0x59);
//	Delay_ms(300);
//	tvalue=tempe_read(0x1C);
//	Delay_ms(10);
// 	return tvalue;
//}
s16 GD60914_ReadTemp(void)     
{   
	s16 tvalue;
	delay_ms(10);
	tvalue=tempe_read(0x81);
	delay_ms(200);
	tvalue=tempe_read(0x1A);
//	printf("%x\r\n",tvalue);
	delay_ms(300);
	tvalue=tempe_read(0x1C);
	delay_ms(10);
 	return tvalue;
}
//s16 OObtaining_ambient_temperature(void)    //获取环境温度 
//{   
//	s16 tvalue;
//	Delay_ms(10);
//	tvalue=tempe_read(0x1E);
//	Delay_ms(400);
//	tvalue=tempe_read(0x1C);
//	Delay_ms(10);
// 	return tvalue;
//}
