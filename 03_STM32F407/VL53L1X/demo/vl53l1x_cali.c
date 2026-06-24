#include "VL53L1X_cali.h"

//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//ALIENTEK MiniV3 STM32开发板
//VL53L0X-校准模式 驱动代码	   
//正点原子@ALIENTEK
//技术论坛:www.openedv.com
//创建日期:2017/7/1
//版本：V1.0
//版权所有，盗版必究。
//Copyright(C) 广州市星翼电子科技有限公司 2009-2019
//All rights reserved									  
////////////////////////////////////////////////////////////////////////////////// 

_VL53L1_adjust VL53L1_adjust; //校准数据24c02写缓存区(用于在校准模式校准数据写入24c02)
_VL53L1_adjust VL53L1_data_param;   //校准数据24c02读缓存区（用于系统初始化时向24C02读取数据）

#define adjust_num 5//校准错误次数

//VL53L0X校准函数
//dev:设备I2C参数结构体
VL53L1_Error VL53L1_adjust(VL53L1_Dev_t *dev)
{
	
	VL53L1_DeviceError Status = VL53L1_Error_NONE;
	uint32_t refSpadCount = 7;
	uint8_t  isApertureSpads = 0;
	uint32_t XTalkCalDistance = 100;
	uint32_t XTalkCompensationRateMegaCps;
	uint32_t CalDistanceMilliMeter = 100<<16;
	int32_t  OffsetMicroMeter = 30000;
	uint8_t VhvSettings = 23;
	uint8_t PhaseCal = 1;
	uint8_t i=0;

	VL53L1_StaticInit(dev);//数值恢复默认,传感器处于空闲状态
  LED_Off;
	//SPADS校准----------------------------
	spads:
	delay_ms(10);
	printf("The SPADS Calibration Start...\r\n");
	Status = VL53L1_PerformRefSpadManagement(dev,&refSpadCount,&isApertureSpads);//执行参考Spad管理
	if(Status == VL53L1_Error_NONE)
	{
	    printf("refSpadCount = %d\r\n",refSpadCount);
	    VL53L1_adjust.refSpadCount = refSpadCount;
	    printf("isApertureSpads = %d\r\n",isApertureSpads);	
	    VL53L1_adjust.isApertureSpads = isApertureSpads;
        printf("The SPADS Calibration Finish...\r\n\r\n");		
	    i=0;
	}
	else
	{
	    i++;
	    if(i==adjust_num) return Status;
	    printf("SPADS Calibration Error,Restart this step\r\n");
	    goto spads;
	}
	//设备参考校准---------------------------------------------------
	ref:
	delay_ms(10);
	printf("The Ref Calibration Start...\r\n");
	Status = VL53L1_PerformRefCalibration(dev,&VhvSettings,&PhaseCal);//Ref参考校准
	if(Status == VL53L1_Error_NONE)
	{
		printf("VhvSettings = %d\r\n",VhvSettings);
		VL53L1_adjust.VhvSettings = VhvSettings;
		printf("PhaseCal = %d\r\n",PhaseCal);
		VL53L1_adjust.PhaseCal = PhaseCal;
		printf("The Ref Calibration Finish...\r\n\r\n");
		i=0;
	}
	else
	{
		i++;
		if(i==adjust_num) return Status;
		printf("Ref Calibration Error,Restart this step\r\n");
		goto ref;
	}
	//偏移校准------------------------------------------------
	offset:
	delay_ms(10);
	printf("Offset Calibration:need a white target,in black space,and the distance keep 100mm!\r\n");
	printf("The Offset Calibration Start...\r\n");
	Status = VL53L1_PerformOffsetCalibration(dev,CalDistanceMilliMeter,&OffsetMicroMeter);//偏移校准
	if(Status == VL53L1_Error_NONE)
	{
		printf("CalDistanceMilliMeter = %d mm\r\n",CalDistanceMilliMeter);
		VL53L1_adjust.CalDistanceMilliMeter = CalDistanceMilliMeter;
		printf("OffsetMicroMeter = %d mm\r\n",OffsetMicroMeter);	
		VL53L1_adjust.OffsetMicroMeter = OffsetMicroMeter;
		printf("The Offset Calibration Finish...\r\n\r\n");
		i=0;
	}
	else
	{
		i++;
		if(i==adjust_num) return Status;
		printf("Offset Calibration Error,Restart this step\r\n");
		goto offset;
	}
	//串扰校准-----------------------------------------------------
	xtalk:
	delay_ms(20);
	printf("Cross Talk Calibration:need a grey target\r\n");
	printf("The Cross Talk Calibration Start...\r\n");	
	Status = VL53L1_PerformXTalkCalibration(dev,XTalkCalDistance,&XTalkCompensationRateMegaCps);//串扰校准
	if(Status == VL53L1_Error_NONE)
	{
		printf("XTalkCalDistance = %d mm\r\n",XTalkCalDistance);
		VL53L1_adjust.XTalkCalDistance = XTalkCalDistance;
		printf("XTalkCompensationRateMegaCps = %d\r\n",XTalkCompensationRateMegaCps);	
		VL53L1_adjust.XTalkCompensationRateMegaCps = XTalkCompensationRateMegaCps;
		printf("The Cross Talk Calibration Finish...\r\n\r\n");
		i=0;
	}
	else
	{
		i++;
		if(i==adjust_num) return Status;
		printf("Cross Talk Calibration Error,Restart this step\r\n");
		goto xtalk;
	}
	LED_On;
	printf("All the Calibration has Finished!\r\n");
	printf("Calibration is successful!!\r\n");

	VL53L1_adjust.adjustok = 0xAA;//校准成功
//AT24CXX_Write(0,(u8*)&VL53L1_adjust,sizeof(_VL53L1_adjust));//将校准数据保存到24c02
	memcpy(&VL53L1_data,&VL53L1_adjust,sizeof(_VL53L1_adjust));//将校准数据复制到VL53L1_data结构体
	return Status;
}

