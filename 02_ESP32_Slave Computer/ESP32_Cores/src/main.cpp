#include <Arduino.h>
#include <WiFi.h>

// --- 1. 网络配置 ---
const char* ssid     = "JKLwindows"; 
const char* password = "JKLwindows";
WiFiServer server(80); 

// --- 2. 硬件引脚定义 ---
const int PUMP_PIN       = 21;  // 气泵
const int VALVE_PIN      = 19;  // 电磁阀
const int LASER_PIN      = 18;  // 激光
const int LX8201_PB3_PIN = 25;  // 雾化片控制 (GPIO25, 高电平=开雾化)


// --- 3. ESP32 LEDC 硬件 PWM 配置 (2.x 通道模式) ---
const int PUMP_CHANNEL  = 0;      // LEDC 通道号
const int LASER_CHANNEL = 1;      // 激光的 LEDC 通道号
const int pwmFreq       = 5000;   
const int pwmResolution = 10;     

// ==========================================
// 显式状态机定义
// ==========================================

// 系统顶层状态（包含扩展的生命周期状态）
enum SystemState {
  SYS_IDLE,             // 空闲待机：可接受所有指令
  SYS_COUGHING,         // 咳嗽执行中：仅接受 STOP
  SYS_PURGING,          // 清洗排空中：仅接受 STOP
  SYS_MANUAL_OVERRIDE   // 手动调试模式：屏蔽咳嗽宏指令，防止误触
};

// 咳嗽子状态 (对应 v6_0 的 5 个阶段)
enum CoughPhase {
  COUGH_IDLE,           // 未激活
  COUGH_PRESSURIZE,     // 阶段0：蓄压          (0 ~ 2800ms)
  COUGH_ATOMIZE,        // 阶段1：蓄雾          (2800 ~ 2993.127ms)
  COUGH_VALVE_FLY,      // 阶段2a：铁芯飞行中   (2993.127 ~ 3000ms)
  COUGH_BLAST,          // 阶段2b：黄金爆破      (3000 ~ 3050ms)
  COUGH_SWEEP           // 阶段3：清风扫膛       (3050 ~ 3100ms)
};

// ==========================================
// FreeRTOS 核心对象
// ==========================================

// 【优化1】用 FreeRTOS 队列替代手搓的 spinlock + volatile bool
//   - 支持多条指令缓冲（深度=4），不再丢指令
//   - 线程安全由 FreeRTOS 内核保证，无需手动 portENTER_CRITICAL
//   - 队列元素为固定大小 char[128]，零堆分配
static QueueHandle_t cmdQueue = NULL;
static const int     CMD_QUEUE_DEPTH = 4;     // 最多缓冲 4 条待处理指令
static const int     CMD_MAX_LEN     = 128;   // 单条指令最大长度

// 【优化2】保存任务句柄，用于生命周期管理和栈监控
static TaskHandle_t networkTaskHandle = NULL;
static TaskHandle_t controlTaskHandle = NULL;  // loop() 所在的 Arduino 主任务

// 【优化3】紧急停机通知位（用 FreeRTOS Task Notification 实现零延迟唤醒）
//   Core 0 收到 STOP 后，通过 xTaskNotifyGive 立即打断 Core 1 的忙等
static const uint32_t NOTIFY_EMERGENCY_STOP = 0x01;

// ==========================================
// 状态变量（仅 Core 1 读写，无需额外保护）
// ==========================================
SystemState sysState       = SYS_IDLE;
CoughPhase  coughPhase     = COUGH_IDLE;
bool        valveState     = false;

// 各种时序状态机用的时间记录
unsigned long coughPhaseStartUs = 0;   // 咳嗽当前阶段起始时刻 (micros)
unsigned long purgeStartUs      = 0;   // 排空模式起始时刻 (micros)
int           coughPumpSpeed    = 0;   // 本次咳嗽使用的泵速
float         current_target_pressure_mpa = 0.00; // 当前设定的目标背压，用于动态补偿

// --- 动态时序控制变量 (单位：微秒 us) ---
// 初始值为 V6.0 完美基准
unsigned long t_pressurize_us = 2800000UL; // 蓄压时间 2.8s
unsigned long t_atomize_us    = 193127UL;  // 蓄雾时间 ~193ms
unsigned long t_valve_fly_us  = 6873UL;    // 铁芯飞行 ~6.8ms (固件级硬件特性)
unsigned long t_blast_us      = 50000UL;   // 爆破时间 50ms
unsigned long t_sweep_us      = 50000UL;   // 扫膛时间 50ms

