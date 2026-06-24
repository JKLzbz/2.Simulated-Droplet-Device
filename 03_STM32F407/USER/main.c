#include "delay.h"
#include "usart.h"
#include "led.h"
#include "exti.h"
#include "lcd.h"
#include "key.h"  
#include "sram.h"   
#include "malloc.h" 
#include "usmart.h"  
#include "sdio_sdcard.h"    
#include "malloc.h" 
#include "w25qxx.h"    
#include "ff.h"  
#include "exfuns.h"    
#include "fontupd.h"
#include "text.h"	
#include "piclib.h"
#include "math.h"	
#include "dcmi.h"	
#include "ov5640.h"	
#include "beep.h"	
#include "timer.h"
//WIFI
#include "WiFiSend.h"
//FDC2214
#include "fdc2214.h"
// ==================== 边缘计算: 一阶卡尔曼滤波 (FDC2214) ====================
typedef struct {
    float Q; // 过程噪声协方差 (决定对基线漂移的追踪速度)
    float R; // 测量噪声协方差 (决定对高频毛刺的抑制程度)  Q噪声
    float x; // 状态估计值 (当前最优电容值)                x预测值
    float P; // 误差协方差                                 P对预测值的信心
    float K; // 卡尔曼增益
} KalmanFilter_t;

KalmanFilter_t fdc_kalman = {0.001f, 0.1f, 0.0f, 1.0f, 0.0f};

// 利用 Cortex-M4 FPU 运行的低延迟自适应一阶卡尔曼更新算法 (带新息峰值保护与防崩溃机制)
float Kalman_Update(KalmanFilter_t* kf, float measurement) {
    // 1. 防御无效输入 (NaN 或 Infinity，或异常大值)，直接返回上次的有效值
    if (measurement != measurement || measurement > 1e9f || measurement < -10000.0f) {
        return kf->x;
    }
    
    if (kf->x == 0.0f) kf->x = measurement; // 初始基线校准
    
    // 2. 计算新息 (测量值与预测值的残差)
    float innovation = measurement - kf->x;
    
    // 3. 自适应 Q 机制 (尖峰保护)
    // 阈值需根据实际底噪进行微调，这里暂定为 0.5 (代表电容跳变阈值)
    if (fabs(innovation) > 0.5f) {
        kf->Q = 10.0f;  // 发生巨大跳变，放开平滑限制，瞬间追踪飞沫尖峰
    } else {
        kf->Q = 0.001f; // 平缓期，强力平滑环境底噪
    }

    // 4. 经典卡尔曼更新方程
    float P_pred = kf->P + kf->Q;
    
    // 5. 确保分母绝对不为 0 (加极小值保护)
    float denominator = P_pred + kf->R;
    if (fabs(denominator) < 1e-6f) {
        return kf->x;
    }
    
    kf->K = P_pred / denominator;
    kf->x = kf->x + kf->K * innovation;
    kf->P = (1.0f - kf->K) * P_pred;
    
    return kf->x;
}
// =========================================================================
//VL53L1X
#include "laser_def.h"
#include "vl53l1x.h"
#include "vl53l1x_i2c.h"
//Temp
#include "STM32_GD60914.h"

/*********************协议设定**************************/
#define PROTOCOL_HEADER1 0xAA // 协议帧头1为0xAA
#define PROTOCOL_HEADER2 0xFF // 协议帧头2为0xFF（传感器数据: 1维飞沫电容 + 1维距离 + 1维温度）

// MPU6050 removed (Desktop Simulator)

/*******************Recognize Result Declar**********************/
int recognize_result= 0; //识别结果

/*******************Droplet Declar**********************/
float droplet=0;
/*******************Distance Declar*********************/
static volatile uint16_t lastdistance=0;//定义上一次的距离值
bool distance_updated = false;

