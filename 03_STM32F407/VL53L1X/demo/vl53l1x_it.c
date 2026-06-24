#include "VL53L1X_it.h"

//upper & lower thresholds of distance: mm
#define Thresh_Low    20  //60  int will occur only when the test distance between upper and lower limit
#define Thresh_High 1500 //100

extern uint8_t Ajusted[];
extern mode_data Mode_data[];

//int mode param struct
typedef struct 
{
	const int VL53L1_Mode;//mode
	uint32_t ThreshLow;    
	uint32_t ThreshHigh;   
}AlrmMode_t; 

AlrmMode_t AlarmModes ={
   VL53L1_GPIOFUNCTIONALITY_THRESHOLD_CROSSED_OUT,// value < thresh_low OR value > thresh_high
	 Thresh_Low << 16,
	 Thresh_High << 16
};

//中断配置初始化
static void exti_init(void)
{
	
}

//alarm_flag 
//1: warn
//0：no warn
uint8_t alarm_flag=0;

//EXTI ISR
//--in callback function----
void VL53L1_get_result(VL53L1_Dev_t* pDev,VL53L1_RangingMeasurementData_t* pRangingMeasurementData)
{
	VL53L1_Error status=VL53L1_Error_NONE;

	alarm_flag=1;		//for main program reading result
	
	status=VL53L1_GetRangingMeasurementData(pDev,	pRangingMeasurementData);
	if(status!=VL53L1_Error_NONE)
		alarm_flag=2;		//error
	
	status = VL53L1_ClearInterruptMask(pDev,0);
	if(status!=VL53L1_Error_NONE)
		alarm_flag=3;		//error
}


//vl53l1x interrupt test mode
//dev: device I2C param struct
//mode: 0:default, 1:high accuracy, 2:long distance, 3:high speed
VL53L1_Error VL53L1_interrupt_start(VL53L1_Dev_t *dev,uint8_t mode)
{
	uint8_t VhvSettings;
	uint8_t PhaseCal;
	uint32_t refSpadCount;
	uint8_t isApertureSpads;
	VL53L1_Error status=VL53L1_Error_NONE;

	VL53L1_reset(dev);//reset vl53l1x
	status = VL53L1_StaticInit(dev);
	if(status!=VL53L1_Error_NONE)
		return status;
		
 	status = VL53L1_PerformRefCalibration(dev, &VhvSettings, &PhaseCal);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_PerformRefSpadManagement(dev, &refSpadCount, &isApertureSpads);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);		 
	status = VL53L1_SetDeviceMode(dev,VL53L1_DEVICEMODE_CONTINUOUS_RANGING);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetInterMeasurementPeriodMilliSeconds(dev,Mode_data[mode].timingBudget);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetLimitCheckEnable(dev,VL53L1_CHECKENABLE_SIGMA_FINAL_RANGE,1);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetLimitCheckEnable(dev,VL53L1_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE,1);//使能信号速率范围检查
	if(status!=VL53L1_Error_NONE)
		return status;
	
	HAL_Delay(2);
	status = VL53L1_SetLimitCheckValue(dev,VL53L1_CHECKENABLE_SIGMA_FINAL_RANGE,Mode_data[mode].sigmaLimit);//设定SIGMA范围
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetLimitCheckValue(dev,VL53L1_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE,Mode_data[mode].signalLimit);//设定信号速率范围范围
	if(status!=VL53L1_Error_NONE)
		return status; 

	//---maybe need, and add a item to Mode_data
	//HAL_Delay(2);
	//status = VL53L1_SetLimitCheckValue(dev,VL53L1_CHECKENABLE_RANGE_IGNORE_THRESHOLD,Mode_data[mode].signalLimit);//set signal rate limit
	//if(status!=VL53L1_Error_NONE) 
	//	return status;

	HAL_Delay(2);
	status = VL53L1_SetMeasurementTimingBudgetMicroSeconds(dev,Mode_data[mode].timingBudget);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2); 
	status = VL53L1_SetVcselPulsePeriod(dev, VL53L1_VCSEL_PERIOD_PRE_RANGE, Mode_data[mode].preRangeVcselPeriod);
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetVcselPulsePeriod(dev, VL53L1_VCSEL_PERIOD_FINAL_RANGE, Mode_data[mode].finalRangeVcselPeriod);
	if(status!=VL53L1_Error_NONE)
		return status;
	
	HAL_Delay(2);
	status = VL53L1_StopMeasurement(dev);//stop testing
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetInterruptThresholds(dev,VL53L1_DEVICEMODE_CONTINUOUS_RANGING,AlarmModes.ThreshLow, AlarmModes.ThreshHigh);//set threshold
	if(status!=VL53L1_Error_NONE)
		return status;

	HAL_Delay(2);
	status = VL53L1_SetGpioConfig(dev,0,VL53L1_DEVICEMODE_CONTINUOUS_RANGING,AlarmModes.VL53L1_Mode,VL53L1_INTERRUPTPOLARITY_LOW);//set int trigger mode, falling
	if(status!=VL53L1_Error_NONE)
		return status;
	
	HAL_Delay(2);
	status = VL53L1_ClearInterruptMask(dev,0);//clear VL53L1X int flag
	 
	alarm_flag = 0;
	VL53L1_StartMeasurement(dev);//start test
}

/*
//vl53l1x int test mode
//dev: device I2C param struct
void VL53L1_interrupt_test(VL53L1_Dev_t *dev)
{
	u8 mode=0;
	
	VL53L1_interrupt_start(dev,mode);
}
*/