// ==========================================
// 气泵开环前馈查表函数 (6档位 MPa -> PWM 映射表)
// ==========================================
int getPumpPWM(float pressure) {
  if (pressure <= 0.02f) return 47;   // 强度 1：极弱干咋 (0.02 MPa)
  if (pressure <= 0.04f) return 61;   // 强度 2：轻度咋嘱 (0.04 MPa)
  if (pressure <= 0.05f) return 68;   // 强度 3：中度咋嘱 (0.05 MPa)
  if (pressure <= 0.06f) return 73;   // 强度 4：重度湿咋 (0.06 MPa)
  if (pressure <= 0.08f) return 200;  // 强度 5：极限爆发 (0.08 MPa)
  return 1023;                        // 强度 6：满功率档 (0.10 MPa)
}

// ==========================================
// 核心算法：电磁阀动态前馈补偿 (分段线性插值查表法)
// ==========================================
float get_compensated_delay(float current_pressure) {
  const float P_NODES[9] = {0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08};
  const float D_NODES[9] = {6.873, 6.731, 6.837, 6.895, 6.908, 6.983, 7.105, 7.251, 7.379};
  if (current_pressure <= 0.00) return D_NODES[0];
  if (current_pressure >= 0.08) return D_NODES[8];
  for (int i = 0; i < 8; i++) {
    if (current_pressure >= P_NODES[i] && current_pressure <= P_NODES[i+1]) {
      float p1 = P_NODES[i], p2 = P_NODES[i+1];
      float d1 = D_NODES[i], d2 = D_NODES[i+1];
      return d1 + (current_pressure - p1) * (d2 - d1) / (p2 - p1);
    }
  }
  return 6.873; 
}

// ==========================================
// 紧急全停 —— 任何状态下都可调用
// ==========================================
void emergencyStop() {
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(VALVE_PIN, LOW);
  ledcWrite(LASER_CHANNEL, 0);
  digitalWrite(LX8201_PB3_PIN, LOW);
  valveState  = false;
  coughPhase  = COUGH_IDLE;
  sysState    = SYS_IDLE;
  Serial.println("🛑 [状态机] 紧急全停！系统回到 IDLE");
}