//uint16_t Distance_data[2] = {0,0};
extern VL53L1_Dev_t VL53L1_dev[];	//2, device param, include I2C
extern uint8_t Ajusted[];//2, adjusted sign, 0-not, 1-had
extern VL53L1_RangingMeasurementData_t VL53L1_data[];//2, ranging result struct, distance, max distance,etc.
//extern uint16_t Distance_data[];//2, the catched distance. VL53L1_data->RangeMilliMeter; 

// MPU6050 variables removed陀螺仪原始数据

/*******************Temp Declar**********************/
s16 temp;//定义温度转换值
float temp_acq;//实际温度值
static volatile float lasttemp_acq=0.0;//上次保存的温度数据
bool temp_updated = false;
/*******************Beep musuic Declar**********************/
const  uint16_t tone[21]={3817,3401,3030,2865,2551,2272,2024,
												1912,1703,1517,1432,1275,1136,1012,
												956,851,758,715,637,568,506
};
const uint8_t music_tone[25]={4,4,5,4,7,6,4,4,5,4,8,7,4,4,11,9,7,6,5,10,10,9,7,8,7};
const uint8_t music_time[25]={2,2,4,4,4,8,2,2,4,4,4,8,2,2,4,4,4,4,4,6,2,4,4,4,8};

/*********************OV5640 code************************/
#define jpeg_dma_bufsize	5*1024		//定义JPEG DMA接收时数据缓存jpeg_buf0/1的大小(*4字节)
volatile u32 jpeg_data_len=0; 			//buf中的JPEG有效数据长度(*4字节)
volatile u8 jpeg_data_ok=0;					//JPEG数据采集完成标志 
																		//0,数据没有采集完;
																		//1,数据采集完了,但是还没处理;
																		//2,数据已经处理完成了,可以开始下一帧接收
										
u32 *jpeg_buf0;											//JPEG数据缓存buf,通过malloc申请内存
u32 *jpeg_buf1;											//JPEG数据缓存buf,通过malloc申请内存
u32 *jpeg_data_buf;									//JPEG数据缓存buf,通过malloc申请内存

