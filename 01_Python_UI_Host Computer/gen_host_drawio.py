import os

drawio_xml = """<mxfile host="Electron" modified="2026-06-18T00:00:00.000Z" agent="Mozilla/5.0" version="20.3.0" type="device">
  <diagram id="diagram_1" name="Page-1">
    <mxGraphModel dx="1200" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- Background Layers -->
        <mxCell id="Layer4" value="【4】双轨反馈与指令下发层" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;verticalAlign=bottom;fontSize=16;fontStyle=1;opacity=50;" vertex="1" parent="1">
          <mxGeometry x="80" y="80" width="660" height="230" as="geometry" />
        </mxCell>
        <mxCell id="Layer3" value="【3】核心算法决策层" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;verticalAlign=bottom;fontSize=16;fontStyle=1;opacity=50;" vertex="1" parent="1">
          <mxGeometry x="80" y="350" width="660" height="180" as="geometry" />
        </mxCell>
        <mxCell id="Layer2" value="【2】数据预处理层" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;verticalAlign=bottom;fontSize=16;fontStyle=1;opacity=50;" vertex="1" parent="1">
          <mxGeometry x="80" y="570" width="660" height="150" as="geometry" />
        </mxCell>
        <mxCell id="Layer1" value="【1】通信与抗抖动缓冲层" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;verticalAlign=bottom;fontSize=16;fontStyle=1;opacity=50;" vertex="1" parent="1">
          <mxGeometry x="80" y="760" width="660" height="150" as="geometry" />
        </mxCell>

        <!-- Layer 1 Nodes -->
        <mxCell id="C1" value="TCP/IP&lt;br&gt;异步接收线程" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="160" y="790" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="C2" value="Jitter Buffer&lt;br&gt;抗抖动环形队列" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="500" y="780" width="140" height="80" as="geometry" />
        </mxCell>
        <mxCell id="Edge_C1_C2" edge="1" parent="1" source="C1" target="C2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Layer 2 Nodes -->
        <mxCell id="P1" value="基线漂移消除&lt;br&gt;与零偏置归一" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="120" y="600" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="P2" value="VL53L1X&lt;br&gt;平方反比衰减补偿" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="340" y="600" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="P3" value="滑动平均平滑&lt;br&gt;宏观包络提取" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="560" y="600" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="Edge_C2_P1" edge="1" parent="1" source="C2" target="P1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="570" y="740" />
              <mxPoint x="190" y="740" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="Edge_P1_P2" edge="1" parent="1" source="P1" target="P2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="Edge_P2_P3" edge="1" parent="1" source="P2" target="P3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Layer 3 Nodes -->
        <mxCell id="A1" value="理论左路：&lt;br&gt;HGW 生理参数解析&lt;br&gt;Gupta靶点推演" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="120" y="410" width="150" height="70" as="geometry" />
        </mxCell>
        <mxCell id="A2" value="实测右路：&lt;br&gt;波形绝对幅值提取&lt;br&gt;PVT达峰时间锁定" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="550" y="410" width="150" height="70" as="geometry" />
        </mxCell>
        <mxCell id="DTW" value="FastDTW&lt;br&gt;动态时间规整&lt;br&gt;(形态打分&amp;amp;量化误差)" style="rhombus;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="310" y="375" width="200" height="100" as="geometry" />
        </mxCell>
        <mxCell id="Edge_P3_A2" edge="1" parent="1" source="P3" target="A2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="Edge_A1_DTW" edge="1" parent="1" source="A1" target="DTW">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="Edge_A2_DTW" edge="1" parent="1" source="A2" target="DTW">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Layer 4 Nodes -->
        <mxCell id="F1" value="前馈标定：&lt;br&gt;气压-PVT 粗调锁定" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="120" y="100" width="150" height="60" as="geometry" />
        </mxCell>
        <mxCell id="F2" value="SISO反馈 1：&lt;br&gt;微调 ATOM 蓄雾" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="335" y="100" width="150" height="60" as="geometry" />
        </mxCell>
        <mxCell id="F3" value="SISO反馈 2：&lt;br&gt;微调 BLAST 开阀" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="550" y="100" width="150" height="60" as="geometry" />
        </mxCell>
        <mxCell id="CMD" value="组装微秒级指令帧" style="shape=document;whiteSpace=wrap;html=1;boundedLbl=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="340" y="210" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="Edge_DTW_F2" edge="1" parent="1" source="DTW" target="F2">
          <mxGeometry relative="1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="Edge_DTW_F3" edge="1" parent="1" source="DTW" target="F3">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="490" y="360" />
              <mxPoint x="625" y="360" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="Edge_F1_CMD" edge="1" parent="1" source="F1" target="CMD">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="195" y="240" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="Edge_F2_CMD" edge="1" parent="1" source="F2" target="CMD">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="Edge_F3_CMD" edge="1" parent="1" source="F3" target="CMD">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="625" y="240" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- External Inputs/Outputs -->
        <mxCell id="In_ESP" value="STM32F407 边缘端上传" style="ellipse;whiteSpace=wrap;html=1;fillColor=#e3c800;strokeColor=#B09500;fontColor=#000000;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="170" y="960" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="Edge_In_C1" edge="1" parent="1" source="In_ESP" target="C1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="Out_ESP" value="ESP32 边缘端执行" style="ellipse;whiteSpace=wrap;html=1;fillColor=#e3c800;strokeColor=#B09500;fontColor=#000000;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="350" y="-10" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="Edge_CMD_Out" edge="1" parent="1" source="CMD" target="Out_ESP">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""

out_dir = r"D:\02Projects\01Simulated-Droplet-Device\docs\研电赛\论文\论文照片"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

out_file = os.path.join(out_dir, "上位机软件架构与分类决策流程图_新版.drawio")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(drawio_xml)

print("Drawio file created at:", out_file)