// ==========================================
// 咳嗽状态机 Tick（非阻塞，每次 loop 调用一次）
//
// 架构：方案 C 混合方案（micros 轮询 + 关键飞跃期忙等）
//
// 时序对应 v6_0_original：
//   阶段0  蓄压        2,800,000 us
//   阶段1  蓄雾          193,127 us
//   阶段2a 铁芯飞行        6,873 us  ← 忙等精确补偿
//   阶段2b 黄金爆破       50,000 us
//   阶段3  清风扫膛       50,000 us
// ==========================================
void coughTick() {
  unsigned long now       = micros();
  unsigned long elapsedUs = now - coughPhaseStartUs;

  switch (coughPhase) {

    // ---------- 阶段 0：前期蓄压 ----------
    case COUGH_PRESSURIZE:
      if (elapsedUs >= t_pressurize_us) {
        Serial.printf("[T=%.1fms] 开启雾化（LX8201 PB3 拉高）...\n", t_pressurize_us / 1000.0);
        digitalWrite(LX8201_PB3_PIN, HIGH);
        coughPhaseStartUs = micros();
        coughPhase = COUGH_ATOMIZE;
      }
      break;

    // ---------- 阶段 1：蓄雾供弹 ----------
    case COUGH_ATOMIZE:
      if (elapsedUs >= t_atomize_us) {
        Serial.printf("[T=%.3fms] 电磁阀发令！铁芯起飞 (进入 %.3fms 精确机械补偿)...\n", 
                      (t_pressurize_us + t_atomize_us) / 1000.0, t_valve_fly_us / 1000.0);
        digitalWrite(VALVE_PIN, HIGH);
        
        // 【方案 C 核心】高精度自旋忙等，同时监听紧急停机通知
        unsigned long flyStartUs = micros();
        while (micros() - flyStartUs < t_valve_fly_us) {
          // 【优化4】在忙等期间检查紧急停机通知
          //   如果 Core 0 在这 6.873ms 内收到了 STOP 指令，
          //   通过 xTaskNotifyGive 可以让我们立即跳出忙等，执行紧急停机
          uint32_t notifyVal = ulTaskNotifyTake(pdFALSE, 0);  // 非阻塞检查
          if (notifyVal > 0) {
            Serial.println("🛑 [忙等期间] 收到紧急停机通知！中止铁芯飞行补偿。");
            emergencyStop();
            return;  // 立即退出 coughTick
          }
        }
        
        Serial.println("[T=爆破点] 阀门全开，停泵，咳嗽瞬态爆发！");
        ledcWrite(PUMP_CHANNEL, 0);
        ledcWrite(LASER_CHANNEL, 1023);   // 激光随阀门全开同步点亮
        coughPhaseStartUs = micros();
        coughPhase = COUGH_BLAST;
      }
      break;

    // ---------- 阶段 2a：铁芯机械延迟补偿 (已在 COUGH_ATOMIZE 尾部精确处理) ----------
    case COUGH_VALVE_FLY:
      // 保持状态机兼容性，直接过渡
      coughPhase = COUGH_BLAST;
      break;

    // ---------- 阶段 2b：黄金爆破 ----------
    case COUGH_BLAST:
      if (elapsedUs >= t_blast_us) {
        Serial.println("[T=清风扫膛] 关闭雾化（断水），清风扫膛开始...");
        digitalWrite(LX8201_PB3_PIN, LOW);   // 断水
        coughPhaseStartUs = micros();
        coughPhase = COUGH_SWEEP;
      }
      break;

    // ---------- 阶段 3：清风扫膛 ----------
    case COUGH_SWEEP:
      if (elapsedUs >= t_sweep_us) {
        Serial.println("[T=结束] 关闭电磁阀，咳嗽周期安全结束。");
        digitalWrite(VALVE_PIN, LOW);
        ledcWrite(LASER_CHANNEL, 0);         // 激光同步熄灭
        Serial.println("--- 咳嗽周期结束，系统安全闭锁 ---\n");
        coughPhase = COUGH_IDLE;
        sysState   = SYS_IDLE;               // 回到空闲状态
      }
      break;

    case COUGH_IDLE:
    default:
      break;
  }
}

// ==========================================
// 清洗排空状态机 Tick（非阻塞，持续 30 秒）
// ==========================================
void purgeTick() {
  unsigned long elapsedUs = micros() - purgeStartUs;
  
  // 30,000,000 微秒 = 30 秒
  if (elapsedUs >= 30000000UL) {
    Serial.println("[T=30s] 🧹 管道清洗排空完成！自动关闭气泵和阀门。");
    ledcWrite(PUMP_CHANNEL, 0);
    digitalWrite(VALVE_PIN, LOW);
    sysState = SYS_IDLE;
  }
}

