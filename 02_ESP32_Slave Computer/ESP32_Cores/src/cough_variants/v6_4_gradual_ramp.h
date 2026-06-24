// ==========================================
// V6.4 【渐进版】渐进式蓄压 + 持续雾化喷射
// 总周期: ~3500ms | 气泵渐进加速 | 长雾化 | 阀门渐开渐关
// 设计思路: 模拟缓慢酝酿后爆发的深度咳嗽
//   - 气泵从0渐进到满功率(模拟肺部逐渐收缩)
//   - 更长的雾化窗口产生更浓密的飞沫
//   - 阀门用PWM模拟渐开效果(如果硬件支持)
//   - 适合模拟慢性咳嗽/深呼吸后咳嗽场景
// ==========================================
void triggerPerfectCough(int pumpSpeed) {
  Serial.println("\n--- 🌊 V6.4 渐进咳嗽序列启动 (渐进蓄压版) ---");

  // 【阶段 0】渐进蓄压 (0-2000ms)
  // 分10步从0加速到满功率，每步200ms
  Serial.println("[T=0] 气泵渐进蓄压...");
  for (int step = 1; step <= 10; step++) {
    int currentSpeed = pumpSpeed * step / 10;
    ledcWrite(PUMP_CHANNEL, currentSpeed);
    delay(200);
  }
  // T=2000ms，气泵已达满功率

  // 【阶段 1】满功率维持 (2000-2200ms)
  Serial.println("[T=2000] 满功率维持200ms...");
  delay(200);

  // 【阶段 2】预按开机键 (2200-2400ms)
  Serial.println("[T=2200] 预按开机键 200ms...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(200);

  // 【阶段 3】触发开机 (T=2400ms)
  Serial.println("[T=2400] 松开开机键 -> 雾化板出雾！气泵降至半速维持背压...");
  digitalWrite(ATOMIZER_KEY, LOW);
  ledcWrite(PUMP_CHANNEL, pumpSpeed / 3); // 降到1/3维持轻微背压
  delay(50);

  // 【阶段 4】长时间产雾 + 预按关机键 (T=2450ms)
  Serial.println("[T=2450] 预按关机键，长时间产雾250ms...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(150); // 先产150ms雾

  // 【阶段 5】开阀爆破 + 气泵瞬间全速 (T=2600ms)
  Serial.println("[T=2600] 阀门开！气泵瞬间全速助推！");
  ledcWrite(PUMP_CHANNEL, pumpSpeed); // 气泵瞬间拉满
  digitalWrite(VALVE_PIN, HIGH);
  delay(50); // 关机键按满200ms

  // 【阶段 6】关雾，气泵+阀门继续 (T=2650ms)
  Serial.println("[T=2650] 断雾！气泵助推扫尾...");
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(100); // 纯压力扫尾100ms

  // 【阶段 7】气泵渐停 (T=2750ms)
  Serial.println("[T=2750] 气泵渐停...");
  for (int step = 10; step >= 0; step--) {
    ledcWrite(PUMP_CHANNEL, pumpSpeed * step / 10);
    delay(50);
  }
  // T=3300ms

  // 【阶段 8】彻底闭锁 (T=3300ms)
  digitalWrite(VALVE_PIN, LOW);
  ledcWrite(PUMP_CHANNEL, 0);
  Serial.println("--- ✅ 渐进咳嗽周期结束，系统安全闭锁 ---\n");
}
