#!/usr/bin/env python3
"""
ASAR 打包/解包 图形化工具 - 毛玻璃版
Frosted Glass Edition
"""

import sys
import os
import json
import struct
import argparse
import queue
import threading


# ==================== 主题色 ====================

THEME = {
    "bg_gradient": [(255, 255, 255), (250, 250, 255), (245, 248, 255)],
    "title_color": "#1a1a2e",
    "desc_color": "rgba(80,80,100,0.7)",
    "card_bg": (255, 255, 255),
    "card_border": (230, 232, 240),
    "input_bg": "rgba(255,255,255,0.7)",
    "input_border": "rgba(200,205,220,0.6)",
    "input_focus_bg": "rgba(255,255,255,0.9)",
    "input_focus_border": "#6c63ff",
    "input_color": "#1a1a2e",
    "tab_active_bg": "rgba(255,255,255,0.85)",
    "tab_active_border": "rgba(220,225,240,0.9)",
    "tab_active_color": "#6c63ff",
    "tab_inactive_bg": "rgba(255,255,255,0.35)",
    "tab_inactive_border": "rgba(220,225,240,0.35)",
    "tab_inactive_color": "rgba(100,100,120,0.6)",
    "btn_browse_bg": "#f0f0f8",
    "btn_browse_border": "#dddde8",
    "btn_browse_hover": "#e0e0f0",
    "btn_browse_color": "#6c63ff",
    "log_bg": "#000000",
    "log_color": "#ffffff",
    "log_border": "#dddde8",
    "footer_color": "#b0b0c0",
    "window_border": (220, 225, 240),
    "clear_btn_bg": "#f0f0f8",
    "clear_btn_border": "#dddde8",
    "clear_btn_color": "#6c63ff",
}

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog,
    QMessageBox, QFrame, QGraphicsDropShadowEffect, QGraphicsBlurEffect,
    QButtonGroup, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve,
    QPoint, QRect, QTimer
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter,
    QPainterPath, QPen, QMouseEvent
)


# ==================== 毛玻璃卡片 ====================

class FrostedCard(QFrame):
    """毛玻璃卡片"""
    def __init__(self, parent=None, opacity=0.75, theme=None):
        super().__init__(parent)
        self._opacity = opacity
        self._theme = theme or THEME
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        t = self._theme

        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 18, 18)

        card_bg = t["card_bg"]
        bg = QColor(*card_bg, int(self._opacity * 255))
        painter.fillPath(path, bg)

        card_border = t["card_border"]
        painter.setPen(QPen(QColor(*card_border, int(self._opacity * 160)), 1))
        painter.drawPath(path)


class FrostedTextEdit(QTextEdit):
    """毛玻璃文本框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        from PyQt5.QtCore import QRectF
        path.addRoundedRect(QRectF(self.viewport().rect()), 12, 12)
        painter.fillPath(path, QColor(20, 20, 35, 210))
        super().paintEvent(event)


# ==================== 自定义控件 ====================

class GlassButton(QPushButton):
    """毛玻璃按钮"""
    def __init__(self, text, color=(102, 126, 234), hover_color=(118, 75, 162)):
        super().__init__(text)
        self._color = color
        self._hover_color = hover_color
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r, g, b = self._hover_color if self._hovered else self._color
        path = QPainterPath()
        from PyQt5.QtCore import QRectF
        path.addRoundedRect(QRectF(self.rect()), 12, 12)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(r, g, b, 240))
        gradient.setColorAt(1, QColor(min(r + 30, 255), min(g + 20, 255), min(b + 40, 255), 240))
        painter.fillPath(path, QBrush(gradient))

        # 高光
        highlight_path = QPainterPath()
        highlight_path.addRoundedRect(2, 2, self.width() - 4, self.height() // 2 - 2, 10, 10)
        painter.fillPath(highlight_path, QColor(255, 255, 255, 40))

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def sizeHint(self):
        return QSize(200, 48)


class GlassLineEdit(QLineEdit):
    """毛玻璃输入框"""
    def __init__(self, placeholder="", theme=None):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setAttribute(Qt.WA_StyledBackground, False)
        t = theme or THEME
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {t['input_border']};
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 13px;
                background: {t['input_bg']};
                color: {t['input_color']};
            }}
            QLineEdit:focus {{
                border-color: {t['input_focus_border']};
                background: {t['input_focus_bg']};
            }}
        """)


