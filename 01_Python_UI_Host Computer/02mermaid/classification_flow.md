# 上位机数据处理与咳嗽变体分类决策流程

```mermaid
graph TD
    %% 节点定义
    Start([开始: 接收 WiFi TCP 字节流]) --> FrameSync{是否检测到帧头 0xAA 0xFF?}
    
    %% 帧校验逻辑
    FrameSync -- 否 --> DropBytes[滑动滑动窗口/丢弃错位字节]
    DropBytes --> Start
    
    FrameSync -- 是 --> StructUnpack[C-Struct 内存映射解包]
    StructUnpack --> Checksum{校验和 Checksum 是否通过?}
    
    Checksum -- 否 --> ErrorLog[丢弃当前帧并记录错误]
    ErrorLog --> Start
    
    %% 数据滤波与特征提取
    Checksum -- 是 --> ParseData[提取特征: ΔC 电容, a 加速度, D 距离]
    ParseData --> Filter電容[电容数据通过 N=5 滑动均值滤波]
    Filter電容 --> ExtractFeatures[计算特征峰值: ΔC_max, a_max, D_max]
    
    %% 启发式分类决策树
    ExtractFeatures --> Decision1{电容峰值 ΔC_max < 1.0 pF?}
    
    Decision1 -- 是/极微小液滴 --> ClassLight[分类结果: 轻度咳唾\n(RSD < 3.0%)]
    
    Decision1 -- 否/明显液滴 --> Decision2{最大飞行射程 D_max < 20 cm?}
    
    Decision2 -- 是/低射程大体积 --> ClassWet[分类结果: 中度湿咳\n(RSD < 3.0%)]
    Decision2 -- 否/高冲击高射程 --> ClassDry[分类结果: 重度干咳\n(RSD < 3.0%)]
    
    %% 输出与显示
    ClassLight --> OutputResult[上位机显示分类类别 & 实时波形绘制]
    ClassWet --> OutputResult
    ClassDry --> OutputResult
    
    OutputResult --> Start
    
    %% 样式美化
    classDef default fill:#F5F7FA,stroke:#90A4AE,stroke-width:2px,font-family:Microsoft YaHei;
    classDef classNode fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,font-weight:bold,color:#1B5E20;
    classDef startNode fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,font-weight:bold,color:#01579B;
    classDef judgeNode fill:#FFF9C4,stroke:#FBC02D,stroke-width:2px,color:#F57F17;
    
    class Start startNode;
    class FrameSync,Checksum,Decision1,Decision2 judgeNode;
    class ClassLight,ClassWet,ClassDry classNode;
```