//处理JPEG数据
//当采集完一帧JPEG数据后,调用此函数,切换JPEG BUF.开始下一帧采集.
void jpeg_data_process(void)
{
	u16 i;
	u16 rlen;//剩余数据长度
	u32 *pbuf;
		if(jpeg_data_ok==0)	//jpeg数据还未采集完?
		{	
			DMA_Cmd(DMA2_Stream1, DISABLE);//停止当前传输 
			while (DMA_GetCmdStatus(DMA2_Stream1) != DISABLE){}//等待DMA2_Stream1可配置  
			rlen=jpeg_dma_bufsize-DMA_GetCurrDataCounter(DMA2_Stream1);//得到此次数据传输的长度
			pbuf=jpeg_data_buf+jpeg_data_len;//偏移到有效数据末尾,继续添加
			if(DMA2_Stream1->CR&(1<<19))for(i=0;i<rlen;i++)pbuf[i]=jpeg_buf1[i];//读取buf1里面的剩余数据
			else for(i=0;i<rlen;i++)pbuf[i]=jpeg_buf0[i];//读取buf0里面的剩余数据 
			jpeg_data_len+=rlen;			//加上剩余长度
			jpeg_data_ok=1; 				//标记JPEG数据采集完按成,等待其他函数处理
		}
		if(jpeg_data_ok==2)	//上一次的jpeg数据已经被处理了
		{
			DMA_SetCurrDataCounter(DMA2_Stream1,jpeg_dma_bufsize);//传输长度为jpeg_buf_size*4字节
			DMA_Cmd(DMA2_Stream1,ENABLE); //重新传输
			jpeg_data_ok=0;					//标记数据未采集
			jpeg_data_len=0;				//数据重新开始
		}
} 
//jpeg数据接收回调函数
void jpeg_dcmi_rx_callback(void)
{ 
	u16 i;
	u32 *pbuf;
	pbuf=jpeg_data_buf+jpeg_data_len;//偏移到有效数据末尾
	if(DMA2_Stream1->CR&(1<<19))//buf0已满,正常处理buf1
	{ 
		for(i=0;i<jpeg_dma_bufsize;i++)pbuf[i]=jpeg_buf0[i];//读取buf0里面的数据
		jpeg_data_len+=jpeg_dma_bufsize;//偏移
	}else //buf1已满,正常处理buf0
	{
		for(i=0;i<jpeg_dma_bufsize;i++)pbuf[i]=jpeg_buf1[i];//读取buf1里面的数据
		jpeg_data_len+=jpeg_dma_bufsize;//偏移 
	} 	
}
//切换为OV5640模式（GPIOC8/9/11切换为 DCMI接口）
void sw_ov5640_mode(void)
{
	OV5640_WR_Reg(0X3017,0XFF);	//开启OV5650输出(可以正常显示)
	OV5640_WR_Reg(0X3018,0XFF); 
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource8,GPIO_AF_DCMI);  //PC8,AF13  DCMI_D2
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource9,GPIO_AF_DCMI);  //PC9,AF13  DCMI_D3
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource11,GPIO_AF_DCMI); //PC11,AF13 DCMI_D4  
 
} 
//切换为SD卡模式（GPIOC8/9/11切换为 SDIO接口）
void sw_sdcard_mode(void)
{
	OV5640_WR_Reg(0X3017,0X00);	//关闭OV5640全部输出(不影响SD卡通信)
	OV5640_WR_Reg(0X3018,0X00); 
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource8,GPIO_AF_SDIO);  //PC8,AF12
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource9,GPIO_AF_SDIO);//PC9,AF12 
	GPIO_PinAFConfig(GPIOC,GPIO_PinSource11,GPIO_AF_SDIO); 
}
//文件名自增（避免覆盖）
//jpg组合成:形如"0:PHOTO/PIC13141.jpg"的文件名
void camera_new_pathname(u8 *pname)
{	 
	u8 res;					 
	u16 index=0;
	while(index<0XFFFF)
	{
    sprintf((char*)pname,"0:PHOTO/PIC%05d.jpg",index);
		res=f_open(ftemp,(const TCHAR*)pname,FA_READ);//尝试打开这个文件
		if(res==FR_NO_FILE)break;		//该文件名不存在=正是我们需要的.
		index++;
	}
}
//OV5640拍照jpg图片
//返回值:0,成功
//    其他,错误代码
u8 ov5640_jpg_photo(u8 *pname)
{
	FIL* f_jpg; 
	u8 res=0;
	u32 bwr;
	u32 i;
	u8* pbuf;
	f_jpg=(FIL *)mymalloc(SRAMIN,sizeof(FIL));	//开辟FIL字节的内存区域 
	if(f_jpg==NULL)return 0XFF;				//内存申请失败.
	jpeg_data_ok=0;
	sw_ov5640_mode();						//切换为OV5640模式 
	OV5640_JPEG_Mode();						//JPEG模式  
	OV5640_OutSize_Set(16,4,1280,800);		//设置输出尺寸(500W)  
	dcmi_rx_callback=jpeg_dcmi_rx_callback;	//JPEG接收数据回调函数
	DCMI_DMA_Init((u32)jpeg_buf0,(u32)jpeg_buf1,jpeg_dma_bufsize,DMA_MemoryDataSize_Word,DMA_MemoryInc_Enable);//DCMI DMA配置(双缓冲模式)
	DCMI_Start(); 			//启动传输 
	while(jpeg_data_ok!=1);	//等待第一帧图片采集完
	jpeg_data_ok=2;			//忽略本帧图片,启动下一帧采集 
	while(jpeg_data_ok!=1);	//等待第二帧图片采集完,第二帧,才保存到SD卡去. 
	DCMI_Stop(); 			//停止DMA搬运
	sw_sdcard_mode();		//切换为SD卡模式
	res=f_open(f_jpg,(const TCHAR*)pname,FA_WRITE|FA_CREATE_NEW);//模式0,或者尝试打开失败,则创建新文件	 
	if(res==0)
	{
//下面一行可以删除
//		printf("jpeg data size:%d\r\n",jpeg_data_len*4);//串口打印JPEG文件大小
		pbuf=(u8*)jpeg_data_buf;
		for(i=0;i<jpeg_data_len*4;i++)//查找0XFF,0XD8和0XFF,0XD9,获取jpg文件大小
		{
			if((pbuf[i]==0XFF)&&(pbuf[i+1]==0XD8))break;//找到FF D8
		}
		if(i==jpeg_data_len*4)res=0XFD;//没找到0XFF,0XD8
		else//找到了
		{
			pbuf+=i;//偏移到0XFF,0XD8处
			res=f_write(f_jpg,pbuf,jpeg_data_len*4-i,&bwr);
			if(bwr!=(jpeg_data_len*4-i))res=0XFE; 
		}
	}
	jpeg_data_len=0;
	f_close(f_jpg); 
	sw_ov5640_mode();		//切换为OV5640模式
	myfree(SRAMIN,f_jpg); 
	return res;
}