//vl53l0x校准测试
//dev:设备I2C参数结构体
void VL53L1_calibration_test(VL53L1_Dev_t *dev)
{  
	VL53L1_Error status = VL53L1_Error_NONE;
	u8 key=0;
	u8 i=0;
	
	LCD_Fill(30,170,320,300,WHITE);
	POINT_COLOR=RED;//设置字体为红色 
	LCD_ShowString(30,170,300,16,16,"need a white target,and ");
	LCD_ShowString(30,190,250,16,16,"the distance keep 100mm.");
	POINT_COLOR=BLUE;//设置字体为蓝色 
	LCD_ShowString(30,220,200,16,16,"KEY_UP: Return menu");
	LCD_ShowString(30,240,200,16,16,"KEY1:   Calibration");
	while(1)
	{
		key = KEY_Scan(0);
		if(key==KEY1_PRES)
		{
			POINT_COLOR=RED;//设置字体为红色 
			LCD_ShowString(30,260,200,16,16,"Start calibration...");
			status = VL53L1_adjust(dev);//进入校准
			if(status!=VL53L1_Error_NONE)//校准失败
			{ 
				 printf("Calibration is error!!\r\n");
				 i=3;
				 while(i--)
				 {
					  delay_ms(500);
					  LCD_ShowString(30,260,200,16,16,"                    ");
					  delay_ms(500);
					  LCD_ShowString(30,260,200,16,16,"Calibration is error");
				 }
			}
			else
				 LCD_ShowString(30,260,200,16,16,"Calibration is complete!");
			delay_ms(500);

			break;
				
		 }
		 else if(key==WKUP_PRES)
		 {
			 LED1=1;
			 break;//返回上一菜单
		 }		 
		 delay_ms(200);
		 LED0=!LED0;
		
	}
		
}
