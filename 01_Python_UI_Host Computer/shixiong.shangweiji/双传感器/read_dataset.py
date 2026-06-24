import csv

import pandas as pd
import pymysql
import json
from typing import Optional, Dict, List

from matplotlib import pyplot as plt


def read_specific_record(row_number: int) -> Optional[Dict[str, List]]:
    """
    按行号读取指定实验记录并解析传感器数据
    参数：
        row_number - 要读取的记录行号（从1开始）
    返回：
        {
            "metadata": 基础信息,
            "sensor_data": 传感器数值列表
        }
    """
    # 参数验证
    if not isinstance(row_number, int) or row_number < 1:
        raise ValueError("行号必须为大于0的整数")

    connection = None
    try:
        # 建立数据库连接（参数与存储代码一致）
        connection = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="12345678",
            database="dataset",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # 构造分页查询语句
            query = """
                SELECT 
                    id,
                    class_result,
                    droplet_data,
                    sum_acc_data,
                    sum_gyro_data,
                    temp,
                    distance,
                    UNIX_TIMESTAMP(create_time) as timestamp
                FROM yanzheng_data
                ORDER BY id ASC
                LIMIT 1 OFFSET %s
            """
            cursor.execute(query, (row_number - 1,))
            record = cursor.fetchone()

        if not record:
            return None

        # 解析JSON数据到列表
        sensor_lists = {
            "droplet_data": json.loads(record.pop("droplet_data")),
            "sum_acc_data": json.loads(record.pop("sum_acc_data")),
            "sum_gyro_data": json.loads(record.pop("sum_gyro_data"))
        }

        # 添加可读标签
        class_names = ["稳定状态下飞沫信号", "自呼吸干扰信号",
                       "气流扰动信号", "运动状态下飞沫信号"]
        record["class_label"] = class_names[record["class_result"]]

        # 转换时间戳格式
        record["timestamp"] = pd.to_datetime(record["timestamp"], unit="s")

        return {
            "metadata": record,
            "sensor_data": sensor_lists
        }

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"数据解析错误: {e}")
        return None
    except KeyError as e:
        print(f"字段缺失: {e}")
        return None
    finally:
        if connection:
            connection.close()


def visualize_droplet_data(data: List[float], title: str = "飞沫传感器数据时序曲线") -> None:
    """
    可视化飞沫传感器时序数据
    参数：
        data - 飞沫数据列表
        title - 图表标题
    """
    plt.figure(figsize=(12, 6))

    # 生成横坐标采样点
    x = range(len(data))

    # 绘制曲线
    plt.plot(x, data,
             color='steelblue',
             linewidth=1.5,
             marker='o',
             markersize=3,
             markerfacecolor='red')

    # 设置图表样式
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("采样点序号", fontsize=12)
    plt.ylabel("传感器数值", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def save_droplet_csv(data: List[float], filename: str = "droplet_data.csv") -> None:
    """
    将飞沫数据按行存储到CSV文件
    参数：
        data - 飞沫数据列表
        filename - 存储文件名
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 添加表头
        writer.writerow(["采样值"])
        # 按行写入每个数据点
        for value in data:
            writer.writerow([round(value, 4)])  # 保留4位小数


def read_and_visualize_record(row_number: int) -> Optional[Dict]:
    """
    读取指定记录并可视化+保存飞沫数据
    返回：
        包含元数据和传感器数据的字典
    """
    result = read_specific_record(row_number)

    if result and result['sensor_data']['droplet_data']:
        # 触发可视化
        visualize_droplet_data(
            result['sensor_data']['droplet_data'],
            title=f"第{row_number}条记录飞沫数据 (ID: {result['metadata']['id']})"
        )
        # 保存CSV文件
        save_droplet_csv(
            result['sensor_data']['droplet_data'],
            f"droplet_row_{row_number}_id_{result['metadata']['id']}.csv"  # 添加ID防重复
        )
    return result


# 在main中添加文件保存提示
if __name__ == "__main__":
    target_row = 50
    result = read_and_visualize_record(target_row)

    if result:
        print(f"\n=== 数据分析报告 ===")
        print(f"记录时长: {len(result['sensor_data']['droplet_data']) / 100:.2f} 秒")
        print(f"\n=== 数据存储信息 ===")
        print(
            f"已保存{len(result['sensor_data']['droplet_data'])}个数据点到 droplet_row_{target_row}_id_{result['metadata']['id']}.csv")