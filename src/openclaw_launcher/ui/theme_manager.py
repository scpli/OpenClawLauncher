from PySide6.QtCore import QObject, Qt, Signal
from ..core.config import Config


class ThemeManager(QObject):
    theme_mode_changed = Signal(str)

    MODE_LIGHT = "light"
    MODE_DARK = "dark"
    MODE_SYSTEM = "system"
    VALID_MODES = {MODE_LIGHT, MODE_DARK, MODE_SYSTEM}

    def __init__(self):
        super().__init__()
        self._app = None
        self._mode = Config.get_setting("theme_mode", self.MODE_SYSTEM)
        if self._mode not in self.VALID_MODES:
            self._mode = self.MODE_SYSTEM
        self._system_listener_connected = False

    @property
    def current_mode(self):
        return self._mode

    def initialize(self, app):
        self._app = app
        self._update_system_listener()
        self.apply_current_theme()

    def set_mode(self, mode: str):
        if mode not in self.VALID_MODES:
            mode = self.MODE_SYSTEM

        if mode == self._mode:
            return

        self._mode = mode
        Config.set_setting("theme_mode", mode)
        self._update_system_listener()
        self.apply_current_theme()
        self.theme_mode_changed.emit(mode)

    def apply_current_theme(self):
        if self._app is None:
            return

        resolved = self._resolve_effective_theme()
        theme_name = "dark_teal.xml" if resolved == self.MODE_DARK else "light_teal.xml"

        try:
            from qt_material import apply_stylesheet

            apply_stylesheet(self._app, theme=theme_name)
            self._apply_material_qss_overrides(resolved)
        except Exception:
            pass

    def _apply_material_qss_overrides(self, resolved_mode: str):
        if self._app is None:
            return

        palette = self._qss_palette(resolved_mode)
        qss = f"""
QMainWindow, QWidget {{
    font-size: 13px;
    background: {palette['bg']};
    color: {palette['text_primary']};
}}

QWidget#MainRoot {{
    background: {palette['bg']};
}}

QWidget#TopBar {{
    background: {palette['surface']};
    border: 1px solid {palette['outline']};
    border-radius: 12px;
    padding: 8px 10px;
}}

QLabel#AppTitleLabel {{
    font-size: 20px;
    font-weight: 700;
    color: {palette['text_primary']};
    padding-left: 4px;
}}

QPushButton#ToolButton {{
    min-height: 34px;
    border-radius: 10px;
    padding: 0 14px;
    font-weight: 600;
    background: {palette['surface_alt']};
    color: {palette['text_primary']};
    border: 1px solid {palette['outline']};
}}

QPushButton#ToolButton:hover {{
    background: {palette['surface_hover']};
}}

QPushButton#ToolButton:pressed {{
    background: {palette['surface_pressed']};
}}

QTabWidget::pane {{
    top: -1px;
    background: {palette['surface']};
}}

QTabBar {{
    background: {palette['surface']};
    border: 1px solid {palette['outline']};
    border-radius: 12px;
    padding: 2px 6px;
}}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QPlainTextEdit,
QTextEdit,
QListWidget,
QTreeWidget,
QTableWidget,
QAbstractScrollArea {{
    border: 1px solid {palette['outline']};
    border-radius: 8px;
    background: {palette['surface']};
}}

QGroupBox {{
    margin-top: 10px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {palette['text_secondary']};
}}

QHeaderView::section {{
    background: {palette['surface_alt']};
    border: 1px solid {palette['outline']};
    padding: 6px;
}}

QTabBar::tab {{
    min-width: 110px;
    min-height: 34px;
    margin: 6px 4px 2px 4px;
    padding: 0 12px;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    color: {palette['text_secondary']};
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: {palette['primary_soft']};
    border-color: {palette['primary']};
    color: {palette['primary']};
}}

QTabBar::tab:hover:!selected {{
    background: {palette['surface_alt']};
    color: {palette['text_primary']};
}}

QMenu {{
    border: 1px solid {palette['outline']};
    border-radius: 8px;
    background: {palette['surface']};
    color: {palette['text_primary']};
    padding: 6px;
}}

QMenu::item {{
    border-radius: 6px;
    padding: 6px 16px;
}}

QMenu::item:selected {{
    background: {palette['surface_alt']};
}}
"""

        base = self._app.styleSheet() or ""
        self._app.setStyleSheet(f"{base}\n{qss}")

    def _qss_palette(self, resolved_mode: str) -> dict[str, str]:
        if resolved_mode == self.MODE_DARK:
            return {
                "bg": "#111827",
                "surface": "#1f2937",
                "surface_alt": "#263447",
                "surface_hover": "#31465f",
                "surface_pressed": "#3a516d",
                "outline": "#334155",
                "primary": "#4dd0e1",
                "primary_soft": "rgba(77, 208, 225, 0.18)",
                "text_primary": "#e5e7eb",
                "text_secondary": "#9ca3af",
            }

        return {
            "bg": "#ffffff",
            "surface": "#ffffff",
            "surface_alt": "#f8fbff",
            "surface_hover": "#f1f7ff",
            "surface_pressed": "#e9f2ff",
            "outline": "#d9e8ff",
            "primary": "#00838f",
            "primary_soft": "rgba(0, 131, 143, 0.12)",
            "text_primary": "#1f2937",
            "text_secondary": "#5b6472",
        }

    def _resolve_effective_theme(self) -> str:
        if self._mode == self.MODE_LIGHT:
            return self.MODE_LIGHT
        if self._mode == self.MODE_DARK:
            return self.MODE_DARK

        if self._app is None:
            return self.MODE_DARK

        try:
            style_hints = self._app.styleHints()
            if style_hints and hasattr(style_hints, "colorScheme"):
                scheme = style_hints.colorScheme()
                if scheme == Qt.ColorScheme.Dark:
                    return self.MODE_DARK
                if scheme == Qt.ColorScheme.Light:
                    return self.MODE_LIGHT
        except Exception:
            pass

        try:
            window_color = self._app.palette().window().color()
            return self.MODE_DARK if window_color.lightness() < 128 else self.MODE_LIGHT
        except Exception:
            return self.MODE_DARK

    def _update_system_listener(self):
        if self._app is None:
            return

        style_hints = self._app.styleHints()
        if not style_hints or not hasattr(style_hints, "colorSchemeChanged"):
            return

        should_connect = self._mode == self.MODE_SYSTEM

        if should_connect and not self._system_listener_connected:
            style_hints.colorSchemeChanged.connect(self._on_system_color_scheme_changed)
            self._system_listener_connected = True
        elif not should_connect and self._system_listener_connected:
            try:
                style_hints.colorSchemeChanged.disconnect(self._on_system_color_scheme_changed)
            except Exception:
                pass
            self._system_listener_connected = False

    def _on_system_color_scheme_changed(self, *_args):
        if self._mode == self.MODE_SYSTEM:
            self.apply_current_theme()


theme_manager = ThemeManager()