volatile u8 g_wifi_success = 0;
volatile u16 g_wifi_status = 0;

// ================= 数据缓冲队列 =================
#define FIFO_SIZE 500
WifiDataPacket fifo_buffer[FIFO_SIZE];
volatile u16 fifo_head = 0;
volatile u16 fifo_tail = 0;

u8 FIFO_Enqueue(WifiDataPacket* pkt) {
    u16 next_head = (fifo_head + 1) % FIFO_SIZE;
    if (next_head == fifo_tail) return 0; // 队列满，丢弃旧数据
    fifo_buffer[fifo_head] = *pkt;
    fifo_head = next_head;
    return 1;
}
int main(void)
{
	uint16_t pre_distance=0;
	float pre_temp=0.0;
	int music_j;
	u8 mode = 0;  					//测距模式
	u8 distance_status=0;		//测距状态
	u8 res;	//代码执行是否成功返回值							
	u8 *pname;					//带路径的文件名 					 
	u8 sd_ok=1;					//0,sd卡不正常;1,SD卡正常. 
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);//设置系统中断优先级分组2
	delay_init(168);   	//初始化延时函数
	Usart1Init(115200);	//初始化系统打印数据的串口1
	LED_Init();				 	//初始化LED	
	// usmart_dev.init(84);		//已剥离：USMART在系统中未使用且其数据未被正确初始化，直接注释以防空指针引脚HardFault
/**************Temp初始化**************/
	SMBus_Init();
/**************FDC2214初始化**************/
	while(FDC2214_Init()){
		printf("FDC2214 Init error\r\n");
		delay_ms(20);
	}
/**************MPU6050 removed**************/
/*************VL53L1X初始化***************/
	distance_status = VL53L1_init(&VL53L1_dev[0]);
	if(0 != distance_status)
	{
		printf("VL53L1 Init error!\r\n");
		printf("%d",distance_status);
	}
	else
	{
		printf("VL53L1 Init OK\r\n");
	}	
	if(VL53L1_set_mode(&VL53L1_dev[0],mode))
	{
		printf("mode set error\r\n");
	}
	else
	{
		printf("set mode OK\r\n");
	}
