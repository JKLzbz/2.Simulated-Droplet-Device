"""
plot_style.py

只负责 pyqtgraph 的“初始化样式”，复用 droplet_detect_main_1209.py 的风格要点：
- 白色背景
- 黑色坐标轴、加粗
- 网格
- 曲线加粗、指定颜色
"""

from __future__ import annotations

import pyqtgraph as pg


def apply_1209_style(plot: pg.PlotWidget, *, grid_alpha: float = 0.25) -> None:
    """对单个 PlotWidget 应用统一样式。"""
    # 性能优化参数：禁用抗锯齿，启用 OpenGL 加速 (PyOpenGL 可选安装)
    pg.setConfigOptions(antialias=False, useOpenGL=True)
    
    # 全局背景/前景（按 1209 风格）
    pg.setConfigOption("background", "w")
    pg.setConfigOption("foreground", "k")

    # 有时全局 config 会被其它地方覆盖，这里对单个图强制白底
    plot.setBackground("w")

    plot.showGrid(x=True, y=True, alpha=grid_alpha)
    
    # 限制渲染视口
    plot.setClipToView(True)
    # 取消降采样，防止出现密集的“毛刺点阵”视觉伪影
    plot.setDownsampling(auto=False)

    axis_b = plot.getAxis("bottom")
    axis_l = plot.getAxis("left")
    axis_b.setPen(pg.mkPen(width=2, color="k"))
    axis_b.setTextPen(pg.mkPen(color="k"))
    axis_l.setPen(pg.mkPen(width=2, color="k"))
    axis_l.setTextPen(pg.mkPen(color="k"))


def make_curve(plot: pg.PlotWidget, *, rgb: tuple[int, int, int], width: int = 2):
    """创建一条曲线（1209 的粗线条风格）。"""
    return plot.plot(pen=pg.mkPen(pg.mkColor(*rgb), width=width))

