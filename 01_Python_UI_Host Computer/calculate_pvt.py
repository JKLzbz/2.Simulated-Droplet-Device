import os
import pandas as pd
import numpy as np

# 设定微观波形数据文件夹路径
MICRO_DATA_DIR = r"D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\04micro_data"

def analyze_pvt():
    print("=" * 70)
    print("       气压-PVT 标定辅助分析工具 (支持多目录分类)")
    print("=" * 70)
    
    if not os.path.exists(MICRO_DATA_DIR):
        print(f"找不到文件夹: {MICRO_DATA_DIR}")
        return
        
    print(f"{'气压分组':<10} | {'文件名':<30} | {'最大振幅 (pF)':<15} | {'PVT 达峰时间 (ms)':<15}")
    print("-" * 80)
    
    # 获取所有的气压子文件夹，倒序排序（0.10 到 0.01）
    subfolders = sorted([f for f in os.listdir(MICRO_DATA_DIR) if os.path.isdir(os.path.join(MICRO_DATA_DIR, f))], reverse=True)
    subfolders.insert(0, "") # 加入根目录本身，用空字符串代表
    
    total_files = 0
    for folder in subfolders:
        folder_path = os.path.join(MICRO_DATA_DIR, folder)
        csv_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".csv")])
        
        if not csv_files:
            continue
            
        for i, file in enumerate(csv_files):
            total_files += 1
            filepath = os.path.join(folder_path, file)
            try:
                data = pd.read_csv(filepath, comment='#')
                
                if len(data.columns) > 1:
                    col_name = data.columns[-1]
                    vals = data[col_name].values
                else:
                    vals = data.iloc[:, 0].values
                    
                max_idx = np.argmax(vals)
                max_val_raw = vals[max_idx]
                
                # 提取前100个安静点作为基准底噪（因为冲线在 7000+ 以后才发生）
                baseline = np.mean(vals[0:100])
                
                # 计算相对峰值振幅
                relative_amp = max_val_raw - baseline
                
                # 寻找升 3pF 开始计数的起点
                start_idx = 0
                for j in range(len(vals)):
                    if vals[j] - baseline > 3.0:
                        start_idx = j
                        break
                
                # 计算达峰时间 PVT
                # 遵从物理真实采样率：500Hz，每个点 = 2ms
                pvt_ms = (max_idx - start_idx) * 2
                
                if pvt_ms < 0 or start_idx == 0:
                    pvt_ms = 0
                    relative_amp = 0.0
                    
                # 只在第一行打印组名，方便查看
                group_name = folder if i == 0 else ""
                print(f"{group_name:<10} | {file:<30} | {relative_amp:<15.2f} | {pvt_ms:<15}")
                
            except Exception as e:
                print(f"{folder:<10} | {file:<30} | 解析出错: {str(e)}")
        
        # 每组打完画一条分割线
        if csv_files:
            print("-" * 80)
            
    print(f"共分析完成 {total_files} 组测试波形数据。")

if __name__ == "__main__":
    analyze_pvt()
