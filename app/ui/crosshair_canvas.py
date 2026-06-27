from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QImage, QPixmap
from PySide6.QtCore import Qt, QRect, QPoint, QSize

class CrosshairCanvas(QWidget):
    """
    准星预览画布
    使用 QPainter 渲染 CS2 准星
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.params = {}
        
        # 预定义 CS2 默认颜色
        self.cs2_colors = {
            0: QColor(255, 50, 50),     # 红
            1: QColor(50, 250, 50),     # 绿
            2: QColor(250, 250, 50),    # 黄
            3: QColor(50, 50, 250),     # 蓝
            4: QColor(50, 250, 250),    # 青
            # 5 是自定义颜色，通过 r, g, b 读取
        }
        
    def set_params(self, params: dict):
        """更新参数并重绘"""
        self.params = params
        self.update()
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False) # 准星通常不需要抗锯齿，保持像素感
        
        # 1. 绘制背景 (模拟游戏画面，这里用深灰色渐变或纯色代替)
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        if not self.params:
            return
            
        # 2. 提取参数
        # 缩放因子，让预览图里的准星大一点方便看
        scale = 2.0 
        
        size = self.params.get('cl_crosshairsize', 2.0) * scale
        thickness = self.params.get('cl_crosshairthickness', 0.5) * scale
        gap = self.params.get('cl_crosshairgap', 0.0) * scale
        
        draw_outline = self.params.get('cl_crosshair_drawoutline', 0)
        outline_thickness = self.params.get('cl_crosshair_outlinethickness', 1.0) * scale
        
        draw_dot = self.params.get('cl_crosshairdot', 0)
        t_style = self.params.get('cl_crosshair_t', 0)
        
        # 解析颜色
        color_idx = self.params.get('cl_crosshaircolor', 1)
        if color_idx == 5:
            r = self.params.get('cl_crosshaircolor_r', 0)
            g = self.params.get('cl_crosshaircolor_g', 255)
            b = self.params.get('cl_crosshaircolor_b', 0)
            color = QColor(r, g, b)
        else:
            color = self.cs2_colors.get(color_idx, QColor(0, 255, 0))
            
        # 透明度
        if self.params.get('cl_crosshairusealpha', 1):
            alpha = self.params.get('cl_crosshairalpha', 255)
            color.setAlpha(alpha)
            
        # 中心点
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # 3. 辅助绘制函数
        def draw_rect_with_outline(x, y, w, h):
            if draw_outline:
                # 绘制轮廓 (扩大一圈)
                outline_color = QColor(0, 0, 0, color.alpha())
                painter.fillRect(
                    int(x - outline_thickness), 
                    int(y - outline_thickness), 
                    int(w + outline_thickness * 2), 
                    int(h + outline_thickness * 2), 
                    outline_color
                )
            # 绘制实体
            painter.fillRect(int(x), int(y), int(w), int(h), color)

        # 4. 开始绘制准星
        
        # 中心点 (Dot)
        if draw_dot:
            dot_size = thickness
            draw_rect_with_outline(
                center_x - dot_size / 2, 
                center_y - dot_size / 2, 
                dot_size, 
                dot_size
            )
            
        # 左线
        draw_rect_with_outline(
            center_x - gap - size, 
            center_y - thickness / 2, 
            size, 
            thickness
        )
        
        # 右线
        draw_rect_with_outline(
            center_x + gap, 
            center_y - thickness / 2, 
            size, 
            thickness
        )
        
        # 下线
        draw_rect_with_outline(
            center_x - thickness / 2, 
            center_y + gap, 
            thickness, 
            size
        )
        
        # 上线 (如果是 T 型准星，不画上线)
        if not t_style:
            draw_rect_with_outline(
                center_x - thickness / 2, 
                center_y - gap - size, 
                thickness, 
                size
            )
