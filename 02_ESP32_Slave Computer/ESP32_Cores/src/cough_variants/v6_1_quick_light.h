// ==========================================
// V6.1 PWM=308, 其余与V6.0完全一致
// 总周期: 3500ms | 蓄压3000ms | 产雾250ms | 阀门50ms+扫膛50ms
// ==========================================
void triggerPerfectCough(int pumpSpeed) {
  const int fixedSpeed = 308;
  Serial.println("\n--- V6.1 低速气泵 (PWM=308) ---");

  Serial.println("[T=0] 气泵蓄压 PWM=308...");
  ledcWrite(PUMP_CHANNEL, fixedSpeed);
  delay(3000);

  Serial.println("[T=3000] 预按开机键 200ms...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(200);

  Serial.println("[T=3200] 停泵! 松开开机键 -> 出雾!");
  ledcWrite(PUMP_CHANNEL, 0);
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(50);

  Serial.println("[T=3250] 预按关机键, 等150ms产雾...");
  digitalWrite(ATOMIZER_KEY, HIGH);
  delay(150);

  Serial.println("[T=3400] 电磁阀开火! (50ms)");
  digitalWrite(VALVE_PIN, HIGH);
  delay(50);

  Serial.println("[T=3450] 断雾! 纯风扫尾...");
  digitalWrite(ATOMIZER_KEY, LOW);
  delay(50);

  digitalWrite(VALVE_PIN, LOW);
  Serial.println("--- V6.1 结束 ---\n");
}