// ==========================================
// 【优化5】指令处理函数 —— 零堆分配版
//   用 strstr() 替代 String.indexOf()，直接操作 char[]
//   消除所有 String 对象的堆分配，防止长时间运行后堆碎片化
// ==========================================
void processCommand(const char* cmd) {

  // --- 1. 紧急全停：任何状态下都优先响应 ---
  if (strstr(cmd, "STOP") != NULL) {
    emergencyStop();
    return;
  }

  // --- 2. 自动化动作执行中：拒绝其他指令 ---
  if (sysState == SYS_COUGHING || sysState == SYS_PURGING) {
    Serial.println("⚠️ [状态机] 自动化序列执行中，仅接受 STOP 指令");
    return;
  }

  // ==========================================
  // 以下指令仅在 IDLE 或 MANUAL_OVERRIDE 状态下执行
  // ==========================================

  // --- 【切换顶层状态的指令】 ---
  if (strstr(cmd, "ENTER_MANUAL") != NULL) {
    sysState = SYS_MANUAL_OVERRIDE;
    Serial.println("🔧 [状态机] 进入 SYS_MANUAL_OVERRIDE 手动模式（已屏蔽宏序列）");
    return;
  }
  if (strstr(cmd, "EXIT_MANUAL") != NULL) {
    emergencyStop();  // 退出调试时顺手关闭硬件更安全
    Serial.println("🔧 [状态机] 退出手动模式，回到 SYS_IDLE");
    return;
  }
  if (strstr(cmd, "START_PURGE") != NULL) {
    Serial.println("🧹 [状态机] 进入 SYS_PURGING，开始 30 秒强力清风扫膛...");
    ledcWrite(PUMP_CHANNEL, 1023);      // 满功率开泵
    digitalWrite(VALVE_PIN, HIGH);      // 保持阀门全开
    digitalWrite(LX8201_PB3_PIN, LOW);  // 绝对禁止雾化
    purgeStartUs = micros();
    sysState = SYS_PURGING;
    return;
  }

  // --- 【设置参数指令：动态修改时序】 ---
  // 上位机传过来的数值单位是 ms，需要在单片机内部转成 us (* 1000)
  const char* p;  // 指针复用，用于定位冒号后的数值

  if ((p = strstr(cmd, "SET_T_PRESS:")) != NULL) {
    int val_ms = atoi(p + 12);  // "SET_T_PRESS:" 长度 = 12
    t_pressurize_us = val_ms * 1000UL;
    Serial.printf("⚙️ [参数] 蓄压时间设为: %d ms\n", val_ms);
    return;
  }
  if ((p = strstr(cmd, "SET_T_ATOM:")) != NULL) {
    int val_ms = atoi(p + 11);
    t_atomize_us = val_ms * 1000UL;
    Serial.printf("⚙️ [参数] 蓄雾时间设为: %d ms\n", val_ms);
    return;
  }
  if ((p = strstr(cmd, "SET_T_BLAST:")) != NULL) {
    int val_ms = atoi(p + 12);
    t_blast_us = val_ms * 1000UL;
    Serial.printf("⚙️ [参数] 爆破时间设为: %d ms\n", val_ms);
    return;
  }
  if ((p = strstr(cmd, "SET_T_SWEEP:")) != NULL) {
    int val_ms = atoi(p + 12);
    t_sweep_us = val_ms * 1000UL;
    Serial.printf("⚙️ [参数] 扫膛时间设为: %d ms\n", val_ms);
    return;
  }

  // --- 【核心集成 1：启动完美咳嗽 (强制恢复 V6.0 黄金基准时序，但叠加动态前馈补偿)】 ---
  if (strstr(cmd, "COUGH_PERFECT") != NULL) {
    // 互锁保护：如果处于手动模式，拒绝执行咳嗽宏，防止气压突然爆破伤人
    if (sysState == SYS_MANUAL_OVERRIDE) {
      Serial.println("⚠️ [互锁保护] 处于手动调试模式，已屏蔽咳嗽宏指令！请先发送 EXIT_MANUAL。");
      return;
    }
    // 强制重置为默认基准参数 (除了开启延迟需要动态计算)
    t_pressurize_us = 2800000UL;
    t_atomize_us    = 193127UL;
    t_blast_us      = 50000UL;
    t_sweep_us      = 50000UL;
    
    // 【完美咳嗽强制满载】气泵会以满速运行 2.8s，必定达到最大压力 0.08MPa
    // 因此这里强行固定为最高档的动态前馈补偿（不再受上位机全局气压影响）
    float comp_delay_ms = get_compensated_delay(0.08);
    t_valve_fly_us = (unsigned long)(comp_delay_ms * 1000.0);
    
    Serial.println("\n--- V1. 完美咳嗽启动 (满载 0.08MPa + 最高级动态前馈补偿) ---");
    Serial.printf("[T=0] 气泵开始蓄压 (预设时间: %lu ms)...\n", t_pressurize_us / 1000);
    coughPumpSpeed = 1023; // 默认满速
    ledcWrite(PUMP_CHANNEL, coughPumpSpeed);   // 开泵
    coughPhaseStartUs = micros();              // 记下启动时间
    coughPhase = COUGH_PRESSURIZE;             // 进入咳嗽子状态机
    sysState   = SYS_COUGHING;                 // 切换到咳嗽状态
    return;
  }

  // --- 【核心集成 2：启动自定义咳嗽 (使用上位机调节后的参数)】 ---
  if (strstr(cmd, "COUGH_CUSTOM") != NULL) {
    if (sysState == SYS_MANUAL_OVERRIDE) {
      Serial.println("⚠️ [互锁保护] 处于手动调试模式，已屏蔽咳嗽宏指令！请先发送 EXIT_MANUAL。");
      return;
    }
    
    // 【点睛之笔：执行前馈动态补偿】
    float comp_delay_ms = get_compensated_delay(current_target_pressure_mpa);
    t_valve_fly_us = (unsigned long)(comp_delay_ms * 1000.0);
    
    Serial.println("\n--- V2. 自定义咳嗽启动 (应用动态前馈补偿) ---");
    Serial.printf("[算法] 当前背压 %.3f MPa -> 计算出机械延迟补偿: %.3f ms\n", current_target_pressure_mpa, comp_delay_ms);
    Serial.printf("[T=0] 气泵开始蓄压 (预设时间: %lu ms)...\n", t_pressurize_us / 1000);
    
    coughPumpSpeed = getPumpPWM(current_target_pressure_mpa);
    ledcWrite(PUMP_CHANNEL, coughPumpSpeed);   // 开泵
    
    coughPhaseStartUs = micros();              
    coughPhase = COUGH_PRESSURIZE;             
    sysState   = SYS_COUGHING;                 
    return;
  }

  // --- 【基础硬件控制指令】 ---
  if ((p = strstr(cmd, "SPEED_MPa:")) != NULL) {
    float mpa = atof(p + 10);
    current_target_pressure_mpa = mpa; // 保存用于动态补偿
    int pwmVal = getPumpPWM(mpa);
    ledcWrite(PUMP_CHANNEL, pwmVal);
    Serial.printf("[指令] 气泵气压 -> %.3f MPa (PWM=%d)\n", mpa, pwmVal);
  }

  // --- 【1b. 兼容旧版：SPEED: 直接PWM值】 ---
  else if ((p = strstr(cmd, "SPEED:")) != NULL) {
    int val = atoi(p + 6);
    ledcWrite(PUMP_CHANNEL, val);
  }

  // --- 【2. 单独控制：气泵开关】 ---
  else if (strstr(cmd, "PUMP_ON") != NULL) {
    ledcWrite(PUMP_CHANNEL, 1023);
  }
  else if (strstr(cmd, "PUMP_OFF") != NULL) {
    ledcWrite(PUMP_CHANNEL, 0);
  }

  // --- 【3. 单独控制：电磁阀（直接 ON/OFF）】 ---
  else if (strstr(cmd, "VALVE_ON") != NULL) {
    valveState = true;
    digitalWrite(VALVE_PIN, HIGH);
    Serial.println("🚰 [指令] 电磁阀 -> 开启");
  }
  else if (strstr(cmd, "VALVE_OFF") != NULL) {
    valveState = false;
    digitalWrite(VALVE_PIN, LOW);
    Serial.println("🚰 [指令] 电磁阀 -> 关闭");
  }

  // --- 【4. 单独控制：雾化（LX8201 PB3 GPIO25 电平控制）】 ---
  else if (strstr(cmd, "ATOM_ON") != NULL) {
    digitalWrite(LX8201_PB3_PIN, HIGH);
    Serial.println("💧 [指令] 雾化 -> 开启");
  }
  else if (strstr(cmd, "ATOM_OFF") != NULL) {
    digitalWrite(LX8201_PB3_PIN, LOW);
    Serial.println("💧 [指令] 雾化 -> 关闭");
  }

  // --- 【激光控制】 ---
  else if ((p = strstr(cmd, "LASER_PWM:")) != NULL) {
    int val = atoi(p + 10);
    ledcWrite(LASER_CHANNEL, val);
  }
  else if (strstr(cmd, "LASER_ON") != NULL) {
    ledcWrite(LASER_CHANNEL, 1023);
    Serial.println("🔆 [指令] 激光 -> 开启");
  }
  else if (strstr(cmd, "LASER_OFF") != NULL) {
    ledcWrite(LASER_CHANNEL, 0);
    Serial.println("🔆 [指令] 激光 -> 关闭");
  }
}

