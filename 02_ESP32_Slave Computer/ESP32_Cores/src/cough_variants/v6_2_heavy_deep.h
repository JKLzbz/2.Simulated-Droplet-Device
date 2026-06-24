// ==========================================
// V6.2 【重咳版】深度剧烈咳嗽
// 总周期: 3380ms | 蓄压2500ms | 产雾350ms | 阀门100ms+扫尾80ms
// 设计思路: 高压蓄压，长时间浓雾积累，大口径爆破
//   - 2500ms超长蓄压，管道压力更高
//   - 雾化持续350ms，浓雾充分填满腔体
//   - 阀门开100ms，大量飞沫猛烈喷出
//   - 适合模拟剧烈咳嗽/深咳场景
// ==========================================
void triggerPerfectCough(int pumpSpeed) {
  Serial.println("\n--- 💥 V6.2 重咳序列启动 (剧烈爆破版) ---");

  // 【阶段 0】超长蓄压 (0-2500ms)
  Serial.println("[T=0] 气泵全功率超长蓄压！");
  ledcWrite(PUMP_CHANNEL, pumpSpeed); // 满功率
  delay(2500);

  // 【阶段 1】预按开机键 (2500-2700ms)
  Serial.println("[T=2500] 预按开机键 200ms...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(200);

  // 【阶段 2】触发开机 (T=2700ms)
  Serial.println("[T=2700] 停泵！松开开机键 -> 雾化板【猛烈产雾】！");
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(ATOMIZER_KEY, LOW);

  delay(50); // 确保下降沿被识别

  // 【阶段 3】预按关机键 & 超长产雾 (T=2750ms)
  Serial.println("[T=2750] 预按关机键，等待300ms让浓雾充分填满...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(150); // 先积150ms雾

  // 【阶段 4】第一波爆破射击 (T=2900ms)
  Serial.println("[T=2900] 电磁阀大口径爆破！(维持100ms)");
  digitalWrite(VALVE_PIN, HIGH);
  // 150ms + 100ms > 200ms! 关机键在 T=2950 时就按满200ms了
  // 但我们在阀门开启期间不松手，让爆破和关雾几乎同步
  delay(50); // 此时关机键刚好按满200ms

  // 【阶段 5】关雾但保持阀门 (T=2950ms)
  Serial.println("[T=2950] 松开关机键 -> 断雾！阀门继续大口径扫尾...");
  digitalWrite(ATOMIZER_KEY, LOW); // 关雾
  delay(50); // 阀门继续开着，纯压力扫尾

  // 【阶段 6】纯风扫尾 (T=3000ms)
  Serial.println("[T=3000] 重新启动气泵做压力扫尾...");
  ledcWrite(PUMP_CHANNEL, pumpSpeed / 2); // 50%功率补压扫尾
  delay(300);

  // 【阶段 7】彻底闭锁 (T=3300ms)
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(VALVE_PIN, LOW);
  Serial.println("--- ✅ 重咳周期结束，系统安全闭锁 ---\n");
}
