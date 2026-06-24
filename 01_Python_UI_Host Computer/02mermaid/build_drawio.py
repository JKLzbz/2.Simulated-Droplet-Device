import xml.etree.ElementTree as ET

# Define nodes with positions, sizes, and Draw.io style strings
nodes = {
    "Start": {"text": "开始: 接收 WiFi TCP 字节流", "x": 300, "y": 50, "w": 180, "h": 60, "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E1F5FE;strokeColor=#0288D1;strokeWidth=2;fontStyle=1;"},
    "FrameSync": {"text": "是否检测到帧头 0xAA 0xFF?", "x": 290, "y": 160, "w": 200, "h": 80, "style": "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=2;"},
    "DropBytes": {"text": "滑动滑动窗口/丢弃错位字节", "x": 50, "y": 170, "w": 180, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "StructUnpack": {"text": "C-Struct 内存映射解包", "x": 300, "y": 290, "w": 180, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "Checksum": {"text": "校验和 Checksum 是否通过?", "x": 290, "y": 390, "w": 200, "h": 80, "style": "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=2;"},
    "ErrorLog": {"text": "丢弃当前帧并记录错误", "x": 50, "y": 400, "w": 180, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "ParseData": {"text": "提取特征: ΔC 电容, a 加速度, D 距离", "x": 290, "y": 520, "w": 200, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "Filter電容": {"text": "电容数据通过 N=5 滑动均值滤波", "x": 300, "y": 620, "w": 180, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "ExtractFeatures": {"text": "计算特征峰值: ΔC_max, a_max, D_max", "x": 290, "y": 720, "w": 200, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"},
    "Decision1": {"text": "电容峰值 ΔC_max &lt; 1.0 pF?", "x": 290, "y": 820, "w": 200, "h": 80, "style": "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=2;"},
    "ClassLight": {"text": "分类结果: 轻度咳唾\n(RSD &lt; 3.0%)", "x": 60, "y": 940, "w": 160, "h": 60, "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontStyle=1;fontColor=#1B5E20;"},
    "Decision2": {"text": "最大飞行射程 D_max &lt; 20 cm?", "x": 510, "y": 820, "w": 200, "h": 80, "style": "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#FBC02D;strokeWidth=2;"},
    "ClassWet": {"text": "分类结果: 中度湿咳\n(RSD &lt; 3.0%)", "x": 420, "y": 940, "w": 160, "h": 60, "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontStyle=1;fontColor=#1B5E20;"},
    "ClassDry": {"text": "分类结果: 重度干咳\n(RSD &lt; 3.0%)", "x": 620, "y": 940, "w": 160, "h": 60, "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontStyle=1;fontColor=#1B5E20;"},
    "OutputResult": {"text": "上位机显示分类类别 &amp; 实时波形绘制", "x": 290, "y": 1070, "w": 200, "h": 60, "style": "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#90A4AE;strokeWidth=2;"}
}

edges = [
    {"src": "Start", "dst": "FrameSync", "label": ""},
    {"src": "FrameSync", "dst": "DropBytes", "label": "否"},
    {"src": "DropBytes", "dst": "Start", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;curved=1;exitX=0.5;exitY=0;entryX=0;entryY=0.5;"},
    {"src": "FrameSync", "dst": "StructUnpack", "label": "是"},
    {"src": "StructUnpack", "dst": "Checksum", "label": ""},
    {"src": "Checksum", "dst": "ErrorLog", "label": "否"},
    {"src": "ErrorLog", "dst": "Start", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;curved=1;exitX=0.5;exitY=0;entryX=0;entryY=0.5;"},
    {"src": "Checksum", "dst": "ParseData", "label": "是"},
    {"src": "ParseData", "dst": "Filter電容", "label": ""},
    {"src": "Filter電容", "dst": "ExtractFeatures", "label": ""},
    {"src": "ExtractFeatures", "dst": "Decision1", "label": ""},
    {"src": "Decision1", "dst": "ClassLight", "label": "是"},
    {"src": "Decision1", "dst": "Decision2", "label": "否"},
    {"src": "Decision2", "dst": "ClassWet", "label": "是"},
    {"src": "Decision2", "dst": "ClassDry", "label": "否"},
    {"src": "ClassLight", "dst": "OutputResult", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=0;entryY=0.5;"},
    {"src": "ClassWet", "dst": "OutputResult", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=0.5;entryY=0;"},
    {"src": "ClassDry", "dst": "OutputResult", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=1;entryY=0.5;"},
    {"src": "OutputResult", "dst": "Start", "label": "", "style": "edgeStyle=orthogonalEdgeStyle;curved=1;exitX=0.5;exitY=1;entryX=0.5;entryY=0;"}
]

def build_drawio():
    mxfile = ET.Element("mxfile", host="Electron", version="20.0.0", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id="diagram_1", name="Page-1")
    mxGraphModel = ET.SubElement(diagram, "mxGraphModel", dx="1200", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="827", pageHeight="1169", math="0", shadow="0")
    root = ET.SubElement(mxGraphModel, "root")
    
    # Base layers required by Draw.io
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    
    # Write nodes
    for node_id, info in nodes.items():
        cell = ET.SubElement(root, "mxCell", id=node_id, value=info["text"], style=info["style"], vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(info["x"]), y=str(info["y"]), width=str(info["w"]), height=str(info["h"]), **{"as": "geometry"})
        
    # Write edges
    edge_counter = 100
    for edge in edges:
        edge_id = f"edge_{edge_counter}"
        edge_counter += 1
        
        style = edge.get("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=1.5;")
        
        cell = ET.SubElement(root, "mxCell", id=edge_id, value=edge["label"], style=style, edge="1", parent="1", source=edge["src"], target=edge["dst"])
        ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        
    tree = ET.ElementTree(mxfile)
    output_path = "D:/02Projects/01Simulated-Droplet-Device/01_Python_UI_Host Computer/02mermaid/agent_flow.drawio"
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Draw.io file generated successfully at: {output_path}")

if __name__ == '__main__':
    build_drawio()