// ==========================================
// 【优化6】Core 0 专属网络服务任务 (FreeRTOS 队列版)
//   - 用 xQueueSend 替代手搓 spinlock，支持指令缓冲
//   - STOP 指令走 xTaskNotifyGive 快速通道，零延迟打断 Core 1
//   - 内置 WiFi 断连自动重连看门狗
// ==========================================
void networkTask(void *pvParameters) {
  Serial.printf("[Core 0] 无线通信任务成功建立，运行在核心 %d\n", xPortGetCoreID());

  while (1) {
    // 【优化7】WiFi 断连自动重连
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("⚠️ [Core 0] WiFi 断连！尝试重连...");
      WiFi.disconnect();
      WiFi.begin(ssid, password);
      
      // 最多等 10 秒重连
      int retryCount = 0;
      while (WiFi.status() != WL_CONNECTED && retryCount < 20) {
        vTaskDelay(pdMS_TO_TICKS(500));
        Serial.print(".");
        retryCount++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n✅ [Core 0] WiFi 重连成功！IP: %s\n", WiFi.localIP().toString().c_str());
      } else {
        Serial.println("\n❌ [Core 0] WiFi 重连失败，30 秒后重试...");
        vTaskDelay(pdMS_TO_TICKS(30000));
        continue;  // 跳过本轮网络处理
      }
    }

    // 正常网络指令接收
    WiFiClient client = server.available();
    if (client) {
      Serial.println("🔍 [Core 0 调试] 检测到客户端连接！");
      
      // 【优化8】用固定 char[] 接收，避免 String 堆分配
      char rawBuf[256] = {0};
      int  rawLen = 0;
      unsigned long readStart = millis();
      
      // 纯超时驱动读取（不依赖 client.connected()，防止远端关闭后过早退出）
      while (millis() - readStart < 100) {
        if (client.available()) {
          char c = client.read();
          if (c == '\r') break;
          if (rawLen < (int)sizeof(rawBuf) - 1) {
            rawBuf[rawLen++] = c;
          }
        } else {
          delay(1);  // 让出 CPU 给 lwIP 协议栈处理 TCP 缓冲
        }
      }
      rawBuf[rawLen] = '\0';
      client.flush();
      
      Serial.printf("🔍 [Core 0 调试] 原始数据 (%d 字节): [%s]\n", rawLen, rawBuf);

      // 解析 $...# 协议帧
      char* frameStart = strchr(rawBuf, '$');
      if (frameStart != NULL) {
        char* frameEnd = strchr(frameStart + 1, '#');
        if (frameEnd != NULL) {
          // 提取帧内容到固定缓冲区
          int cmdLen = frameEnd - frameStart - 1;
          if (cmdLen > 0 && cmdLen < CMD_MAX_LEN) {
            char cmdBuf[CMD_MAX_LEN] = {0};
            memcpy(cmdBuf, frameStart + 1, cmdLen);
            cmdBuf[cmdLen] = '\0';
            
            Serial.printf("🔍 [Core 0 调试] 解析成功，指令: [%s]\n", cmdBuf);
            
            // 【优化3】STOP 走快速通道：先通知 Core 1 立即中止，再入队
            if (strstr(cmdBuf, "STOP") != NULL) {
              xTaskNotifyGive(controlTaskHandle);  // 零延迟唤醒 Core 1
            }
            
            // 通过 FreeRTOS 队列发送到 Core 1
            if (xQueueSend(cmdQueue, cmdBuf, 0) != pdTRUE) {
              Serial.println("⚠️ [Core 0] 指令队列已满，丢弃本条指令");
            } else {
              Serial.println("🔍 [Core 0 调试] 指令已入队，等待 Core 1 消费");
            }
          } else {
            Serial.printf("🔍 [Core 0 调试] 帧长度异常: cmdLen=%d\n", cmdLen);
          }
        } else {
          Serial.println("🔍 [Core 0 调试] 未找到帧尾 '#'");
        }
      } else {
        Serial.println("🔍 [Core 0 调试] 未找到帧头 '$'");
      }
    }
    // 释放 CPU 所有权，防止 watchdog 喂狗并让出时间片给底层 Wi-Fi 协议栈
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// ==========================================
// setup()
// ==========================================
void setup() {
  Serial.begin(115200);
  
  // 【优化2】获取 Arduino 主任务句柄（loop 跑在这个任务上）
  controlTaskHandle = xTaskGetCurrentTaskHandle();
  
  pinMode(VALVE_PIN, OUTPUT);
  digitalWrite(VALVE_PIN, LOW); 
  
  pinMode(LX8201_PB3_PIN, OUTPUT);
  digitalWrite(LX8201_PB3_PIN, LOW);  // 雾化默认关闭

  ledcSetup(PUMP_CHANNEL, pwmFreq, pwmResolution);  // 2.x: 配置通道
  ledcAttachPin(PUMP_PIN, PUMP_CHANNEL);             // 2.x: 绑定引脚到通道
  ledcWrite(PUMP_CHANNEL, 0);

  ledcSetup(LASER_CHANNEL, pwmFreq, pwmResolution); // 激光 PWM 配置
  ledcAttachPin(LASER_PIN, LASER_CHANNEL);
  ledcWrite(LASER_CHANNEL, 0);

  // 【优化1】创建 FreeRTOS 指令队列
  cmdQueue = xQueueCreate(CMD_QUEUE_DEPTH, CMD_MAX_LEN);
  if (cmdQueue == NULL) {
    Serial.println("❌ [致命错误] 指令队列创建失败！系统挂起。");
    while (1) { delay(1000); }  // 停在这里，不允许继续
  }

  Serial.println("\n--- 系统启动中 (FreeRTOS 双核优化架构) ---");
  Serial.print("尝试连接 Wi-Fi 热点: ");
  Serial.println(ssid);
  
  // ===============================================
  // 强行锁死静态 IP，防止电脑热点 DHCP 乱分配
  IPAddress local_IP(192, 168, 137, 100);
  IPAddress gateway(192, 168, 137, 1);
  IPAddress subnet(255, 255, 255, 0);

  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("STA Failed to configure");
  }
  // ===============================================

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  
  Serial.println("\n✅ Wi-Fi 连接成功！");
  server.begin();
  Serial.print("📍 当前局域网 IP 地址为: ");
  Serial.println(WiFi.localIP());
  Serial.println("=========================================");
  Serial.println("📊 系统状态: SYS_IDLE (空闲待命)");
  Serial.println("=========================================");

  // 创建 Core 0 专用网络通信任务
  xTaskCreatePinnedToCore(
    networkTask,          /* 任务函数 */
    "NetworkTask",        /* 任务名称 */
    8192,                 /* 任务栈大小 */
    NULL,                 /* 传入参数 */
    1,                    /* 优先级 */
    &networkTaskHandle,   /* 【优化2】保存任务句柄 */
    0                     /* 绑定在核心 0 */
  );
  
  Serial.println("🚀 [双核系统] Core 0 网络线程已拉起，与 Core 1 精密控制硬隔离。");
  Serial.printf("📊 [FreeRTOS] 指令队列深度: %d | 单条指令上限: %d 字节\n", CMD_QUEUE_DEPTH, CMD_MAX_LEN);
}