class SmallGlassButton(QPushButton):
    """小毛玻璃按钮"""
    def __init__(self, text="📂 浏览", theme=None):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(78, 44)
        t = theme or THEME
        self.setStyleSheet(f"""
            QPushButton {{
                background: {t['btn_browse_bg']};
                border: 1px solid {t['btn_browse_border']};
                border-radius: 12px;
                font-size: 12px;
                color: {t['btn_browse_color']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {t['btn_browse_hover']};
                border-color: rgba(255,255,255,0.9);
            }}
        """)


class TabPill(QPushButton):
    """胶囊选项卡"""
    def __init__(self, text, icon="", theme=None):
        super().__init__(f"  {icon}  {text}  ")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)
        self._active = False
        self._theme = theme or THEME

    def setActive(self, a):
        t = self._theme
        self._active = a
        if a:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t['tab_active_bg']};
                    border: 1px solid {t['tab_active_border']};
                    border-radius: 22px;
                    font-size: 14px;
                    font-weight: bold;
                    color: {t['tab_active_color']};
                    padding: 6px 22px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t['tab_inactive_bg']};
                    border: 1px solid {t['tab_inactive_border']};
                    border-radius: 22px;
                    font-size: 14px;
                    color: {t['tab_inactive_color']};
                    padding: 6px 22px;
                }}
                QPushButton:hover {{
                    color: #6c63ff;
                }}
            """)


# ==================== 主窗口 ====================

class ASARGUI(QMainWindow):
    def __init__(self, opacity=0.75):
        super().__init__()

        self._opacity = max(0.2, min(1.0, opacity))
        self._theme = THEME

        # 消息队列 + 定时器 (经典 PyQt 线程安全方案)
        self._msg_queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._process_queue)
        self._poll_timer.start(50)  # 每 50ms 轮询一次

        # 无边框毛玻璃窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setWindowTitle("ASAR 打包/解包工具")
        self.setMinimumSize(720, 620)
        self.resize(760, 660)

        # 拖拽移动
        self._drag_pos = None

        central = QWidget()
        central.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(central)

        self._setup_ui(central)

        # 居中
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                   (screen.height() - self.height()) // 2)

    # ==================== 窗口拖拽 ====================

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def closeEvent(self, event):
        """关闭窗口时确认，防止误关"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出 ASAR 工具吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def _toggle_maximize(self):
        """切换最大化/还原，修复无边框窗口的 bug"""
        if self.isMaximized():
            # 还原到保存的几何
            if self._saved_geom:
                self.setGeometry(self._saved_geom)
            else:
                self.showNormal()
            self._max_btn.setText("□")
        else:
            # 保存当前几何，然后最大化
            self._saved_geom = self.geometry()
            # 获取可用屏幕区域（排除任务栏）
            screen = QApplication.primaryScreen().availableGeometry()
            self.setGeometry(screen)
            self._max_btn.setText("❐")

    # ==================== 全局背景绘制 ====================

    def paintEvent(self, event):
        """绘制毛玻璃窗口背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        t = self._theme
        op = self._opacity
        bg = t["bg_gradient"]
        bg_alpha = int(255 * op)
        overlay_alpha = int(255 * op * 0.2)
        shadow_alpha = int(100 * op)
        border_color = t["window_border"]

        if self.isMaximized():
            bg_path = QPainterPath()
            bg_path.addRect(0, 0, self.width(), self.height())
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(*bg[0], bg_alpha))
            gradient.setColorAt(0.5, QColor(*bg[1], bg_alpha))
            gradient.setColorAt(1, QColor(*bg[2], bg_alpha))
            painter.fillPath(bg_path, QBrush(gradient))
            painter.fillPath(bg_path, QColor(255, 255, 255, overlay_alpha))
            return

        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(8, 8, self.width() - 16, self.height() - 16, 24, 24)
        painter.fillPath(shadow_path, QColor(0, 0, 0, shadow_alpha))

        bg_path = QPainterPath()
        bg_path.addRoundedRect(6, 6, self.width() - 12, self.height() - 12, 22, 22)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(*bg[0], bg_alpha))
        gradient.setColorAt(0.5, QColor(*bg[1], bg_alpha))
        gradient.setColorAt(1, QColor(*bg[2], bg_alpha))
        painter.fillPath(bg_path, QBrush(gradient))

        inner = QPainterPath()
        inner.addRoundedRect(6, 6, self.width() - 12, self.height() - 12, 22, 22)
        painter.fillPath(inner, QColor(255, 255, 255, overlay_alpha))

        painter.setPen(QPen(QColor(*border_color, int(100 * op)), 1.5))
        painter.drawPath(inner)

    # ==================== UI ====================

    def _setup_ui(self, central):
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)

        t = self._theme

        # ---- 标题栏 ----
        title_bar = QHBoxLayout()

        self.title_icon = QLabel("📦")
        self.title_icon.setFont(QFont("", 26))
        title_bar.addWidget(self.title_icon)

        title_text = QLabel("ASAR 打包/解包工具")
        title_text.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_text.setStyleSheet(f"color: {t['title_color']};")
        title_bar.addWidget(title_text)

        title_bar.addSpacing(10)

        title_bar.addStretch()

        # 窗口控制按钮
        self._saved_geom = None

        btn_min = QPushButton("─")
        btn_max = QPushButton("□")
        btn_close = QPushButton("✕")

        for btn, clr in [(btn_min, (120,120,140)), (btn_max, (120,120,140)), (btn_close, (220,100,100))]:
            btn.setFixedSize(36, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.3);
                    border: none; border-radius: 10px;
                    font-size: 14px; color: rgba({clr[0]},{clr[1]},{clr[2]},0.8);
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: rgba({clr[0]},{clr[1]},{clr[2]},0.25);
                    color: rgba({clr[0]},{clr[1]},{clr[2]},1);
                }}
            """)

        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)
        btn_max.clicked.connect(self._toggle_maximize)

        title_bar.addWidget(btn_min)
        title_bar.addWidget(btn_max)
        title_bar.addWidget(btn_close)

        self._max_btn = btn_max

        outer.addLayout(title_bar)

        # ---- 选项卡 ----
        tab_bar = QHBoxLayout()
        tab_bar.setSpacing(10)

        self.tab_group = QButtonGroup(self)
        self.tab_unpack = TabPill("解包", "📦", theme=t)
        self.tab_pack = TabPill("打包", "📁", theme=t)
        self.tab_group.addButton(self.tab_unpack, 0)
        self.tab_group.addButton(self.tab_pack, 1)
        self.tab_unpack.setActive(True)
        self.tab_pack.setActive(False)

        self.tab_unpack.clicked.connect(lambda: self._switch_tab(0))
        self.tab_pack.clicked.connect(lambda: self._switch_tab(1))

        tab_bar.addWidget(self.tab_unpack)
        tab_bar.addWidget(self.tab_pack)
        tab_bar.addStretch()
        outer.addLayout(tab_bar)

        # ---- 内容区 ----
        self.stack = QWidget()
        self.stack.setAttribute(Qt.WA_TranslucentBackground)
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self._build_unpack_panel()
        self._build_pack_panel()
        self._switch_tab(0)

        outer.addWidget(self.stack)

        # ---- 日志 ----
        log_card = FrostedCard(opacity=self._opacity * 0.7, theme=t)
        log_inner = QVBoxLayout(log_card)
        log_inner.setContentsMargins(18, 14, 18, 14)

        log_header = QHBoxLayout()
        log_lbl = QLabel("📋 运行日志")
        log_lbl.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        log_lbl.setStyleSheet(f"color: {t['title_color']};")
        log_header.addWidget(log_lbl)
        log_header.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t['clear_btn_bg']}; border: 1px solid {t['clear_btn_border']};
                border-radius: 8px; padding: 4px 14px; color: {t['clear_btn_color']}; font-size: 11px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.6); }}
        """)
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_header.addWidget(clear_btn)
        log_inner.addLayout(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(130)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {t['log_border']};
                border-radius: 12px;
                background: {t['log_bg']};
                color: {t['log_color']};
                padding: 10px;
                selection-background-color: rgba(150,140,220,0.5);
            }}
        """)
        log_inner.addWidget(self.log_text)
        outer.addWidget(log_card)

        # 底部
        footer = QLabel("用于学习源码用途  |  Powered by Python + PyQt5  |  Frosted Glass UI")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"color: {t['footer_color']}; font-size: 11px;")
        outer.addWidget(footer)

    # ==================== 面板 ====================

    def _build_unpack_panel(self):
        t = self._theme
        self.unpack_panel = QWidget()
        self.unpack_panel.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self.unpack_panel)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)

        card = FrostedCard(opacity=self._opacity * 0.85, theme=t)
        c = QVBoxLayout(card)
        c.setContentsMargins(26, 20, 26, 22)
        c.setSpacing(16)

        desc = QLabel("将 .asar 文件解包为文件夹，提取其中的所有文件")
        desc.setStyleSheet(f"color: {t['desc_color']}; font-size: 13px;")
        c.addWidget(desc)

        c.addWidget(QLabel("📄  ASAR 文件路径"))
        row1 = QHBoxLayout()
        self.asar_path = GlassLineEdit("选择或拖拽 .asar 文件...", theme=t)
        row1.addWidget(self.asar_path, 1)
        b1 = SmallGlassButton(theme=t)
        b1.clicked.connect(lambda: self._browse_file("选择 ASAR 文件", "*.asar", self.asar_path))
        row1.addWidget(b1)
        c.addLayout(row1)

        c.addWidget(QLabel("📂  输出目录"))
        row2 = QHBoxLayout()
        self.unpack_out = GlassLineEdit("解包后的文件存放位置...", theme=t)
        row2.addWidget(self.unpack_out, 1)
        b2 = SmallGlassButton(theme=t)
        b2.clicked.connect(lambda: self._browse_dir("选择输出目录", self.unpack_out))
        row2.addWidget(b2)
        c.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.unpack_btn = GlassButton("  🚀  开 始 解 包  ", (100, 130, 240))
        self.unpack_btn.clicked.connect(self._start_unpack)
        btn_row.addWidget(self.unpack_btn)
        btn_row.addStretch()
        c.addLayout(btn_row)

        self.unpack_progress = QProgressBar()
        self.unpack_progress.setRange(0, 0)
        self.unpack_progress.setVisible(False)
        self.unpack_progress.setFixedHeight(5)
        self.unpack_progress.setStyleSheet(f"""
            QProgressBar {{ border: none; background: {t['btn_browse_bg']}; border-radius: 3px; }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(100,130,240,0.9), stop:1 rgba(140,100,220,0.9));
                border-radius: 3px;
            }}
        """)
        c.addWidget(self.unpack_progress)

        layout.addWidget(card)
        layout.addStretch()

    def _build_pack_panel(self):
        t = self._theme
        self.pack_panel = QWidget()
        self.pack_panel.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self.pack_panel)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)

        card = FrostedCard(opacity=self._opacity * 0.85, theme=t)
        c = QVBoxLayout(card)
        c.setContentsMargins(26, 20, 26, 22)
        c.setSpacing(16)

        desc = QLabel("将文件夹打包为 .asar 文件，用于 Electron 应用")
        desc.setStyleSheet(f"color: {t['desc_color']}; font-size: 13px;")
        c.addWidget(desc)

        c.addWidget(QLabel("📂  源文件夹"))
        row1 = QHBoxLayout()
        self.pack_src = GlassLineEdit("选择要打包的文件夹...", theme=t)
        row1.addWidget(self.pack_src, 1)
        b1 = SmallGlassButton(theme=t)
        b1.clicked.connect(lambda: self._browse_dir("选择源文件夹", self.pack_src))
        row1.addWidget(b1)
        c.addLayout(row1)

        c.addWidget(QLabel("💾  输出 ASAR 文件"))
        row2 = QHBoxLayout()
        self.pack_out = GlassLineEdit("输出的 .asar 文件路径...", theme=t)
        row2.addWidget(self.pack_out, 1)
        b2 = SmallGlassButton(theme=t)
        b2.clicked.connect(lambda: self._browse_save("保存 ASAR", "*.asar", self.pack_out))
        row2.addWidget(b2)
        c.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.pack_btn = GlassButton("  📦  开 始 打 包  ", (230, 100, 150))
        self.pack_btn.clicked.connect(self._start_pack)
        btn_row.addWidget(self.pack_btn)
        btn_row.addStretch()
        c.addLayout(btn_row)

        self.pack_progress = QProgressBar()
        self.pack_progress.setRange(0, 0)
        self.pack_progress.setVisible(False)
        self.pack_progress.setFixedHeight(5)
        self.pack_progress.setStyleSheet(f"""
            QProgressBar {{ border: none; background: {t['btn_browse_bg']}; border-radius: 3px; }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(230,110,160,0.9), stop:1 rgba(240,100,120,0.9));
                border-radius: 3px;
            }}
        """)
        c.addWidget(self.pack_progress)

        layout.addWidget(card)
        layout.addStretch()

    # ==================== 选项卡 ====================

    def _switch_tab(self, idx):
        self.tab_unpack.setActive(idx == 0)
        self.tab_pack.setActive(idx == 1)

        while self.stack_layout.count():
            item = self.stack_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self.stack_layout.addWidget(
            self.unpack_panel if idx == 0 else self.pack_panel
        )

    # ==================== 文件浏览 ====================

    def _browse_file(self, title, filt, le):
        path, _ = QFileDialog.getOpenFileName(self, title, "", f"ASAR files ({filt});;All files (*)")
        if path:
            le.setText(path)
            if le is self.asar_path and not self.unpack_out.text():
                dn = os.path.splitext(os.path.basename(path))[0] + "_unpacked"
                self.unpack_out.setText(os.path.join(os.path.dirname(path), dn))

    def _browse_dir(self, title, le):
        path = QFileDialog.getExistingDirectory(self, title)
        if path:
            le.setText(path)
            if le is self.pack_src and not self.pack_out.text():
                self.pack_out.setText(os.path.join(os.path.dirname(path), "app.asar"))

    def _browse_save(self, title, filt, le):
        path, _ = QFileDialog.getSaveFileName(self, title, "", f"ASAR files ({filt});;All files (*)")
        if path:
            le.setText(path)

    # ==================== 日志 ====================

    def _log(self, msg):
        self.log_text.append(msg)
        from PyQt5.QtGui import QTextCursor
        c = self.log_text.textCursor()
        c.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(c)

    # ==================== 消息队列轮询 ====================

    def _process_queue(self):
        """定时轮询队列，在主线程安全地处理消息"""
        try:
            while True:
                msg_type, msg = self._msg_queue.get_nowait()
                if msg_type == "log":
                    self._log(msg)
                elif msg_type == "unpack_done":
                    QMessageBox.information(self, "✅ 完成", msg)
                    self._unpack_done()
                elif msg_type == "unpack_error":
                    self._log(f"❌ [错误] {msg}")
                    QMessageBox.critical(self, "解包失败", msg)
                    self._unpack_done()
                elif msg_type == "pack_done":
                    QMessageBox.information(self, "✅ 完成", msg)
                    self._pack_done()
                elif msg_type == "pack_error":
                    self._log(f"❌ [错误] {msg}")
                    QMessageBox.critical(self, "打包失败", msg)
                    self._pack_done()
        except queue.Empty:
            pass

    # ==================== 解包 ====================

    def _start_unpack(self):
        try:
            asar_path = self.asar_path.text().strip()
            out_dir = self.unpack_out.text().strip()

            if not asar_path:
                QMessageBox.critical(self, "错误", "请选择 ASAR 文件")
                return
            if not os.path.exists(asar_path):
                QMessageBox.critical(self, "错误", f"文件不存在:\n{asar_path}")
                return
            if not out_dir:
                out_dir = os.path.join(os.path.dirname(asar_path), "unpacked")
                self.unpack_out.setText(out_dir)

            self._log(f"🔍 准备解包: {asar_path}")
            self.unpack_btn.setEnabled(False)
            self.unpack_progress.setVisible(True)

            t = threading.Thread(target=_do_unpack, args=(asar_path, out_dir, self._msg_queue), daemon=True)
            t.start()
            self._log("⏳ 解包线程已启动...")
        except Exception as e:
            import traceback
            self._log(f"❌ 启动异常: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "异常", str(e))
            self._unpack_done()

    def _unpack_done(self):
        self.unpack_btn.setEnabled(True)
        self.unpack_progress.setVisible(False)

    # ==================== 打包 ====================

    def _start_pack(self):
        try:
            src_dir = self.pack_src.text().strip()
            out_asar = self.pack_out.text().strip()

            if not src_dir:
                QMessageBox.critical(self, "错误", "请选择源文件夹")
                return
            if not os.path.isdir(src_dir):
                QMessageBox.critical(self, "错误", f"文件夹不存在:\n{src_dir}")
                return
            if not out_asar:
                out_asar = os.path.join(os.path.dirname(src_dir), "app.asar")
                self.pack_out.setText(out_asar)

            self._log(f"🔍 准备打包: {src_dir}")
            self.pack_btn.setEnabled(False)
            self.pack_progress.setVisible(True)

            t = threading.Thread(target=_do_pack, args=(src_dir, out_asar, self._msg_queue), daemon=True)
            t.start()
            self._log("⏳ 打包线程已启动...")
        except Exception as e:
            import traceback
            self._log(f"❌ 启动异常: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "异常", str(e))
            self._pack_done()

    def _pack_done(self):
        self.pack_btn.setEnabled(True)
        self.pack_progress.setVisible(False)

# ==================== 工作函数（在后台线程运行） ====================

def _do_unpack(asar_path, out_dir, msg_queue):
    """解包工作函数 - 运行在后台线程，通过 queue 与主线程通信"""
    try:
        msg_queue.put(("log", f"📦 解包: {asar_path}"))
        msg_queue.put(("log", f"   → {out_dir}"))
        msg_queue.put(("log", ""))

        with open(asar_path, "rb") as f:
            data = f.read()

        if len(data) < 12:
            raise Exception("文件太小，不是有效的 ASAR 文件")

        pickle_size = struct.unpack_from("<I", data, 0)[0]
        hsize = struct.unpack_from("<I", data, 4)[0]

        msg_queue.put(("log", f"📋 Pickle size: {pickle_size}"))
        msg_queue.put(("log", f"📋 Header size: {hsize}"))

        if 12 + hsize > len(data):
            raise Exception("头部大小超过文件大小，文件可能已损坏")

        header_json = data[12:12 + hsize].decode("utf-8").rstrip("\x00")
        base_offset = 12 + hsize
        base_offset += (4 - (hsize % 4)) % 4

        header = json.loads(header_json)
        files_dict = header.get("files", {})

        if not files_dict:
            raise Exception("ASAR 中没有找到文件")

        os.makedirs(out_dir, exist_ok=True)
        count = 0

        for name, info in files_dict.items():
            offset = int(info["offset"]) + base_offset
            size = int(info["size"])
            if name == "files":
                continue
            out_path = os.path.join(out_dir, name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as fout:
                fout.write(data[offset:offset + size])
            msg_queue.put(("log", f"  ✅ {name}  ({size:,} bytes)"))
            count += 1

        msg_queue.put(("log", ""))
        msg_queue.put(("log", f"🎉 完成! 共提取 {count} 个文件"))
        msg_queue.put(("unpack_done", f"解包成功！\n\n共提取 {count} 个文件\nto: {out_dir}"))

    except Exception as e:
        import traceback
        err = f"{e}\n{traceback.format_exc()}"
        msg_queue.put(("unpack_error", err))


def _do_pack(src_dir, out_asar, msg_queue):
    """打包工作函数 - 运行在后台线程，通过 queue 与主线程通信"""
    try:
        msg_queue.put(("log", f"📁 打包: {src_dir}"))
        msg_queue.put(("log", f"   → {out_asar}"))
        msg_queue.put(("log", ""))

        file_list = []
        for root, dirs, files in os.walk(src_dir):
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, src_dir).replace("\\", "/")
                file_list.append((rel, full, os.path.getsize(full)))

        if not file_list:
            raise Exception("源文件夹中没有文件")

        file_list.sort(key=lambda x: x[0])
        msg_queue.put(("log", f"📋 找到 {len(file_list)} 个文件"))
        msg_queue.put(("log", ""))

        cur = 0
        files_dict = {}
        for rel, _, size in file_list:
            files_dict[rel] = {"offset": str(cur), "size": size}
            cur += size

        header_json = json.dumps({"files": files_dict}, indent=None, separators=(", ", ": "))
        header_bytes = header_json.encode("utf-8")
        hsize = len(header_bytes)
        pad = (4 - (hsize % 4)) % 4
        aligned = hsize + pad

        msg_queue.put(("log", f"📋 Header 大小: {hsize} (对齐: {aligned})"))
        msg_queue.put(("log", ""))

        with open(out_asar, "wb") as f:
            f.write(struct.pack("<I", 4))
            f.write(struct.pack("<I", aligned))
            f.write(struct.pack("<I", aligned))
            f.write(header_bytes)
            if pad > 0:
                f.write(b"\x00" * pad)
            for rel, full, size in file_list:
                with open(full, "rb") as fin:
                    f.write(fin.read())
                msg_queue.put(("log", f"  ✅ {rel}  ({size:,} bytes)"))

        total = os.path.getsize(out_asar)
        msg_queue.put(("log", ""))
        msg_queue.put(("log", f"🎉 完成! → {out_asar}"))
        msg_queue.put(("log", f"📦 总大小: {total:,} bytes  ({len(file_list)} 个文件)"))
        msg_queue.put(("pack_done", f"打包成功！\n\n共 {len(file_list)} 个文件\n大小: {total:,} bytes"))

    except Exception as e:
        import traceback
        err = f"{e}\n{traceback.format_exc()}"
        msg_queue.put(("pack_error", err))


# ==================== 入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="ASAR 打包/解包 图形化工具",
        epilog="示例: %(prog)s --opacity 0.85"
    )
    parser.add_argument(
        "-o", "--opacity", type=float, default=0.9,
        help="不透明度 0.2~1.0 (默认: 0.9, 越大越不透明)"
    )
    args = parser.parse_args()
    opacity = max(0.2, min(1.0, args.opacity))

    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ASARGUI(opacity=opacity)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
