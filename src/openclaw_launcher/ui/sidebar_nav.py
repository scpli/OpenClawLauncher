from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QStackedWidget,
                               QScrollArea, QApplication, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from .i18n import i18n


class SidebarNavButton(QPushButton):
    """Sidebar navigation button with active state"""
    
    def __init__(self, text: str, panel_name: str, parent=None):
        super().__init__(text, parent)
        self.panel_name = panel_name
        self.setObjectName("SidebarNavButton")
        self.setCheckable(True)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
    
    def set_active(self, active: bool):
        """Set the button as active or inactive"""
        self.setChecked(active)
        if active:
            self.setObjectName("SidebarNavButtonActive")
        else:
            self.setObjectName("SidebarNavButton")
        self.style().polish(self)


class CollapsibleSection(QWidget):
    """Collapsible section in sidebar with multiple buttons"""
    
    button_clicked = Signal(str)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        self.buttons = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(0)
        
        # Section title with collapse button
        title_widget = QWidget()
        title_widget.setMinimumHeight(35)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)
        
        # Collapse indicator button
        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setObjectName("SidebarCollapseButton")
        self.collapse_btn.setFixedSize(20, 20)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_expansion)
        title_layout.addWidget(self.collapse_btn, 0, Qt.AlignVCenter)
        
        # Section title label (clickable)
        self.section_btn = QPushButton(title)
        self.section_btn.setObjectName("SidebarSectionButton")
        self.section_btn.setSizePolicy(self.section_btn.sizePolicy().horizontalPolicy(), self.section_btn.sizePolicy().verticalPolicy())
        self.section_btn.setCursor(Qt.PointingHandCursor)
        self.section_btn.clicked.connect(self.toggle_expansion)
        title_layout.addWidget(self.section_btn, 1)
        
        layout.addWidget(title_widget)
        
        # Container for child buttons
        self.content_widget = QWidget()
        self.content_widget.setMaximumHeight(10000)  # Large initial value
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 0, 0, 0)
        self.content_layout.setSpacing(0)
        layout.addWidget(self.content_widget)
        
        # Animation for smooth collapse/expand
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def add_button(self, text: str, panel_name: str):
        """Add a button to this section"""
        btn = SidebarNavButton(text, panel_name)
        btn.clicked.connect(lambda: self.button_clicked.emit(panel_name))
        self.content_layout.addWidget(btn)
        self.buttons.append(btn)
        return btn
    
    def toggle_expansion(self):
        """Toggle section expansion with animation"""
        self.is_expanded = not self.is_expanded
        self.update_visibility()
    
    def update_visibility(self):
        """Show/hide child buttons based on expansion state with animation"""
        # Update collapse button appearance
        self.collapse_btn.setText("▼" if self.is_expanded else "▶")
        
        if self.is_expanded:
            # Calculate content height
            content_height = sum(btn.sizeHint().height() for btn in self.buttons)
            content_height += self.content_layout.spacing() * max(0, len(self.buttons) - 1)
            
            self.animation.setStartValue(0)
            self.animation.setEndValue(content_height)
            self.animation.start()
        else:
            current_height = self.content_widget.height()
            self.animation.setStartValue(current_height)
            self.animation.setEndValue(0)
            self.animation.start()
    
    def get_button_by_panel(self, panel_name: str):
        """Get button by panel name"""
        for btn in self.buttons:
            if btn.panel_name == panel_name:
                return btn
        return None


class SidebarNav(QWidget):
    """Sidebar navigation widget with collapsible sections"""
    
    panel_selected = Signal(str)
    toggle_sidebar = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarNav")
        self.current_panel = None
        self.sections = {}
        self.all_buttons = {}
        self.is_collapsed = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)
        
        # Scroll area for sections
        self.scroll = QScrollArea()
        self.scroll.setObjectName("SidebarScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        self.sections_layout = QVBoxLayout(scroll_content)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(5)
        self.sections_layout.addStretch()
        
        self.scroll.setWidget(scroll_content)
        layout.addWidget(self.scroll, 1)  # Give it stretch factor
    
    def set_collapsed(self, collapsed: bool):
        """Set sidebar collapsed state"""
        self.is_collapsed = collapsed
        if collapsed:
            self.scroll.hide()
        else:
            self.scroll.show()
    
    def add_section(self, title: str, panel_configs: list):
        """
        Add a collapsible section with buttons
        
        Args:
            title: Section title
            panel_configs: List of tuples (display_name, panel_name)
        """
        section = CollapsibleSection(title, self)
        section.button_clicked.connect(self.on_button_clicked)
        
        for display_name, panel_name in panel_configs:
            btn = section.add_button(display_name, panel_name)
            self.all_buttons[panel_name] = btn
        
        section.update_visibility()
        self.sections[title] = section
        # Insert before the stretch
        self.sections_layout.insertWidget(self.sections_layout.count() - 1, section)
    
    def on_button_clicked(self, panel_name: str):
        """Handle button click"""
        self.select_panel(panel_name)
        self.panel_selected.emit(panel_name)
    
    def select_panel(self, panel_name: str):
        """Select a panel and update button states"""
        if self.current_panel == panel_name:
            return
        
        # Deactivate previous button
        if self.current_panel and self.current_panel in self.all_buttons:
            self.all_buttons[self.current_panel].set_active(False)
        
        # Activate new button
        self.current_panel = panel_name
        if panel_name in self.all_buttons:
            self.all_buttons[panel_name].set_active(True)
    
    def update_ui_texts(self, section_configs: dict):
        """
        Update UI texts for all sections
        
        Args:
            section_configs: Dict of {section_title: [(display_name, panel_name), ...]}
        """
        # Clear existing sections
        for section in self.sections.values():
            section.setParent(None)
        self.sections.clear()
        self.all_buttons.clear()
        
        # Re-add sections with new texts
        for title, configs in section_configs.items():
            self.add_section(title, configs)
        
        # Re-select current panel if any
        if self.current_panel and self.current_panel in self.all_buttons:
            self.all_buttons[self.current_panel].set_active(True)