// ==========================================
// loop() —— 主循环，FreeRTOS 双核优化架构
//   ① 顶层状态机 Tick（Core 1，每帧运行）
//   ② 从 FreeRTOS 队列消费指令（零堆分配）
//   ③ 周期性健康监控（栈水位检查）
// ==========================================

static unsigned long lastHealthCheckUs = 0;
static const unsigned long HEALTH_CHECK_INTERVAL_US = 30000000UL;  // 30 秒一次

void loop() {

  // ===== ① 状态机 Tick (Core 1) =====
  if (sysState == SYS_COUGHING) {
    coughTick();
  } else if (sysState == SYS_PURGING) {
    purgeTick();
  }

  // ===== ② 从 FreeRTOS 队列消费指令（零堆分配） =====
  char cmdBuf[CMD_MAX_LEN];
  if (xQueueReceive(cmdQueue, cmdBuf, 0) == pdTRUE) {
    Serial.printf("📩 [Core 1 收到指令] %s\n", cmdBuf);
    processCommand(cmdBuf);
  }

  // ===== ③ 周期性健康监控 =====
  unsigned long nowUs = micros();
  if (nowUs - lastHealthCheckUs >= HEALTH_CHECK_INTERVAL_US) {
    lastHealthCheckUs = nowUs;
    
    // 打印各任务栈的剩余高水位（单位：word = 4 bytes）
    // 如果接近 0 说明栈快溢出了，需要增大 xTaskCreatePinnedToCore 的栈参数
    UBaseType_t controlStack  = uxTaskGetStackHighWaterMark(controlTaskHandle);
    UBaseType_t networkStack  = uxTaskGetStackHighWaterMark(networkTaskHandle);
    Serial.printf("📊 [健康监控] Core1 控制栈余量: %u words | Core0 网络栈余量: %u words | 队列剩余: %u/%d\n",
                  controlStack, networkStack,
                  (unsigned)uxQueueSpacesAvailable(cmdQueue), CMD_QUEUE_DEPTH);
  }
}