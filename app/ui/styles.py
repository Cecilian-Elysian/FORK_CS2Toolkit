# UI样式管理模块

class UIStyles:
    @staticmethod
    def get_global_style():
        return """
        /* 卡片基础样式 */
        #actionCard {
            background-color: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
        }
        #actionCard:hover {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 120, 212, 0.4);
            margin-top: -2px; /* 悬停上浮动效需要代码配合，但可以增加边框发光 */
        }
        
        /* 深色模式下的卡片样式 */
        .Dark #actionCard {
            background-color: rgba(255, 255, 255, 0.043);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .Dark #actionCard:hover {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(0, 120, 212, 0.6);
        }
        
        /* 自定义面板 */
        #customPanel {
            background-color: transparent;
        }
        """

    @staticmethod
    def apply_styles(widget):
        widget.setStyleSheet(UIStyles.get_global_style())
