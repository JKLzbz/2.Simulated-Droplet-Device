with open(r'D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\00.Main_UI\wifi_worker.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of emitting every time, we will rely on main3.py timer to fetch
# But we can also throttle the signal emission to at most 30Hz!
new_code = """
import time
# ... inside WiFiWorker
"""

# Let's just remove the signal emission from the inner loop and put it in a separate thread/timer?
# No, we can just throttle the emit inside the worker.
content = content.replace("self.data_received.emit()", "self._throttle_emit()")

inject = """    def _throttle_emit(self):
        now = time.time()
        if not hasattr(self, '_last_emit'):
            self._last_emit = 0
        if now - self._last_emit > 0.033: # Max ~30Hz
            self._last_emit = now
            self.data_received.emit()
"""
if 'def _throttle_emit' not in content:
    content = content.replace('def snapshot(self)', inject + '\n    def snapshot(self)')

with open(r'D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\00.Main_UI\wifi_worker.py', 'w', encoding='utf-8') as f:
    f.write(content)
