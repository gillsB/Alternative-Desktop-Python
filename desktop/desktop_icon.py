from PySide6.QtWidgets import QGraphicsItem, QDialog, QMenu, QMessageBox, QToolTip
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPixmap, QPainterPath, QPen, QAction, QMovie, QPixmapCache
from util.settings import get_setting
from util.config import get_icon_data, is_default, get_data_directory, change_launch, set_entry_to_default, get_icon_font_size, get_icon_font_color
from menus.run_menu_dialog import RunMenuDialog
from menus.display_warning import (display_no_successful_launch_error, display_file_not_found_error, display_no_default_type_error, display_failed_cleanup_warning, 
                                   display_path_and_parent_not_exist_warning, display_delete_icon_warning, display_cannot_swap_icons_warning)
import os
import logging
import shlex
import subprocess
import send2trash

logger = logging.getLogger(__name__)



class DesktopIcon(QGraphicsItem):
    def __init__(self, row, col, icon_size=64, parent=None):
        super().__init__(parent)



        # Need to be changed manually usually by DesktopGrid (self.desktop_icons[(row, col)].row = X)
        self.row = row
        self.col = col
        self.pixmap = None

        data = get_icon_data(row, col)
        self.name = data['name']
        self.icon_path = data['icon_path']
        self.executable_path = data['executable_path']
        self.command_args = data['command_args']
        self.website_link = data['website_link']
        self.launch_option = data['launch_option']
        self.use_global_font_size = data['use_global_font_size']
        self.use_global_font_color = data['use_global_font_color']
        self.font_size = get_icon_font_size(self.row, self.col)
        self.font_color = get_icon_font_color(self.row, self.col)

        self.movie = None # For loading a gif
        self.init_movie() # Load movie if .gif icon_path

        self.text_height = 0

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setAcceptDrops(True)

        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.padding = 30
        self.font = QFont(get_setting("font", "Arial"), self.font_size)

        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.load_pixmap()
        self.log_paints = False
        self.paints = 1
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_tooltip)
        self.last_pos = None
        self.tooltip_shown = False
        self.dragging = False
        self.distance = 0

    def reload_from_config(self):
        logger.info("Reloaded self fields from config.")
        data = get_icon_data(self.row, self.col)
        self.name = data['name']
        self.icon_path = data['icon_path']
        self.executable_path = data['executable_path']
        self.command_args = data['command_args']
        self.website_link = data['website_link']
        self.launch_option = data['launch_option']
        self.use_global_font_size = data['use_global_font_size']
        self.use_global_font_color = data['use_global_font_color']
        self.font_size = get_icon_font_size(self.row, self.col)
        self.font_color = get_icon_font_color(self.row, self.col)
        self.init_movie()
        self.load_pixmap(True)
        self.update_font()

    def update_font(self, font_size= None):
        print(f"update font called with font_size = {font_size}")
        if font_size == None:
            self.font = QFont(get_setting("font", "Arial"), self.font_size)
        else:
            print(f"using custom font size")
            self.font = QFont(get_setting("font", "Arial"), font_size)
        self.update()

    def update_font_color(self, font_color= None):
        self.font_color = font_color
        self.update()


    def update_size(self, new_size):
        self.icon_size = new_size
        self.prepareGeometryChange()

    def boundingRect(self) -> QRectF:
        self.text_height = self.calculate_text_height(self.name)
        return QRectF(0, 0, self.icon_size, self.icon_size + self.text_height + self.padding)
    

    # reset_cache variable defaults to false, when True will place the new icon into cache and discard old icon.
    def load_pixmap(self, reset_cache=False):
        if self.movie:
            return
        if self.icon_path and os.path.exists(self.icon_path):
            cached_pixmap = QPixmapCache.find(self.icon_path)
            # If cached pixmap is found and function called without an override to reset the cached version, load from cache.
            # Else, get the new pixmap from path, and store it.
            if cached_pixmap and not reset_cache:
                logger.debug(f"Cached pixmap found for {self.icon_path}")
                self.pixmap = cached_pixmap
            else:
                self.pixmap = QPixmap(self.icon_path)
                if self.pixmap.isNull():
                    logger.error(f"Failed to load pixmap from {self.icon_path}")
                    self.load_unknown_pixmap()
                else:
                    self.pixmap = self.pixmap.scaled(
                        self.icon_size - 4,
                        self.icon_size - 2,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    QPixmapCache.insert(self.icon_path, self.pixmap)  # Cache the loaded pixmap
            self.update()
        else:
            if self.icon_path != "":
                logger.warning(f"Invalid icon path: {self.icon_path} Loading unknown.png instead")
            self.load_unknown_pixmap()

    def load_unknown_pixmap(self):
        unknown_path = "assets/images/unknown.png"
        if os.path.exists(unknown_path):
            self.pixmap = QPixmap(unknown_path)
            if self.pixmap.isNull():
                logger.error(f"Failed to load unknown.png")
            else:
                self.pixmap = self.pixmap.scaled(
                        self.icon_size - 4,
                        self.icon_size - 2,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                )
                QPixmapCache.insert("unknown", self.pixmap)
        else:
            logger.error(f"unknown.png not found at {unknown_path}")
        self.update()


    def paint(self, painter: QPainter, option, widget=None):
        if self.log_paints:
            if self.paints % 100 == 0:
                logger.warning(f"Painted {self.row}, {self.col}  {self.paints} times.")
                self.paints = 0
            self.paints += 1

        if not is_default(self.row, self.col):
            if self.movie:
                # Get the current frame and draw it
                frame = self.movie.currentPixmap()
                if not frame.isNull():
                    scaled_frame = frame.scaled(self.icon_size - 4, self.icon_size - 2, 
                                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    x_offset = (self.icon_size - scaled_frame.width()) / 2
                    y_offset = (self.icon_size - scaled_frame.height()) / 2
                    painter.drawPixmap(x_offset, y_offset, scaled_frame)
                else:
                    logger.error(f"Warning: Frame: {frame} is null.")
            elif self.pixmap and not self.pixmap.isNull():
                x_offset = (self.icon_size - self.pixmap.width()) / 2
                y_offset = (self.icon_size - self.pixmap.height()) / 2
                painter.drawPixmap(x_offset, y_offset, self.pixmap)
            else:
                logger.warning(f"No valid pixmap for {self.row}, {self.col}")
                self.load_unknown_pixmap()
                if self.pixmap and not self.pixmap.isNull():
                    painter.drawPixmap(0, 0, self.icon_size, self.icon_size, self.pixmap)
                else:
                    logger.error(f"Failed to load unknown pixmap for {self.row}, {self.col}")

        # If the user has set the font size to 0, do not render the text.
        if self.font_size > 0:
            painter.setFont(self.font)

            lines = self.get_multiline_text(self.font, self.name)

            # Define the outline color and main text color
            outline_color = QColor(0, 0, 0)  # Black outline Eventually will have a setting

            text_color = QColor(self.font_color)

            for i, line in enumerate(lines):
                text_y = self.icon_size + self.padding / 2 + i * 15

                # Create a QPainterPath for the text outline
                path = QPainterPath()
                path.addText(0, text_y, self.font, line)

                # Draw the text outline with a thicker pen
                painter.setPen(QColor(outline_color))
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(outline_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)) # 4 = pixels of outline eventually will have a setting
                painter.drawPath(path)

                # Draw the main text in the middle
                painter.setPen(text_color)
                painter.drawText(0, text_y, line)

                

    def init_movie(self):
        if self.icon_path.lower().endswith('.gif'):
            logger.info(f"Loading GIF: {self.icon_path}")
            self.movie = QMovie(self.icon_path)
            if not self.movie.isValid():
                logger.error("Error: GIF failed to load.")
                self.movie = None
                return

            self.movie.frameChanged.connect(self.on_frame_changed)
            self.movie.start()
        else:
            self.movie = None
    
    def on_frame_changed(self, frame):
        if frame != -1:
            self.update() 

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)
        

    def calculate_text_height(self, text):
        font_metrics = QFontMetrics(self.font)
        lines = self.get_multiline_text(font_metrics, text)
        return len(lines) * 15

    def get_multiline_text(self, font, text):
        font_metrics = QFontMetrics(font)
        words = text.split()
        lines = []
        current_line = ""

        max_lines = 3

        for word in words:
            if len(lines) > max_lines:
                break
            # Handle long words that exceed the icon size
            while font_metrics.boundingRect(word).width() > self.icon_size:
                if len(lines) > max_lines:
                    break
                for i in range(1, len(word)):
                    if font_metrics.boundingRect(word[:i]).width() > self.icon_size:
                        # Add the max length that fits to the current line
                        lines.append(word[:i-1])
                        # Continue processing the remaining part of the word
                        word = word[i-1:]
                        break
                else:
                    # This else is part of the for-else construct; it means the word fits entirely
                    break

            # Word fits within line
            new_line = current_line + " " + word if current_line else word
            if font_metrics.boundingRect(new_line).width() <= self.icon_size:
                current_line = new_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)



        # If we exceed the limit, cut it down to 3 lines + "..."
        if len(lines) > max_lines:
            # Cut it to max_lines (total) lines
            lines = lines[:max_lines]

            last_line = lines[max_lines -1]
            # Make sure the last line fits with the "..." within the icon size
            while font_metrics.boundingRect(last_line + "...").width() > self.icon_size:
                last_line = last_line[:-1]  # Remove one character at a time till it fits

            last_line += "..."

            lines = lines[:max_lines -1]  # Keep the lines < max lines
            lines.append(last_line)

        return lines
    
    def show_tooltip(self):
        if self.last_pos:
            QToolTip.showText(
                self.last_pos,
                self.name,
                None
            )
            self.tooltip_shown = True

    def hoverEnterEvent(self, event):
        pos = event.pos()
        if self.hover_in_text_area(pos):
            self.hover_timer.start(1500)
            self.last_pos = event.screenPos()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Stop the timer and hide tooltip when mouse leaves
        self.hover_timer.stop()
        QToolTip.hideText()
        self.tooltip_shown = False
        self.last_pos = None
        super().hoverLeaveEvent(event)

    def hoverMoveEvent(self, event):
        # Hide tooltip and restart timer on mouse movement
        pos = event.pos()
        if self.hover_in_text_area(pos):
            if self.tooltip_shown:
                QToolTip.hideText()
                self.tooltip_shown = False
            
            # Reset the timer
            self.hover_timer.stop()
            self.hover_timer.start(1500)
            self.last_pos = event.screenPos()
        else:
            # If mouse moves out of text area, stop timer and hide tooltip
            self.hover_timer.stop()
            QToolTip.hideText()
            self.tooltip_shown = False
            self.last_pos = None
        super().hoverMoveEvent(event)

    def hover_in_text_area(self, pos):
        if self.text_height == 0:
            return False
        bottom_rect = QRectF(
            0,
            self.boundingRect().height() - self.text_height - self.padding,
            self.boundingRect().width(),
            self.text_height
        )
        return bottom_rect.contains(pos)


    def double_click(self, event):
        logger.info(f"double clicked: icon fields = row: {self.row} col: {self.col} name: {self.name} icon_path: {self.icon_path}, executable path: {self.executable_path} command_args: {self.command_args} website_link: {self.website_link} launch_option: {self.launch_option} icon_size = {self.icon_size}")
        if event.button() == Qt.LeftButton and is_default(self.row, self.col):
            view = self.scene().views()[0]
            view.show_grid_menu(self.row, self.col)
        # if Icon is non-default. Note: This does not mean it has a valid exec_path or website_link.
        # No or invalid exec_path/website_link will either give an error like not found. Or No successful launch detected.
        elif event.button() == Qt.LeftButton:
            self.run_program()
    
    def run_program(self):
        self.show_warning_count = 0
        launch_option_methods = {
            0: self.launch_first_found,
            1: self.launch_prio_web_link,
            2: self.launch_ask_upon_launching,
            3: self.launch_exec_only,
            4: self.launch_web_link_only,
        }

        launch_option = self.launch_option
        method = launch_option_methods.get(launch_option, 0)
        success = method()
        
        if not success and self.show_warning_count == 0:
            logger.error("No successful launch detected")
            display_no_successful_launch_error()
    
    def launch_first_found(self):
        logger.info("launch option = 0")
        return self.run_executable() or self.run_website_link()
    def launch_prio_web_link(self):
        logger.info("launch option = 1")
        return self.run_website_link() or self.run_executable()
    def launch_ask_upon_launching(self):
        logger.info("launch option = 2")
        return self.choose_launch()
    def launch_exec_only(self):
        logger.info("launch option = 3")
        return self.run_executable()
    def launch_web_link_only(self):
        logger.info("launch option = 4")
        return self.run_website_link()

    def run_executable(self):
        #returns running = true if runs program, false otherwise
        running = False

        file_path = self.executable_path
        args = shlex.split(self.command_args)
        command = [file_path] + args

        

        #only bother trying to run file_path if it is not empty
        if file_path == "":
            return running
        
        #ensure path is an actual file that exists, display message if not
        try:
            if os.path.exists(file_path) == False:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.error(f"While attempting to run the executable the file is not found at {self.executable_path}")
            self.show_warning_count += 1
            display_file_not_found_error(self.executable_path)
            return running


        #file path exists and is not ""
        try:
            #if it is a .lnk file it is expected that the .lnk contains the command line arguments
            #upon which running os.startfile(file_path) runs the .lnk the same as just clicking it from a shortcut
            if file_path.lower().endswith('.lnk'):
                running = True
                os.startfile(file_path)
            else:
                try:

                    #when shell=True exceptions like FileNotFoundError are no longer raised but put into stderr
                    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    running = True
                    stdout, stderr = process.communicate(timeout=0.5)
                    

                    text = stderr.decode('utf-8')
                    if "is not recognized as an internal or external command" in text:
                        running = False
                        
                        logger.error(f"Error opening file, Seems like user does not have a default application for this file type and windows is not popping up for them to select a application to open with., path = {self.executable_path}")
                        self.show_warning_count += 1
                        display_no_default_type_error(self.executable_path)
                    
                #kill the connection between this process and the subprocess we just launched.
                #this will not kill the subprocess but just set it free from the connection
                except Exception as e:
                    logger.info("killing connection to new subprocess")
                    process.kill()

        except Exception as e:
            logger.error(f"An error occurred: {e}")
        return running
        
    def run_website_link(self):
        logger.info("run_web_link attempted")
        running = True
        url = self.website_link

        if(url == ""): 
            running = False
            return running
        #append http:// to website to get it to open as a web link
        #for example google.com will not open as a link, but www.google.com, http://google.com, www.google.com all will, even http://google will open in the web browser (it just won't put you at google.com)
        elif not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        os.startfile(url)
        logger.info(f"Run website link running status = {running}")
        return running

    
    def choose_launch(self):
        
        logger.info("Choose_launch called")
        self.run_menu_dialog = RunMenuDialog()
        if self.run_menu_dialog.exec() == QDialog.Accepted:
            result = self.run_menu_dialog.get_result()
            if result == 'run_executable':
                logger.info("Run Executable button was clicked")
                return self.run_executable()

            elif result == 'open_website_link':
                logger.info("Open Website Link button was clicked")
                return self.run_website_link()
        return True
    
    def context_menu(self, event):
        context_menu = QMenu()

        # Edit Icon section
        
        logger.info(
            f"Row: {self.row}, Column: {self.col}, Name: {self.name}, Icon_path: {self.icon_path}, "
            f"Exec Path: {self.executable_path}, Command args: {self.command_args}, Website Link: {self.website_link}, "
            f"Launch option: {self.launch_option}, Use Default Font Size: {self.use_global_font_size}, "
            f"Font Size: {self.font_size}, Use Default Font color: {self.use_global_font_color}, font_color {self.font_color}"
        )

        
        edit_action = QAction('Edit Icon', context_menu)
        edit_action.triggered.connect(self.edit_triggered)
        context_menu.addAction(edit_action)

        context_menu.addSeparator()

        #Launch Options submenu section
        launch_options_sm = QMenu("Launch Options", context_menu)
    
        action_names = [
            "Launch first found",
            "Prioritize Website links",
            "Ask upon launching",
            "Executable only",
            "Website Link only"
        ]
    
        for i, name in enumerate(action_names, start=0):
            action = QAction(name, context_menu)
            action.triggered.connect(lambda checked, pos=i: self.update_launch_option(pos))
            action.setCheckable(True)
            action.setChecked(i ==  self.launch_option)
            launch_options_sm.addAction(action)

        context_menu.addMenu(launch_options_sm)

        context_menu.addSeparator()

        # Launch executable or website section
        executable_action = QAction('Run Executable', context_menu)
        executable_action.triggered.connect(self.run_executable)
        context_menu.addAction(executable_action)

        website_link_action = QAction('Open Website in browser', context_menu)
        website_link_action.triggered.connect(self.run_website_link)
        context_menu.addAction(website_link_action)

        context_menu.addSeparator()

        #Open Icon and Executable section
        icon_path_action = QAction('Open Icon location', context_menu)
        icon_path_action.triggered.connect(lambda: self.open_path(self.icon_path))
        context_menu.addAction(icon_path_action)

        exec_path_action = QAction('Open Executable location', context_menu)
        exec_path_action.triggered.connect(lambda: self.open_path(self.executable_path))
        context_menu.addAction(exec_path_action)

        context_menu.addSeparator()

        delte_action = QAction('Delete Icon', context_menu)
        delte_action.triggered.connect(self.delete_triggered)
        context_menu.addAction(delte_action)

        context_menu.aboutToHide.connect(self.context_menu_closed)
        context_menu.exec(event.globalPos())


    def context_menu_closed(self):
        logger.debug("Context menu closed")

    def edit_triggered(self):
        view = self.scene().views()[0]
        view.show_grid_menu(self.row, self.col)

    def update_launch_option(self, pos):
        change_launch(pos, self.row, self.col)
        self.reload_from_config()

    def open_path(self, path):
        normalized_path = os.path.normpath(path)
        
        # Check if the file exists
        if os.path.exists(normalized_path):
            # Open the folder and highlight the file in Explorer
            subprocess.run(['explorer', '/select,', normalized_path])
        else:
            # Get the parent directory
            parent_directory = os.path.dirname(normalized_path)
            
            # Check if the parent directory exists
            if os.path.exists(parent_directory):
                # Open the parent directory in Explorer
                subprocess.run(['explorer', parent_directory])
            else:
                # Show error if neither the file nor the parent directory exists
                logger.warning(f"Tried to open file directory but path: {normalized_path} does not exist nor its parent: {parent_directory} exist")
                display_path_and_parent_not_exist_warning(normalized_path)

    def delete_triggered(self):
        logger.info(f"User attempted to delete {self.name}, at {self.row}, {self.col}")
        # Show delete confirmation warning, if Ok -> delete icon. if Cancel -> do nothing.
        if display_delete_icon_warning(self.name, self.row, self.col) == QMessageBox.Yes:   
            logger.info(f"User confirmed deletion for {self.name}, at {self.row}, {self.col}")
            set_entry_to_default(self.row, self.col)
            self.delete_folder_items()

            # Delete icon and references from QGraphicsView (To stop it from repainting on hover.)
            views = self.scene().views()
            if views:
                view = views[0]
                view.delete_icon(self.row, self.col)

        
    
    def delete_folder_items(self):
        # Check if the directory exists
        data_directory = get_data_directory()
        folder_path = os.path.join(data_directory, f'[{self.row}, {self.col}]')
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Loop through all the items in the directory
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                logger.info(f"Deleting ITEM = {item_path}")
                send2trash.send2trash(item_path)
        else:
            logger.warning(f"{folder_path} does not exist or is not a directory.")


    def get_view_size(self):
        # Get the list of views from the scene
        views = self.scene().views()
        
        if views:
            # Assume there's only one view and get the first one
            view = views[0]

            # Get the size of the QGraphicsView
            view_size = view.size()
            view_width = view_size.width()
            view_height = view_size.height()

            return view_width, view_height

        return None  # If there are no views

    def update_icon_path(self, icon_path):
        if self.icon_path != icon_path:
            self.icon_path = icon_path
            self.init_movie()
        if not self.movie:
            self.load_pixmap(reset_cache=True)
        self.update()

    # Override mousePressEvent
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.distance = 0
            self.dragging = True
            self.start_pos = event.pos()  # Store the initial position
            event.accept()

    # Override mouseMoveEvent (to track dragging without moving)
    def mouseMoveEvent(self, event):
        if self.dragging:
            # Calculate the distance moved, but don't move the item
            self.distance = (event.pos() - self.start_pos).manhattanLength()
            if self.distance > 5:  # A threshold to consider as dragging
                self.setCursor(Qt.ClosedHandCursor) 


    def mouseReleaseEvent(self, event):
        views = self.scene().views()
        self.dragging = False
        self.setCursor(Qt.ArrowCursor) 

        if event.button() == Qt.RightButton:
            # If right-click, do not perform any action related to swapping
            return
        
        if is_default(self.row, self.col):
            return
        
        if views:
            # Assume there's only one view and get the first one
            view = views[0]

            old_row = self.row
            old_col = self.col

            # Get the mouse release position in the scene
            mouse_pos = event.pos()  # This gives you the position relative to the item
            
            # Convert the mouse position from item coordinates to scene coordinates
            scene_pos = self.mapToScene(mouse_pos)

            # Call icon_dropped with the scene position
            new_row, new_col = view.icon_dropped(scene_pos)
            logger.info(f"old_row: {old_row} old_col: {old_col} row: {new_row}, col: {new_col} (released at {scene_pos.x()}, {scene_pos.y()})")
            # Swap icons
            if new_row == None or new_col== None:
                logger.error("Icon dropped outside of visible icon range or bad return from icon_dropped.")
            elif old_row != new_row or old_col != new_col:
                logger.info("Swapping icons.")
                view.swap_icons(old_row, old_col, new_row, new_col)
            elif self.distance > 5:
                logger.info("Icon dropped at same location")
            
            
            self.update()

    def drop_event(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()  # Get the list of dropped files (as URLs)
            if urls:
                file_path = urls[0].toLocalFile()  # Convert the first URL to a local file path
                self.handle_file_drop(file_path)
                event.acceptProposedAction()

    def handle_file_drop(self, file_path):
        logger.info(f"Item {file_path} dropped to existing icon: {self.name} at: {self.row},{self.col}")
        view = self.scene().views()[0]
        view.show_grid_menu(self.row, self.col, file_path)

