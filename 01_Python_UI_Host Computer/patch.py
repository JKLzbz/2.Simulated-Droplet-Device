import re

file_path = 'D:/02Projects/01Simulated-Droplet-Device/01_Python_UI_Host Computer/00.Main_UI/main3.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

flush_pattern = r'        # --- 基于真实时钟的 PID 动态平滑控制器 \(Real-Time P-Controller\) ---.*?        for droplet, distance, temp in q_data:'
replacement = '''        # --- 纯正实时示波器算法 (Pure Real-Time Constant-Speed Oscilloscope) ---
        t_now = time.perf_counter()
        dt = t_now - getattr(self, '_last_draw_t', t_now - 0.05)
        self._last_draw_t = t_now
        
        if dt > 0.5:
            dt = 0.05
            
        buf_len = len(self._jitter_buf)
        if getattr(self, '_force_prefill', True):
            if buf_len < 100:  
                return  # 攒够 0.2 秒底水发车
            self._force_prefill = False
            
        # 绝对死锁在 500Hz 物理速度，无论积压多少，绝对不允许“快进”或者“慢放”
        target_hz = 500.0
        
        ideal_consume = target_hz * dt + getattr(self, '_consume_carry', 0.0)
        consume_n = int(ideal_consume)
        self._consume_carry = ideal_consume - consume_n
        
        n = min(consume_n, buf_len)
        if n == 0:
            return
            
        if n == buf_len:
            self._consume_carry = 0.0
            
        q_data = [self._jitter_buf.popleft() for _ in range(n)]
        
        # 【杀手锏】：如果因为电脑卡顿，导致蓄水池积压了超过 0.5 秒 (250个点) 的数据，
        # 绝对不能像蛇一样“快爬”去追赶！直接一刀切，把过期的历史数据扔进垃圾桶，强行对齐到现在！
        if len(self._jitter_buf) > 250:
            drop_count = len(self._jitter_buf) - 100
            for _ in range(drop_count):
                self._jitter_buf.popleft()
            
        # 提取极准的采样点 (甩掉脏数据)
        for droplet, distance, temp in q_data:'''

content = re.sub(flush_pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
