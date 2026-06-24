with open(r'D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\00.Main_UI\main3.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'self.lbl_temp_val.setText(f"{temp:.1f}")' in line:
        insert_idx = i
        break

lines.insert(insert_idx, '        if abs(temp - 2193.0) < 1.0 or temp > 1000:\n            temp = getattr(self, "last_valid_temp", 0.0)\n        else:\n            self.last_valid_temp = temp\n')

with open(r'D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\00.Main_UI\main3.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
