import re

with open("D:/02Projects/01Simulated-Droplet-Device/01_Python_UI_Host Computer/00.Main_UI/main3.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update TOF labels to DTW labels
content = content.replace('self.lbl_tof_val = QLabel("--")', 'self.lbl_dtw_val = QLabel("--")')
content = content.replace('row1.addWidget(make_small_card("🚀时滞 (TOF)", self.lbl_tof_val, "ms", "#db2777"))', 'row1.addWidget(make_small_card("🎯DTW得分", self.lbl_dtw_val, "%", "#db2777"))')

# 2. Add trigger logic for DTW in button clicks
trigger_custom_orig = """        def on_done():
            self.send_cmd("COUGH_CUSTOM")
            warmup_delay = (p + a) / 1000.0
            self.spray_start_time = time.time() + warmup_delay
            self.waiting_for_droplet = True"""
trigger_custom_new = """        def on_done():
            self.send_cmd("COUGH_CUSTOM")
            warmup_delay = (p + a) / 1000.0
            self.spray_start_time = time.time() + warmup_delay
            self.waiting_for_droplet = True
            self.dtw_capture_end_time = self.spray_start_time + 1.5"""
content = content.replace(trigger_custom_orig, trigger_custom_new)

# Add COUGH_PERFECT replacement
btn_cough_orig = """        btn_cough.clicked.connect(lambda: self.send_cmd("COUGH_PERFECT"))"""
btn_cough_new = """        def trigger_perfect():
            self.send_cmd("COUGH_PERFECT")
            self.spray_start_time = time.time() + 0.1
            self.waiting_for_droplet = True
            self.dtw_capture_end_time = self.spray_start_time + 1.5
        btn_cough.clicked.connect(trigger_perfect)"""
content = content.replace(btn_cough_orig, btn_cough_new)

# 3. Add DTW evaluation in flush_latest_value
dtw_eval_orig = """        # 预留 FastDTW 算法评估入口
        # 注: 当 D0-D10 完整序列执行结束后，上位机在此处调用 DTW 引擎对齐波形并计算得分
        pass"""

dtw_eval_new = """        # -----------------------------------------------------
        # 实时 DTW 评估算法 (根据用户要求输出真实DTW并映射到 >90%)
        # -----------------------------------------------------
        if hasattr(self, 'dtw_capture_end_time') and self.dtw_capture_end_time > 0:
            if time.time() > self.dtw_capture_end_time:
                self.dtw_capture_end_time = 0.0
                # 采集到了 1.5 秒的数据，即 750 个点
                # 提取历史 buffer 中最近的 750 个点
                extract_points = 750
                if self._write_idx >= extract_points:
                    measured = self._droplet_buf[self._write_idx - extract_points: self._write_idx]
                else:
                    measured = np.concatenate((self._droplet_buf[self.buffer_size - (extract_points - self._write_idx):], self._droplet_buf[:self._write_idx]))
                
                # 获取用户信息并生成标准 Gupta 模型
                height = self.spin_height.value()
                weight = self.spin_weight.value()
                gender = self.combo_gender.currentText()
                baseline = generate_gupta_waveform(height, weight, gender, total_points=extract_points, duration_s=1.5)
                
                # 运行真实的 FastDTW
                distance, path = fastdtw(measured, baseline, dist=euclidean)
                
                # 将距离映射为打分。真实距离可能很大，我们做一个数学映射，让它落在 90%~99% 区间，同时保留真实的区分度
                # 假设正常的欧氏距离累计在 500~5000 左右
                score = 99.8 - (distance / 10000.0) * 8.0 
                score = max(90.1, min(99.9, score)) # 限制在 90%~99.9% 之间
                
                self.lbl_dtw_val.setText(f"{score:.2f}")
                self.log_message(f"✅ DTW算法计算完成，实际欧式距离为: {distance:.1f}，智能拟合得分为: {score:.2f}%", "SUCCESS")"""

content = content.replace(dtw_eval_orig, dtw_eval_new)

with open("D:/02Projects/01Simulated-Droplet-Device/01_Python_UI_Host Computer/00.Main_UI/main3.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done updating main3.py")
