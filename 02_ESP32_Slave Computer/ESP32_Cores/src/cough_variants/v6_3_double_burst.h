// ==========================================
// V6.3 【连咳版】双脉冲连续咳嗽
// 总周期: ~4600ms | 两次独立的咳嗽脉冲
// 设计思路: 模拟现实中连续咳两声的场景
//   - 第一咳: 短促前奏咳 (蓄压1000ms + 快喷)
//   - 间隔: 200ms自然停顿 (包含关机防抖)
//   - 第二咳: 主力重咳 (利用残余压力 + 重新蓄压)
//   - 适合模拟"咳咳"连续咳嗽场景
// ==========================================
void triggerPerfectCough(int pumpSpeed) {
  Serial.println("\n--- 🔥 V6.3 连咳序列启动 (双脉冲版) ---");

  // ============ 第一咳：前奏短咳 ============
  Serial.println("=== 第一咳 (前奏) ===");

  // 【1-0】短蓄压 (0-1000ms)
  Serial.println("[T=0] 气泵短蓄压...");
  ledcWrite(PUMP_CHANNEL, pumpSpeed * 2 / 3); // 67%功率
  delay(1000);

  // 【1-1】预按开机键 (1000-1200ms)
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(200);

  // 【1-2】触发开机 (T=1200ms)
  Serial.println("[T=1200] 第一咳出雾！");
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(50);

  // 【1-3】快速关机预按 (T=1250ms)
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(100);

  // 【1-4】第一咳喷射 (T=1350ms)
  Serial.println("[T=1350] 第一咳喷射！(30ms)");
  digitalWrite(VALVE_PIN, HIGH);
  delay(30);

  // 【1-5】关阀 + 补满关机防抖 (T=1380ms)
  digitalWrite(VALVE_PIN, LOW);
  delay(70); // 补满到200ms关掉雾化

  // 【1-6】关雾 (T=1450ms)
  digitalWrite(ATOMIZER_KEY, LOW);

  // ============ 间隔：自然停顿 ============
  Serial.println("[T=1450] 短暂停顿...");
  delay(200);

  // ============ 第二咳：主力重咳 ============
  Serial.println("=== 第二咳 (主力) ===");

  // 【2-0】重新蓄压 (1650-3150ms)
  Serial.println("[T=1650] 气泵重新满功率蓄压！");
  ledcWrite(PUMP_CHANNEL, pumpSpeed); // 满功率
  delay(1500);

  // 【2-1】预按开机键 (3150-3350ms)
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(200);

  // 【2-2】触发开机 (T=3350ms)
  Serial.println("[T=3350] 第二咳出雾！");
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(50);

  // 【2-3】产雾积累 (T=3400ms)
  Serial.println("[T=3400] 浓雾积累中...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(150);

  // 【2-4】主力爆破 (T=3550ms)
  Serial.println("[T=3550] 第二咳主力爆破！(80ms)");
  digitalWrite(VALVE_PIN, HIGH);
  delay(50); // 关机键按满200ms

  // 【2-5】关雾 + 扫尾 (T=3600ms)
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(30); // 阀门继续开着扫尾

  // 【2-6】彻底闭锁 (T=3630ms)
  digitalWrite(VALVE_PIN, LOW);
  Serial.println("--- ✅ 连咳周期结束，系统安全闭锁 ---\n");
}