/**************OV5640初始化***************/
	while(OV5640_Init())
	{
		printf("OV5640 Init error\r\n");
		delay_ms(20);
	}
	FSMC_SRAM_Init();					//初始化外部SRAM.
	
	sw_sdcard_mode();					//切换为SDIO模式	
 	my_mem_init(SRAMIN);			//初始化内部内存池 
	my_mem_init(SRAMEX);			//初始化内部内存池  
	my_mem_init(SRAMCCM);			//初始化CCM内存池
	SD_Init();								//SD卡初始化
	exfuns_init();						//为fatfs相关变量申请内存  
  f_mount(fs[0],"0:",1); 		//挂载SD卡  
	sw_sdcard_mode(); 				//切换为SD卡模式	
	if(SD_Init())
	{
		printf("SD Init error\r\n");
		delay_ms(200);
	}
	f_mount(fs[0],"0:",1); 					//挂载SD卡
	res=f_mkdir("0:/PHOTO");				//创建PHOTO文件夹
	if(res!=FR_EXIST&&res!=FR_OK) 	//发生了错误
	{
		printf("SD error,you can't take a photo\r\n");
		delay_ms(200);			
		sd_ok=0;  	
	}
	if(res!=FR_EXIST&&res!=FR_OK) 	//发生了错误
	{
		printf("SD error,you can't take a photo\r\n");			
		sd_ok=0;  	
	}
	else{
		printf("All going well\r\n");
		sd_ok=1;
	} 	
	jpeg_buf0=mymalloc(SRAMIN,jpeg_dma_bufsize*4);	//为jpeg dma接收申请内存	
	jpeg_buf1=mymalloc(SRAMIN,jpeg_dma_bufsize*4);	//为jpeg dma接收申请内存	
	jpeg_data_buf=mymalloc(SRAMEX,500*1024);		//为jpeg文件申请内存(最大300KB)
 	pname=mymalloc(SRAMIN,30);//为带路径的文件名分配30个字节的内存	 
 	while(pname==NULL||!jpeg_buf0||!jpeg_buf1||!jpeg_data_buf)	//内存分配出错
 	{
		printf("Memory allocation failure\r\n");
		delay_ms(200);		
	}	
	sw_ov5640_mode();
	OV5640_JPEG_Mode();  //JPEG模式
	//自动对焦初始化	
	OV5640_Focus_Init(); 
	OV5640_Light_Mode(0);		//自动模式
	OV5640_Color_Saturation(3);//色彩饱和度0
	OV5640_Brightness(4);		//亮度0
	OV5640_Contrast(3);			//对比度0
	OV5640_Sharpness(33);		//自动锐度
	OV5640_Focus_Constant();//启动持续对焦
	My_DCMI_Init();					//DCMI配置
/*****************WiFi模块初始化********************/
	M8266HostIf_Init();			//wifi_spi接口初始化
	g_wifi_success = M8266WIFI_Module_Init_Via_SPI();   //MCU通过wifi_spi接口配置wifi模块初始化
	if(!g_wifi_success)
		printf("MCU通过SPI2接口配置WIFI模块失败\r\n");
	else
	  printf("MCU通过SPI2接口配置WIFI模块成功\r\n");
