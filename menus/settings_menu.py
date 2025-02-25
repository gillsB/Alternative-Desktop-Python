from PySide6.QtWidgets import (QPushButton, QMessageBox, QHBoxLayout, QCheckBox, QDialog, QFormLayout, QScrollArea, QWidget, QVBoxLayout, QLabel, QApplication, QTabWidget, QFrame,
                               QSlider, QComboBox, QStyle, QFileDialog, QSpinBox, QColorDialog, QSizePolicy)
from PySide6.QtCore import Qt, QEvent, QSize, QTimer, QPoint, QStandardPaths
from PySide6.QtGui import QKeySequence, QColor
from util.utils import ClearableLineEdit, SliderWithInput, create_separator
from util.settings import get_setting, set_setting, load_settings, save_settings
from util.config import reset_all_to_default_font_size, reset_all_to_default_font_color
from menus.display_warning import (display_bg_video_not_exist, display_bg_image_not_exist, display_settings_not_saved, display_reset_default_font_color_warning,
                                display_multiple_working_keybind_warning, display_reset_default_font_size_warning)
import os
import logging

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    is_changed = False
    def initUI(self):
        self.setWindowTitle("Settings")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        main_layout = QFormLayout(self.content_widget)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        tab_widget = QTabWidget()
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        general_tab.setLayout(general_layout)

        background_tab = QWidget()
        background_layout = QFormLayout(background_tab)
        background_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        icon_tab = QWidget()
        icon_layout = QVBoxLayout(icon_tab)
        icon_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        icon_tab.setLayout(icon_layout)

        # Small optimization to load settings once for the entire file then use .get() from that
        # Instead of using get_setting() which calls a load_settings() every instance.
        self.settings = load_settings()

        self.add_general_tab(general_layout)
        self.add_background_tab(background_layout)
        self.add_icon_tab(icon_layout)

        self.display_theme() # Updates stylesheet for theme loaded.
        # End Scroll area before save button (so save button remains separate)
        scroll_area.setWidget(self.content_widget)

        # Save button (appears outside scroll area)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button)
        self.save_button.setAutoDefault(False)
        self.save_button.setDefault(False)

        # Attach General and Background tab to layout.
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(background_tab, "Background")
        tab_widget.addTab(icon_tab, "Icon")
        main_layout.addWidget(tab_widget)

        # Finish Layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.save_button)
        self.setLayout(main_layout)

        # Adding/hiding rows and resize to fit screen.
        self.update_background_sliders_visibility()
        self.update_custom_bg_color_visibility()
        self.background_selector.currentIndexChanged.connect(self.update_background_sliders_visibility)
        self.custom_bg_fill_cb.toggled.connect(self.update_custom_bg_color_visibility)

        self.installEventFilter(self)
        self.main_window_closing = False

    def add_general_tab(self, general_layout):

        ### Program Behavior Section
        # Checkbox for update on launch
        self.update_on_launch_cb = QCheckBox()
        self.update_on_launch_cb.setChecked(self.settings.get("update_on_launch", True))
        self.update_on_launch_cb.clicked.connect(self.set_changed)

        # On closing the program: Minimize to Tray or Terminiate the program
        self.on_close_cb = QComboBox()
        on_close_options = ['Terminiate the program', 'Minimize to tray']
        self.on_close_cb.addItems(on_close_options)
        self.on_close_cb.setCurrentIndex(self.settings.get("on_close", 0))
        self.on_close_cb.currentIndexChanged.connect(self.set_changed)
        self.on_close_cb.setItemData(0, "Closing the program will fully close the window.", Qt.ToolTipRole)
        self.on_close_cb.setItemData(1, "Closing the program will minimize it to the system tray.\nProgram can be restored by pressing the Toggle Overlay Keybind or through the system tray.", Qt.ToolTipRole)

        self.local_icons_cb = QCheckBox()
        self.local_icons_cb.setChecked(self.settings.get("local_icons", True))
        self.local_icons_cb.clicked.connect(self.set_changed)

        ### Keybindings Section
        # Toggle Overlay Keybind
        self.toggle_overlay_keybind_button = KeybindButton()
        self.toggle_overlay_keybind_button.setText(self.settings.get("toggle_overlay_keybind", "alt+d"))
        self.toggle_overlay_keybind_button.setAutoDefault(False)
        self.toggle_overlay_keybind_button.setDefault(False)
        self.toggle_overlay_keybind_button.clicked.connect(self.set_changed)

        # When window in focus keybind: 
        self.keybind_minimize = QComboBox()
        keybind_options = ['Minimize window', 'Hide window (restore through the keybind or system tray)']
        self.keybind_minimize.addItems(keybind_options)
        self.keybind_minimize.setCurrentIndex(self.settings.get("keybind_minimize", 0))
        self.keybind_minimize.currentIndexChanged.connect(self.set_changed)

        ### Appearance Section
        self.theme_selector = QComboBox()
        self.color_selector = QComboBox()

        # Add theme options including 'None'
        self.theme_selector.addItems(['None', 'Dark', 'Light'])

        # Add color options
        self.colors = ['Amber', 'Blue', 'Cyan', 'Lightgreen', 'Pink', 'Purple', 'Red', 'Teal', 'Yellow']
        self.color_selector.addItems(self.colors)

        # Retrieve and set theme from settings
        self.set_theme = self.settings.get("theme", "None")
        if '_' in self.set_theme:
            split_theme = self.set_theme.rsplit('.', 1)[0]
            theme, color = split_theme.split('_', 1)

            if theme.capitalize() in ['None', 'Dark', 'Light']:
                self.theme_selector.setCurrentText(theme.capitalize())

            if color.capitalize() in self.colors:
                self.color_selector.setCurrentText(color.capitalize())
        else:
            logger.error("Theme format is invalid. Themes will be set to default.")
            self.theme_selector.setCurrentText("None")  # Set default to 'None'

        # Connect signals for theme and color selection
        self.theme_selector.currentIndexChanged.connect(self.update_theme)
        self.color_selector.currentIndexChanged.connect(self.update_theme)

        self.window_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_opacity_slider.setMinimum(30)
        self.window_opacity_slider.setMaximum(100)
        self.window_opacity_slider.setSingleStep(1)
        self.window_opacity_slider.setSliderPosition(self.settings.get("window_opacity", 100))
        self.window_opacity_slider.valueChanged.connect(self.opacity_slider_changed)

        # Re drawing due to change in Max Rows/Cols is heavy so only redraw it if these are changed
        self.redraw_request = False

        self.max_rows_sb = QSpinBox()
        self.max_rows_sb.setValue(self.settings.get("max_rows", 20))
        self.max_rows_sb.setRange(0, 100)
        self.max_rows_sb.valueChanged.connect(self.redraw_setting_changed)
        self.max_cols_sb = QSpinBox()
        self.max_cols_sb.setValue(self.settings.get("max_cols", 40))
        self.max_cols_sb.setRange(0, 100)
        self.max_cols_sb.valueChanged.connect(self.redraw_setting_changed)

        self.global_font_color = self.settings.get("global_font_color", "white") #default white

        # Outer layout is for default padding. I.e. Separators which have no padding
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0) # Default to no padding

        # Padding for non-separators
        left_padding = 20

        # General Section
        outer_layout.addLayout(create_separator("Program Behavior"))
        general_inner_layout = QFormLayout()
        general_inner_layout.setContentsMargins(left_padding, 0, 0, 0)
        general_inner_layout.addRow("Update on Launch", self.update_on_launch_cb)
        general_inner_layout.addRow("On closing the program:", self.on_close_cb)
        general_inner_layout.addRow("Save icons locally", self.local_icons_cb)
        general_inner_layout.itemAt(0).widget().setToolTip("Attempt to update upon launching the program.")
        general_inner_layout.itemAt(2).widget().setToolTip("When the program is closed it will")
        general_inner_layout.itemAt(4).widget().setToolTip("When checked, will save a copy of the icon locally. \nWhen unchecked uses the direct path to the image when it was set.")
        outer_layout.addLayout(general_inner_layout)

        # Keybindings Section
        outer_layout.addLayout(create_separator("Keybindings"))
        keybindings_inner_layout = QFormLayout()
        keybindings_inner_layout.setContentsMargins(left_padding, 0, 0, 0)
        keybindings_inner_layout.addRow("Toggle Overlay Keybind", self.toggle_overlay_keybind_button)
        keybindings_inner_layout.addRow("Keybind minimize", self.keybind_minimize)
        keybindings_inner_layout.itemAt(0).widget().setToolTip("Keybind toggles the window between minimized and focused states.")
        keybindings_inner_layout.itemAt(2).widget().setToolTip("Behavior when the window is in focus, and keybind pressed")
        outer_layout.addLayout(keybindings_inner_layout)

        # Appearance Section
        outer_layout.addLayout(create_separator("Appearance"))
        appearance_inner_layout = QFormLayout()
        appearance_inner_layout.setContentsMargins(left_padding, 0, 0, 0)
        appearance_inner_layout.addRow("Theme", self.theme_selector)
        appearance_inner_layout.addRow("", self.color_selector)
        appearance_inner_layout.addRow("Overlay Opacity", self.window_opacity_slider)
        appearance_inner_layout.addRow("Max rows", self.max_rows_sb)
        appearance_inner_layout.addRow("Max Columns", self.max_cols_sb)
        outer_layout.addLayout(appearance_inner_layout)

        # Adds a spacer at the end which pushes up all other separators/content in the tab
        outer_layout.addStretch(1)
        general_layout.addLayout(outer_layout)


    def add_background_tab(self, background_layout):
        # background path clearable line edits
        self.background_video = ClearableLineEdit()
        self.background_image = ClearableLineEdit()
        self.background_video.setText(self.settings.get("background_video", ""))
        self.background_image.setText(self.settings.get("background_image", ""))
        self.background_video.textChanged.connect(self.set_changed)
        self.background_image.textChanged.connect(self.set_changed)
        # folder buttons to open path in fileDialog
        video_folder_button = QPushButton(self)
        video_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        video_folder_button.setIconSize(QSize(16,16))
        video_folder_button.setAutoDefault(False)
        video_folder_button.setDefault(False)
        video_folder_button.clicked.connect(self.video_folder_button_clicked)
        image_folder_button = QPushButton(self)
        image_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        image_folder_button.setIconSize(QSize(16,16))
        image_folder_button.setAutoDefault(False)
        image_folder_button.setDefault(False)
        image_folder_button.clicked.connect(self.image_folder_button_clicked)
        # layouts to add folder buttons
        video_folder_layout = QHBoxLayout()
        video_folder_layout.addWidget(self.background_video)
        video_folder_layout.addWidget(video_folder_button)
        image_folder_layout = QHBoxLayout()
        image_folder_layout.addWidget(self.background_image)
        image_folder_layout.addWidget(image_folder_button)
        background_layout.addRow("Background Video path:", video_folder_layout)
        background_layout.addRow("Background Image path:", image_folder_layout)


        # Background source row:
        self.background_selector = QComboBox()
        background_options = ["First found", "Both", "Video only", "Image only", "None"]
        self.background_selector.addItems(background_options)
        background_layout.addRow("Background sourcing:", self.background_selector)
        set_bg_option = self.settings.get("background_source", "First found")
        # format for background_source is no capitalize and "_" instead of " " therefore revert both
        self.background_selector.setCurrentText(set_bg_option.replace("_", " ").capitalize())
        self.background_selector.currentIndexChanged.connect(self.set_changed)

        # Background Z Order adjustment (for background option = "Both")
        self.bg_z_order_selector = QComboBox()
        bg_z_order_options = ["Video on top", "Image on top"]
        self.bg_z_order_selector.addItems(bg_z_order_options)
        self.bg_z_order_label = QLabel("Display order")
        self.bg_z_order_selector.setCurrentIndex(self.settings.get("bg_z_order", 0))
        background_layout.addRow(self.bg_z_order_label, self.bg_z_order_selector)
        self.bg_z_order_selector.currentIndexChanged.connect(self.bg_z_order_changed)

        # Video background alignments
        self.video_horizontal_slider = SliderWithInput(-150, 150, 1, self.settings.get("video_x_offset", 0)* 100)
        self.video_horizontal_slider.valueChanged.connect(self.video_location_changed)
        self.video_horizontal_label = QLabel("Video horizontal adjustment:")
        background_layout.addRow(self.video_horizontal_label, self.video_horizontal_slider)

        self.video_vertical_slider = SliderWithInput(-150, 150, 1, -self.settings.get("video_y_offset", 0)* 100)
        self.video_vertical_slider.valueChanged.connect(self.video_location_changed)
        self.video_vertical_label = QLabel("Video vertical adjustment:")
        background_layout.addRow(self.video_vertical_label, self.video_vertical_slider)

        initial_zoom = self.settings.get("video_zoom", 1.00)
        self.video_zoom_slider = SliderWithInput(0, 200, 1, self.video_zoom_to_slider(initial_zoom))
        self.video_zoom_slider.valueChanged.connect(self.video_zoom_changed)
        self.video_zoom_label = QLabel("Video zoom adjustment:")
        background_layout.addRow(self.video_zoom_label, self.video_zoom_slider)


        # Image background alignments
        self.image_horizontal_slider = SliderWithInput(-150, 150, 1, self.settings.get("image_x_offset", 0)* 100)
        self.image_horizontal_slider.valueChanged.connect(self.image_location_changed)
        self.image_horizontal_label = QLabel("Image horizontal adjustment:")
        background_layout.addRow(self.image_horizontal_label, self.image_horizontal_slider)

        self.image_vertical_slider = SliderWithInput(-150, 150, 1, -self.settings.get("image_y_offset", 0)* 100)
        self.image_vertical_slider.valueChanged.connect(self.image_location_changed)
        self.image_vertical_label = QLabel("Image vertical adjustment:")
        background_layout.addRow(self.image_vertical_label, self.image_vertical_slider)

        initial_zoom = self.settings.get("image_zoom", 1.00)
        self.image_zoom_slider = SliderWithInput(0, 200, 1, self.image_zoom_to_slider(initial_zoom))
        self.image_zoom_slider.valueChanged.connect(self.image_zoom_changed)
        self.image_zoom_label = QLabel("Image zoom adjustment:")
        background_layout.addRow(self.image_zoom_label, self.image_zoom_slider)

        # Custom bg fill checkbox
        self.custom_bg_fill_cb = QCheckBox()
        self.custom_bg_fill_cb.setChecked(self.settings.get("custom_bg_fill", False))
        self.custom_bg_fill_cb.clicked.connect(self.custom_bg_fill)
        background_layout.addRow("Custom background fill:", self.custom_bg_fill_cb)


        # Custom bg color
        self.bg_color = self.settings.get("custom_bg_color", "white")
        self.custom_bg_color = QPushButton("", self)
        self.custom_bg_color.clicked.connect(self.open_bg_color_dialog)
        self.custom_bg_color.setFixedSize(QSize(75, 30))
        self.custom_bg_color.setAutoDefault(False)
        self.custom_bg_color.setDefault(False)
        self.custom_bg_color_label = QLabel("Custom bg color:")
        background_layout.addRow(self.custom_bg_color_label, self.custom_bg_color)

    def add_icon_tab(self, icon_layout):

        ### Icon Appearance
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0) # Default to no padding
        self.icon_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.icon_size_slider.setMinimum(30)
        self.icon_size_slider.setMaximum(256)
        self.icon_size_slider.setSingleStep(1)
        self.icon_size_slider.setSliderPosition(self.settings.get("icon_size", 100))
        self.icon_size_slider.valueChanged.connect(self.label_size_changed)

        ### Icon Name
        ## Name font color:
        self.icon_name_color_box = QPushButton("", self)
        self.icon_name_color_box.clicked.connect(self.open_color_dialog)
        self.icon_name_color_box.setFixedSize(QSize(75, 30))
        self.icon_name_color_box.setAutoDefault(False)
        self.icon_name_color_box.setDefault(False)

        reset_name_color_pb = QPushButton("Reset")
        reset_name_color_pb.setAutoDefault(False)
        reset_name_color_pb.setDefault(False)
        reset_name_color_pb.setFixedWidth(75)
        reset_name_color_pb.clicked.connect(self.reset_default_font_color_clicked)
        name_color_layout = QHBoxLayout()
        name_color_layout.addWidget(self.icon_name_color_box)
        name_color_layout.addWidget(reset_name_color_pb)

        # Name Default font size
        self.icon_name_font_size_sb = QSpinBox()
        self.icon_name_font_size_sb.setValue(self.settings.get("global_font_size", 10))
        self.icon_name_font_size_sb.setRange(0, 100)
        self.icon_name_font_size_sb.valueChanged.connect(self.redraw_setting_changed)

        reset_name_font_size_pb = QPushButton("Reset")
        reset_name_font_size_pb.setAutoDefault(False)
        reset_name_font_size_pb.setDefault(False)
        reset_name_font_size_pb.setFixedWidth(75)
        reset_name_font_size_pb.clicked.connect(self.reset_default_font_size_clicked)
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.icon_name_font_size_sb)
        font_size_layout.addWidget(reset_name_font_size_pb)


        left_padding = 20

        outer_layout.addLayout(create_separator("Icon Appearance"))

        icon_appearance_inner_layout = QFormLayout()
        icon_appearance_inner_layout.setContentsMargins(left_padding, 0, 0, 0)
        icon_appearance_inner_layout.addRow("Desktop Icon Size", self.icon_size_slider)
        outer_layout.addLayout(icon_appearance_inner_layout)

        outer_layout.addLayout(create_separator("Icon Name"))

        icon_name_inner_layout = QFormLayout()
        icon_name_inner_layout.setContentsMargins(left_padding, 0, 0, 0)
        icon_name_inner_layout.addRow("Name font color", name_color_layout)
        icon_name_inner_layout.addRow("Default Font size", font_size_layout)
        icon_name_inner_layout.itemAt(2).widget().setToolTip("Sets the default font size for icon names. This can be adjusted individually in the icon edit menu.")
        outer_layout.addLayout(icon_name_inner_layout)

        # Adds a spacer at the end which pushes up all other separators/content in the tab
        outer_layout.addStretch(1)
        icon_layout.addLayout(outer_layout, 0)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # If a button is focused, trigger its click on Enter
                focused_widget = QApplication.focusWidget()
                if isinstance(focused_widget, QPushButton):
                    focused_widget.click()
                    return True
                elif isinstance(focused_widget, QComboBox):
                    focused_widget.showPopup()
                    return True
                elif isinstance(focused_widget, QCheckBox):
                    focused_widget.toggle()
                    return True
        return super().eventFilter(obj, event)

    def update_custom_bg_color_visibility(self):
        if self.custom_bg_fill_cb.isChecked():
            self.custom_bg_color.show()
            self.custom_bg_color_label.show()
        else:
            self.custom_bg_color.hide()
            self.custom_bg_color_label.hide()
        self.resize_window()
        
    def update_background_sliders_visibility(self):
        video_widgets = [
            self.video_horizontal_label,
            self.video_horizontal_slider,
            self.video_vertical_label,
            self.video_vertical_slider,
            self.video_zoom_label,
            self.video_zoom_slider,
        ]
        image_widgets = [
            self.image_horizontal_label,
            self.image_horizontal_slider,
            self.image_vertical_label,
            self.image_vertical_slider,
            self.image_zoom_label,
            self.image_zoom_slider,
        ]
        
        video_show = self.background_selector.currentIndex() in [0, 1, 2]
        image_show = self.background_selector.currentIndex() in [0, 1, 3]
        
        for widget in video_widgets:
            widget.setVisible(video_show)

        for widget in image_widgets:
            widget.setVisible(image_show)

        # Controlling display of "Display order setting" (Only shows when background sourcing = "Both" (index = 1))
        self.bg_z_order_label.setVisible(self.background_selector.currentIndex() == 1)
        self.bg_z_order_selector.setVisible(self.background_selector.currentIndex() == 1)

        self.resize_window()
    
    def resize_window(self, width=0, height=0):
        current_position = self.pos()
        logger.info(f"Current Position: {current_position}")
        screen_geometry = self.screen().availableGeometry()
        # 30 height is for top window bar, 30 width is for padding.
        target_height = min(self.content_widget.sizeHint().height() + 30 + self.save_button.sizeHint().height() + height, screen_geometry.height())
        target_width = min(self.content_widget.sizeHint().width() + 30 + width, screen_geometry.width())
        logger.info(f"resizing to ideal target width = {target_width}, target height = {target_height}")
        self.resize(target_width, target_height)
        logger.info(f"Setting maximum size for window: {screen_geometry.width()},  {screen_geometry.height()-40}")
        self.setMaximumSize(screen_geometry.width(), screen_geometry.height()-40) # -40 on height to account for windows taskbar

        if current_position.y() + self.height() >= screen_geometry.height()-40:
            logger.info("Moving up to fit entire menu on screen.")
            new_position = QPoint(current_position.x(), (screen_geometry.height()-40 - self.height()))
            if new_position.y() < 0:
                logger.error(f"Attempted to place the window at negative height: {new_position.y()}, args: {current_position.y()}, {self.height()}, {screen_geometry.height()-40}")
            else:
                self.move(new_position)

    def bg_z_order_changed(self):
        self.set_changed()
        # Only bothering with setting the Z Value of the image as it is easier to adjust, video_item is always Z value = -2.
        # If "Video on top" put image_background at -3 Z value (below Video item)
        if self.bg_z_order_selector.currentIndex() == 0:
            self.parent().grid_widget.image_background_manager.set_z_value(-3)
        # "Image on top" put image_background at -1 Z value (above Video item)
        else:
            self.parent().grid_widget.image_background_manager.set_z_value(-1)


    def open_color_dialog(self):
        self.redraw_setting_changed() # redraw or it won't update
        # Open the color dialog and get the selected color
        color = QColorDialog.getColor(QColor(self.global_font_color))

        if color.isValid():
            self.global_font_color = color.name()  # Get the hex code of the selected color
            self.display_theme()
    def open_bg_color_dialog(self):
        self.set_changed() # Background color does not need full redraw as it calls render_bg itself.
        
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(QColor(self.bg_color))

        # Preview based on currently selected color in selector.
        def update_bg_color(color):
            if color.isValid():
                color = color.name()
                self.parent().grid_widget.render_bg(bg_enabled=True, bg_color=color)

        color_dialog.currentColorChanged.connect(update_bg_color)

        # Accepted means full return (clicked Ok)
        if color_dialog.exec()== QDialog.Accepted:
            selected_color = color_dialog.currentColor()
            if selected_color.isValid():
                self.bg_color = selected_color.name()
                self.display_theme()
                self.parent().grid_widget.render_bg(bg_enabled=True, bg_color=self.bg_color)
        # User did not select a color (Revert back to color it had when opening)
        else:
            logger.info("User closed Custom bg color selector without selecting")
            self.parent().grid_widget.render_bg(bg_enabled=True, bg_color=self.bg_color)

    def custom_bg_fill(self):
        self.set_changed()
        if self.custom_bg_fill_cb.isChecked():
            self.parent().grid_widget.render_bg(bg_enabled = True, bg_color = self.bg_color)
        else:
            self.parent().grid_widget.render_bg(bg_enabled = False)
            

    # Only called when a setting which requires redrawing of desktop icons is changed.
    def redraw_setting_changed(self):
        if not self.redraw_request:
            self.set_changed()
            self.redraw_request = True
            logger.info("Redraw request now set to True")

    def set_changed(self):
        if not self.is_changed:
            logger.info("Settings changed")
            self.is_changed = True

    def update_theme(self):
        category = self.theme_selector.currentText().lower()
        color = self.color_selector.currentText().lower()
        theme = f"{category}_{color}.xml"
        logger.info(f"Selected theme: {theme}")
        self.parent().change_theme(theme)
        self.display_theme()
        self.resize_window()
        self.parent().grid_widget.render_bg()
        self.is_changed = True

    def display_theme(self):
        selected_theme = self.theme_selector.currentText()
        
        if selected_theme == 'None':
            self.color_selector.hide()  # Hide color selector if 'None' is selected
            self.enable_stylesheet(False)
        else:
            self.color_selector.show()  # Show color selector for other themes
            self.enable_stylesheet(True)


    # Directly toggles between "Theme" stylesheet and "None" stylesheet. All stylesheet changes should happen here. Anything done outside only makes it hard to keep track of.
    def enable_stylesheet(self, bool):
        self.primary_color = getattr(self.parent(), 'primary_color', '#202020')
        if bool:
            logger.info(f"Setting stylesheet to match qt-material, with primary color = {self.primary_color}")
            self.setStyleSheet((f"""
                QSlider::handle:focus {{
                    border: 2px solid {self.primary_color};
                }}
            """))
            self.icon_name_color_box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.global_font_color};
                    border: 1px solid black;
                }}
                QPushButton:focus {{
                    border: 3px solid {self.primary_color};
                }}
            """)
            self.custom_bg_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.bg_color};
                    border: 1px solid black;
                }}
                QPushButton:focus {{
                    border: 3px solid {self.primary_color};
                }}
            """)
        else:
            self.setStyleSheet("")

            # Required for changing color of the button to match the set color.
            self.icon_name_color_box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.global_font_color};
                }}
            """)
            self.custom_bg_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.bg_color};
                    border: 1px solid black;
                }}
                QPushButton:focus {{
                    border: 3px solid {self.primary_color};
                }}
            """)
        



    def opacity_slider_changed(self, i):
        self.set_changed()
        if self.parent():
            self.parent().change_opacity(i)
        self.setWindowOpacity(1.0)

    # Depreciated, it causes crashing for attempting to preview and changing rows/cols in the same save.
    def label_size_changed(self, i):
        self.redraw_setting_changed()

        # Can cause crashing upon changing icon_size and max rows/cols in the same save.
        #self.parent().grid_widget.update_icon_size(i)

    
    def video_location_changed(self):
        self.parent().grid_widget.video_manager.move_video(-float (self.video_horizontal_slider.get_value()/ 100.0), -float (self.video_vertical_slider.get_value()/ 100.0)) 
        self.set_changed()

    def video_zoom_changed(self):
        self.parent().grid_widget.video_manager.zoom_video(self.slider_to_video_zoom())
        self.set_changed()

    # Override and call with min_zoom, max_zoom for further scaling in/out.
    def video_zoom_to_slider(self, zoom_factor, min_zoom=0.15, max_zoom=15.0, scale_factor= 2.1):
        # min_zoom must be < 1.00, and max_zoom must be > 1.00
        if min_zoom >= 1.0 or max_zoom <= 1.00:
            logger.error(f"user is a dumbass and overrided min_zoom or max_zoom incorrectly: min_zoom = {min_zoom}, max_zoom = {max_zoom}")
            return
        if zoom_factor <= 1.0:
            # Scale linearly between min_zoom and 1.0 for slider range 0–100
            return int((zoom_factor - min_zoom) / (1.0 - min_zoom) * 100)
        else:
            # Scale NON-linearly between 1.0 and max_zoom for slider range 101–200
            return int(100 + ((zoom_factor - 1.0) / (max_zoom - 1.0)) ** (1 / scale_factor) * 100)

    # Override and call with min_zoom, max_zoom for further scaling in/out.
    def image_zoom_to_slider(self, zoom_factor, min_zoom=0.15, max_zoom=15.0, scale_factor= 2.1):
        # min_zoom must be < 1.00, and max_zoom must be > 1.00
        if min_zoom >= 1.0 or max_zoom <= 1.00:
            logger.error(f"user is a dumbass and overrided min_zoom or max_zoom incorrectly: min_zoom = {min_zoom}, max_zoom = {max_zoom}")
            return
        if zoom_factor <= 1.0:
            # Scale linearly between min_zoom and 1.0 for slider range 0–100
            return int((zoom_factor - min_zoom) / (1.0 - min_zoom) * 100)
        else:
            # Scale NON-linearly between 1.0 and max_zoom for slider range 101–200
            return int(100 + ((zoom_factor - 1.0) / (max_zoom - 1.0)) ** (1 / scale_factor) * 100)
        
    def slider_to_video_zoom(self, min_zoom=0.15, max_zoom=15.0, scale_factor= 2.1):
        slider_value = self.video_zoom_slider.get_value()
        if slider_value <= 100:
            # Reverse linear scaling from slider range 0–100 to zoom range min_zoom–1.0
            return min_zoom + (slider_value / 100.0) * (1.0 - min_zoom)
        else:
            # Reverse NON-linear scaling (difference between 100 and 101 is < difference between 199 and 200) from slider range 101–200 to zoom range 1.0–max_zoom
            normalized_value = (slider_value - 100) / 100.0
            return 1.0 + (normalized_value ** scale_factor) * (max_zoom - 1.0)

    def slider_to_image_zoom(self, min_zoom=0.15, max_zoom=15.0, scale_factor= 2.1):
        slider_value = self.image_zoom_slider.get_value()
        if slider_value <= 100:
            # Reverse linear scaling from slider range 0–100 to zoom range min_zoom–1.0
            return min_zoom + (slider_value / 100.0) * (1.0 - min_zoom)
        else:
            # Reverse NON-linear scaling (difference between 100 and 101 is < difference between 199 and 200) from slider range 101–200 to zoom range 1.0–max_zoom
            normalized_value = (slider_value - 100) / 100.0
            return 1.0 + (normalized_value ** scale_factor) * (max_zoom - 1.0)

    def image_location_changed(self):
        self.parent().grid_widget.image_background_manager.move_background(-float (self.image_horizontal_slider.get_value()/ 100.0), -float (self.image_vertical_slider.get_value()/ 100.0)) 
        self.set_changed()

    def image_zoom_changed(self):
        self.parent().grid_widget.image_background_manager.zoom_background(self.slider_to_image_zoom())
        self.set_changed()


    def save_settings(self):

        #cleanup background paths
        self.cleanup_bg_paths()
        if self.background_video.text() != "" and os.path.exists(self.background_video.text()) == False:
            logger.warning("Background Video does not exist")
            # Display warning that bg video path does not exist, cancel save if user hits cancel otherwise save.
            if display_bg_video_not_exist(self.background_image.text()) == QMessageBox.Yes:   
                logger.info("User chose to save regardless")
            else:
                logger.info("User chose to cancel saving.")
                return
        if self.background_image.text() != "" and os.path.exists(self.background_image.text())  == False:
            logger.warning("Background Image does not exist")
            #display warning that bg image path does not exist, cancel save if user hits cancel otherwise save.
            if display_bg_image_not_exist(self.background_image.text()) == QMessageBox.Yes:   
                logger.info("User chose to save regardless")
            else:
                logger.info("User chose to cancel saving.")
                return


        # Double check keybind is set to something. Changes it to last saved setting if not. (i.e. click button but don't press anything then hit save)
        self.good_keybind()


        # More optimized to load and modify all settings then save. Than to set_setting() for each setting as set_setting() has load and save overhead.
        settings = load_settings()
        settings["update_on_launch"] = self.update_on_launch_cb.isChecked()
        settings["toggle_overlay_keybind"] = self.toggle_overlay_keybind_button.get_keybind()
        settings["window_opacity"] = self.window_opacity_slider.value()
        settings["theme"] = f"{self.theme_selector.currentText().lower()}_{self.color_selector.currentText().lower()}.xml"
        settings["background_source"] = self.background_selector.currentText().lower().replace(" ", "_")
        settings["background_video"] = self.background_video.text()
        settings["background_image"] = self.background_image.text()
        settings["local_icons"] = self.local_icons_cb.isChecked()
        settings["icon_size"] = self.icon_size_slider.value()
        settings["max_rows"] = self.max_rows_sb.value()
        settings["max_cols"] = self.max_cols_sb.value()
        settings["global_font_color"] = self.global_font_color
        settings["on_close"] = self.on_close_cb.currentIndex()
        settings["keybind_minimize"] = self.keybind_minimize.currentIndex()
        settings["video_x_offset"] = float (self.video_horizontal_slider.get_value()/ 100.0)
        settings["video_y_offset"] = -float (self.video_vertical_slider.get_value()/ 100.0)
        settings["video_zoom"] = self.slider_to_video_zoom()
        settings["custom_bg_fill"] = self.custom_bg_fill_cb.isChecked()
        settings["custom_bg_color"] = self.bg_color
        settings["image_x_offset"] = float (self.image_horizontal_slider.get_value()/ 100.0)
        settings["image_y_offset"] = -float (self.image_vertical_slider.get_value()/ 100.0)
        settings["image_zoom"] = self.slider_to_image_zoom()
        settings["bg_z_order"] = self.bg_z_order_selector.currentIndex()
        settings["global_font_size"] = self.icon_name_font_size_sb.value()
        save_settings(settings)
        if self.parent():
            self.parent().set_hotkey()
            self.parent().grid_widget.render_bg()
            
            

            # Can be a quite heavy impact so only redraw when these values have changed.
            if self.redraw_request:
                self.parent().grid_widget.change_max_grid_dimensions(self.max_rows_sb.value(), self.max_cols_sb.value())
                self.parent().grid_widget.update_icon_size(self.icon_size_slider.value())
                pass
        
        # No need to reload self.settings as after saving this will terminate (self.accept()) and reload settings on next launch.
        self.accept()

    def good_keybind(self):
        if self.toggle_overlay_keybind_button.get_keybind() == "Press a key":
            logger.error("Attempted to save keybind while changing keybind")
            self.toggle_overlay_keybind_button.set_keybind()

    def closeEvent(self, event):
        
        if self.is_changed == False:
            logger.info("Called close with no changes made in settings")
            self.accept()
        else:
            logger.info("Called close with changes in settings")
            if self.main_window_closing != True:
                reply = display_settings_not_saved()
                if reply == QMessageBox.Yes:
                    logger.info("User chose to close the settings menu and revert the changes")
                    self.reject()
                else:
                    logger.info("User chose to cancel the close event.")
                    event.ignore()
            else:
                logger.info("closed from main window, discard changes and do not show warning.")
    

    def cleanup_bg_paths(self):

        #cleanup background_video
        if self.background_video.text().startswith("file:///"):
            self.background_video.setText(self.background_video.text()[8:])  # remove "file:///"
        elif self.background_video.text().startswith("file://"):
            self.background_video.setText(self.background_video.text()[7:])  # Remove 'file://' prefix

        #cleanup background_image
        if self.background_image.text().startswith("file:///"):
            self.background_image.setText(self.background_image.text()[8:])  # remove "file:///"
        elif self.background_image.text().startswith("file://"):
            self.background_image.setText(self.background_image.text()[7:])  # Remove 'file://' prefix


    def video_folder_button_clicked(self):
        self.set_changed()
        directory = None

        current_path = self.background_video.text()

        # Attempt to open the file path at the saved path
        if os.path.exists(current_path) and current_path != "":
            # Use the parent directory of the current path
            directory = os.path.dirname(current_path)
        else:
            # Use default location for Movies (Usually "Videos" folder) if current_path is not a path.
            directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)

        file_dialog = QFileDialog(self)
        if directory is not None:
            file_dialog.setDirectory(directory)

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_video.setText(selected_file)

    def image_folder_button_clicked(self):
        self.set_changed()
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_image.setText(selected_file)
    
    def reset_default_font_size_clicked(self):
        if display_reset_default_font_size_warning() == QMessageBox.Ok:
            logger.info(f"User chose to reset all to default font size: {self.icon_name_font_size_sb.value()}")
            reset_all_to_default_font_size()
            self.parent().grid_widget.redraw_all_icons()
        else:
            logger.info("User chose NOT to reset all font sizes.")

    def reset_default_font_color_clicked(self):
        if display_reset_default_font_color_warning() == QMessageBox.Ok:
            logger.info(f"User chose to reset all icons to default font color: {self.global_font_color}.")
            reset_all_to_default_font_color()
            self.parent().grid_widget.redraw_all_icons()
        else:
            logger.info("User chose NOT to reset all font sizes.")





class KeybindButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Keybind button initialized")
        self.listening = False
        self.key = None  # Store the non-modifier key separately
        self.modifiers = None  # Store the modifiers
        self.clicked.connect(self.enable_listening)
        self.installEventFilter(self)
        self.shift_pressed = False

    def enable_listening(self):
        logger.info("Enable listening called")
        self.listening = True
        self.setText("Press a key")

    def keyPressEvent(self, event):
        if self.listening:
            logger.info(f"Key press event: {event}")
            key = event.key()
            modifiers = event.modifiers()
            logger.info(f"Modifiers = {modifiers}")

            # Set shift_pressed if key = shift. This is used for shift+numpad # keybinding.
            if key == Qt.Key_Shift:
                self.shift_pressed = True
                logger.info("Shift key pressed")

            # Check if the key is from the numpad
            if modifiers & Qt.KeypadModifier:
                # Use a custom mapping for numpad keys
                key_name = self.get_numpad_key_sequence(event)
                logger.info(f"Numpad key detected: {key_name}")
            else:
                # Use custom get_key_sequence to handle shift-modified keys
                key_name = self.get_key_sequence(event)

            logger.info(f"Key name = {key_name}")
            if "enter" in key_name.lower() or "return" in key_name.lower():
                display_multiple_working_keybind_warning(key_name)

            # Handle if a non-modifier key is pressed (e.g., F1, D, etc.)
            if key not in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                logger.info(f"Non-modifier key press: {key_name}")  # Changed to use `key_name`
                self.key = key_name  # Store the key or numpad key name
                self.modifiers = modifiers  # Store the modifiers
                self.finalize_keybind()
            else:
                logger.info(f"Modifier key press: {event.text()}")

        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            def set_false():
                self.shift_pressed = False

            # Instantly resetting shift_pressed will mean that holding shift the hitting num 7
            # Will instantly reset shift_pressed to False. Before running keyPressEvent
            # So delay this very slightly so that it will instead run KeyPressEvent then turn shift off.
            # This allows for detecting shift on a shift numpad # press (which gives a full unique key with no shift modifier.)
            # This self.shift_pressed is only used in get_numpad_key_sequence below because the only time a shift modified key
            # Changes input to a non-shift modified key is when 'shift + numpad #'.
            QTimer.singleShot(100, set_false)
            
            logger.info("Shift key released")

        super().keyReleaseEvent(event)
            

    def get_numpad_key_sequence(self, key_event):
        logger.info(f"SHIFT PRESSED = {self.shift_pressed}")
        # Create local variable as self.shift_pressed is essentially on a 100ms timer before turning to False.
        shift_pressed = self.shift_pressed
        logger.info("getting numpad key sequence")
        key = key_event.key()
        modifiers = key_event.modifiers()
        logger.info(f"modifiers = {modifiers}")

        logger.info(f"Key event = {key_event}")
        logger.info(f"Key = {key}")

        # List to store key sequence parts
        sequence_parts = []

        # Mapping of native numpad keys to "num X" representation
        numpad_mapping = {
            Qt.Key_Insert: "shift+num 0" if shift_pressed else "num 0",
            Qt.Key_End: "shift+num 1" if shift_pressed else "num 1",
            Qt.Key_Down: "shift+num 2" if shift_pressed else "num 2",
            Qt.Key_PageDown: "shift+num 3" if shift_pressed else "num 3",
            Qt.Key_Left: "shift+num 4" if shift_pressed else "num 4",
            Qt.Key_Clear: "shift+num 5" if shift_pressed else "num 5",
            Qt.Key_Right: "shift+num 6" if shift_pressed else "num 6",
            Qt.Key_Home: "shift+num 7" if shift_pressed else "num 7",
            Qt.Key_Up: "shift+num 8" if shift_pressed else "num 8",
            Qt.Key_PageUp: "shift+num 9" if shift_pressed else "num 9",
            Qt.Key_Delete: "shift+decimal" if shift_pressed else "decimal",
            Qt.Key_NumLock: "num lock",
            Qt.Key_Slash: "shift+num /" if shift_pressed else "num /", # still broken with scan code = 57397
            Qt.Key_Plus: "num add",
            Qt.Key_Period: "decimal",
            # shift+num "*, -, Enter, numlock" all seem to work by default / is still buggy.

        }

        # If non-normal numpad key take the key and convert it to the numpad equivalent
        if key in numpad_mapping:
            sequence_parts.append(numpad_mapping[key])
        else:
            # Handle any non-numpad keys that may be mapped to logical keys
            sequence_parts.append(f"num {QKeySequence(key).toString()}")

        # Return the formatted key sequence string (e.g., "Shift+num 7")
        seq = "+".join(sequence_parts)
        logger.info(f"Sequence = {seq}")
        return seq

    
    def get_key_sequence(self, key_event):
        logger.info("getting normal key sequence")
        # Create a list to store the key sequence parts
        sequence_parts = []
        key = key_event.key()
        modifiers = key_event.modifiers()
        logger.info(f"modifiers = {modifiers}")
        logger.info(f"Key event = {key_event}")
        logger.info(f"Key = {key}")

        # Check if Shift is pressed
        shift_pressed = key_event.modifiers() & Qt.ShiftModifier

        # Handle regular alphanumeric and shifted special characters
        if key_event.key() >= Qt.Key_Space and key_event.key() <= Qt.Key_AsciiTilde:
            if shift_pressed:
                # Manually map shifted characters to their unshifted versions
                shifted_map = {
                    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8',
                    '(': '9', ')': '0', '_': '-', '+': '=', '{': '[', '}': ']', ':': ';',
                    '"': "'", '<': ',', '>': '.', '?': '/', '|': '\\'
                }
                # Get the character typed and map it back to the unshifted key
                base_key = shifted_map.get(key_event.text(), key_event.text())
                sequence_parts.append(base_key)
            else:
                # For unmodified alphanumeric keys, just append the character
                base_key = key_event.text()
                sequence_parts.append(base_key)
        else:
            # If it's some other special key, handle it using QKeySequence
            base_key = QKeySequence(key_event.key()).toString()
            sequence_parts.append(base_key)

        # Join the parts to form the final key sequence string
        return "+".join(sequence_parts)

    def finalize_keybind(self):
        key_name = self.key
        modifier_names = []

        # Add modifiers to keybind if modifier detected, and not already in key_name (essentially ensure modifier only included 1 time.)
        if self.modifiers & Qt.ShiftModifier and "shift" not in key_name.lower():
            modifier_names.append("Shift")
        if self.modifiers & Qt.ControlModifier and "ctrl" not in key_name.lower():
            modifier_names.append("Ctrl")
        if self.modifiers & Qt.AltModifier and "alt" not in key_name.lower():
            modifier_names.append("Alt")
        if self.modifiers & Qt.MetaModifier:
            modifier_names.append("Meta")

        full_key_name = "+".join(modifier_names + [key_name])
        logger.info(f"Full key name: {full_key_name}")
        self.setText(full_key_name)
        self.listening = False

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and self.listening:
            logger.info(f"Key press detected by event filter: {event}")
            self.keyPressEvent(event)
            return True
        return super().eventFilter(source, event)

    def get_keybind(self):
        return self.text()

    def set_keybind(self):
        logger.error("Resetting keybind to last keybind saved")
        self.setText(get_setting("toggle_overlay_keybind", "alt+d"))