/*************创建套接字连接--tcp客户端*************/
	printf("正在连接服务器...\r\n");
	while(1){
			g_wifi_success = M8266WIFI_SPI_Setup_Connection(1,0, "192.168.137.1", 8080, 0, 255, (u16*)&g_wifi_status); //tcp客户端、本机端口、目标地址、目标端口号、建立服务的超时时间
			if(g_wifi_success){
				printf("连接服务器成功... \r\n");
				break;
			}
			else{
				printf("连接服务器失败!\r\n");
				printf("正在连接服务器!\r\n");
		}	
	}
	EXTIX_Init();//WIFI接收中断初始化
  TIM3_Int_Init(10000-1,8400-1);//10Khz计数,1秒钟中断一次
	TIM13_PWM_Init();//蜂鸣器PWM波初始化
	TIM2_Int_Init(840-1, 200-1); // 500Hz高频采样（保证上位机画图有足够的数据点来快速滚动）
	while(1)
	{
		// 检查FIFO队列并批量发送
        u8 batch_count = 0;
        u16 q_len = (fifo_head + FIFO_SIZE - fifo_tail) % FIFO_SIZE;
        // 500Hz+5包（10ms发一次65字节，每秒100包），热点舒适区，配合上位机Jitter Buffer恒速消费
        while (q_len >= 5 || (q_len > 0 && q_len > 100)) {
            u8 batch_count = 0;
            WifiDataPacket batch_array[5];
            u16 temp_tail = fifo_tail;
            
            while (fifo_head != temp_tail && batch_count < 5) {
                batch_array[batch_count] = fifo_buffer[temp_tail];
                temp_tail = (temp_tail + 1) % FIFO_SIZE;
                batch_count++;
            }
            if (SendBufferViaWiFi((u8*)batch_array, batch_count * sizeof(WifiDataPacket))) {
                fifo_tail = temp_tail;
                q_len = (fifo_head + FIFO_SIZE - fifo_tail) % FIFO_SIZE;
            } else {
                break;
            }
        }

        static u8 sensor_div = 0;
        if (++sensor_div >= 100) {
            sensor_div = 0;
            distance_status = VL53L1_single_test(&VL53L1_dev[0],&VL53L1_data[0]);
            if(distance_status==VL53L1_Error_NONE){
                if(Distance!=pre_distance){
                    pre_distance=Distance;
                    distance_updated=true;
                }
            }
            temp=GD60914_ReadTemp();
            if(temp != pre_temp){
                pre_temp=temp;
                temp_updated=true;
                temp_acq=temp/10.0;
            }
        }
		if(recognize_result==16777216){                     //carema.open
		  if(sd_ok)//SD卡正常才可以拍照
			{    
				sw_sdcard_mode();	//切换为SD卡模式
				camera_new_pathname(pname);//得到文件名	
				res=ov5640_jpg_photo(pname);
				if(res)//拍照有误
				{
					printf("Write file error\r\n");		 
				}else 
				{	
					printf("Write file success\r\n");
					OV5640_Flash_Ctrl(1);//打开闪光灯
					delay_ms(50);
					OV5640_Flash_Ctrl(0);//关闭闪光灯
				}  			
			}else //提示SD卡错误
			{
				printf("SD error,you can't take a photo\r\n");	    
			}
			TIM_Cmd(TIM13, ENABLE);  //使能TIM13
			for(music_j=0;music_j<25;music_j++){
				set_pwm(tone[music_tone[music_j]],tone[music_tone[music_j]]/2);
				delay_ms(music_time[music_j]*62.5);
			}
			TIM_SetCompare1(TIM13,0);
			TIM_Cmd(TIM13, DISABLE);  //失能TIM13
			PFout(9)=1;
			delay_ms(50);
			PFout(9)=0;
		}
	} 
}





//定时器2中断服务函数
void TIM2_IRQHandler(void)
{
    if(TIM_GetITStatus(TIM2,TIM_IT_Update)!=RESET) //溢出中断
    {
			WifiDataPacket pkt;
			pkt.header1 = PROTOCOL_HEADER1;
			pkt.header2 = PROTOCOL_HEADER2;
			// 1. 获取原始电容数据 (FDC2214)
			float raw_cap = Cap_Calculate(0);
			
			// 2. 边缘计算: 卡尔曼滤波 (利用M4 FPU实现零延迟、去毛刺与基线追踪)
			pkt.droplet = Kalman_Update(&fdc_kalman, raw_cap);
			
			// MPU6050 (加速度计/陀螺仪) 已剥离，以符合桌面固定监测仪的系统逻辑。
			if(distance_updated == true){
				pkt.distance = Distance; //发送更新距离数据
				lastdistance = Distance;  //保存更新的距离数据
				distance_updated = false;  //重置距离更新标志
			}
			else{	//发送老数据
				pkt.distance = lastdistance;
			}
			if(temp_updated == true){
				pkt.temp = temp_acq; //发送更新温度数据
				lasttemp_acq = temp_acq;  //保存更新的温度数据
				temp_updated = false;	//重置温度更新标志
			}
			else{ //发送老数据
				pkt.temp = lasttemp_acq;
			}
			
			// 计算校验和
			u8 data_for_crc[sizeof(WifiDataPacket) - 1];
			memcpy(data_for_crc, &pkt, sizeof(WifiDataPacket) - 1);
			pkt.checksum = CalculateChecksum(data_for_crc, sizeof(data_for_crc));
			
			// 压入队列，不再直接发送（耗时仅1us，彻底解放中断！）
			FIFO_Enqueue(&pkt);
    }
    TIM_ClearITPendingBit(TIM2,TIM_IT_Update);  //清除中断标志位
}
