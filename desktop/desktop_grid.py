from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QApplication, QDialog, QMenu
from PySide6.QtCore import Qt, QSize, QRectF, QTimer, QMetaObject, QUrl, QPoint, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPixmap, QBrush, QPainterPath, QPen, QAction
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from util.settings import get_setting
from util.config import get_item_data, create_paths, is_default, get_data_directory, swap_items_by_position
from desktop.desktop_grid_menu import Menu
from menus.run_menu_dialog import RunMenuDialog
from menus.display_warning import display_no_successful_launch_error, display_file_not_found_error, display_no_default_type_error
from desktop.desktop_grid_menu import Menu
import sys
import os
import logging
import shlex
import subprocess

logger = logging.getLogger(__name__)


# Global Padding Variables
TOP_PADDING = 20  # Padding from the top of the window
SIDE_PADDING = 20  # Padding from the left side of the window
VERTICAL_PADDING = 50  # Padding between icons
HORIZONTAL_PADDING = 10

MEDIA_PLAYER = None
AUTOGEN_ICON_SIZE = 256

BACKGROUND_VIDEO = ""
BACKGROUND_IMAGE = ""


# Desktop Icon variables
ICON_SIZE = 128  # Overrided by settings
FONT_SIZE = 10
FONT = "Arial"

class DesktopGrid(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Desktop Grid Prototype')
        self.setMinimumSize(400, 400)

        # Build paths for config and data directories (stored in config.py)
        create_paths()

        global ICON_SIZE
        ICON_SIZE = get_setting("icon_size", 100)

        self.prev_max_visible_columns = 0
        self.prev_max_visible_rows = 0

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Disable scroll bars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setDragMode(QGraphicsView.NoDrag)




        # Initialize 2D array for icon items
        self.desktop_icons = []

        

        # Initialize a timer for debouncing update_icon_visibility
        self.resize_timer = QTimer()
        self.resize_timer.setInterval(200)  # Adjust the interval to your preference (in ms)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_icon_visibility)

        # Example of calling a function for a DesktopIcon
        # self.desktop_icons[3][1].set_color("black") function removed but calling remains the same syntax

        # Set the scene rectangle to be aligned with the top-left corner with padding
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        self.scene.clear()
        self.populate_icons()

        # Video background stuff
        global MEDIA_PLAYER
        self.load_video, self.load_image = self.background_setting()
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        MEDIA_PLAYER = QMediaPlayer()
        MEDIA_PLAYER.setVideoOutput(self.video_item)
        MEDIA_PLAYER.mediaStatusChanged.connect(self.handle_media_status_changed)

        # Only run _fresh_ for launch to init all visibilities.
        self.update_fresh_icon_visiblity()
        self.render_bg()

    def populate_icons(self):
        icon_size = ICON_SIZE
        self.cols = 40
        self.rows = 10

        # Create a 2D array for icon items
        self.desktop_icons = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        for row in range(self.rows):
            for col in range(self.cols):
                data = get_item_data(row, col)
                icon_item = DesktopIcon(
                    row, 
                    col, 
                    data['name'], 
                    data['icon_path'], 
                    data['executable_path'], 
                    data['command_args'], 
                    data['website_link'], 
                    data['launch_option'],
                    icon_size)
                # setPos uses [column, row] equivalent so flip it. i.e. SIDEPADDING + y(column) = column position.
                icon_item.setPos(SIDE_PADDING + col * (icon_size + HORIZONTAL_PADDING), 
                    TOP_PADDING + row * (icon_size + VERTICAL_PADDING))
                self.desktop_icons[row][col] = icon_item
                self.scene.addItem(icon_item)

        # Initially update visibility based on the current window size
        self.update_icon_visibility()



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scene.setSceneRect(self.rect())
        self.video_item.setSize(self.size())
        self.render_bg()

        # Prioritizes resizing window then redraws. i.e. slightly smoother dragging to size then slightly delayed redraw updates.
        self.resize_timer.start() 

        # Prioritizes drawing over resizing. i.e. always draw and always resize at the same time, thus resize can lag a bit more behind but desktop will always look to be the same.
        #self.scene.setSceneRect(0, 0, self.width(), self.height())
        #self.update_icon_visibility()

    def update_icon_visibility(self):
        self.scene.setSceneRect(0, 0, self.width(), self.height())
        # Get the size of the visible area of the window
        view_width = self.viewport().width()
        view_height = self.viewport().height()

        # Calculate current max visible row and column based on icon size and padding
        # min() ensures max_visible_rows/columns cannot exceed the self.rows/self.cols values.
        max_visible_rows = min((view_height - TOP_PADDING) // (self.desktop_icons[0][0].icon_size + VERTICAL_PADDING), self.rows)
        max_visible_columns = min((view_width - SIDE_PADDING) // (self.desktop_icons[0][0].icon_size + HORIZONTAL_PADDING), self.cols)
        print(f"max columns: {max_visible_columns}, max rows: {max_visible_rows}")


        # If nothing has changed, no need to proceed
        if max_visible_columns == self.prev_max_visible_columns and max_visible_rows == self.prev_max_visible_rows:
            return
        
        # Add rows as visible
        if max_visible_rows > self.prev_max_visible_rows:
            for x in range(self.prev_max_visible_rows, max_visible_rows):
                for y in range(min(max_visible_columns, self.cols)):
                    if x < self.rows and y < self.cols:  
                        self.desktop_icons[x][y].setVisible(True)

        # Add columns as visible
        if max_visible_columns > self.prev_max_visible_columns:
            for y in range(self.prev_max_visible_columns, max_visible_columns):
                for x in range(min(max_visible_rows, self.rows)):
                    if x < self.rows and y < self.cols:  
                        self.desktop_icons[x][y].setVisible(True)

        # Remove Rows as visible
        if max_visible_rows < self.prev_max_visible_rows:
            for y in range(self.prev_max_visible_columns +1):
                for x in range(max(max_visible_rows, 0), self.prev_max_visible_rows +1):
                    if x < self.rows and y < self.cols:  
                        self.desktop_icons[x][y].setVisible(False)
        
        # Remove Columns as visbile
        if max_visible_columns < self.prev_max_visible_columns:
            for x in range(self.prev_max_visible_rows +1):
                for y in range(max(max_visible_columns, 0), self.prev_max_visible_columns +1):
                    if x < self.rows and y < self.cols:  
                        self.desktop_icons[x][y].setVisible(False)
        
        

        self.prev_max_visible_columns = max_visible_columns
        self.prev_max_visible_rows = max_visible_rows

    # Iterates through every self.desktop_icons and sets visiblity (more costly than self.update_icon_visibility)
    # Generally only use this on launching the program to set the defaults and then update them from there normally.
    def update_fresh_icon_visiblity(self):
        view_width = self.viewport().width()
        view_height = self.viewport().height()

        max_visible_columns = (view_width - SIDE_PADDING) // (self.desktop_icons[0][0].icon_size + HORIZONTAL_PADDING)
        max_visible_rows = (view_height - TOP_PADDING) // (self.desktop_icons[0][0].icon_size + VERTICAL_PADDING)
        for x in range(self.rows):
            for y in range(self.cols):
                if x < max_visible_rows and y < max_visible_columns:
                    self.desktop_icons[x][y].setVisible(True)
                else:
                    self.desktop_icons[x][y].setVisible(False)

    # Override to do nothing to avoid scrolling
    def wheelEvent(self, event):

        #temporary override to test resizing icons.
        global ICON_SIZE
        if ICON_SIZE == 64:
            ICON_SIZE = 128
            self.update_icon_size(128)
        else:
            ICON_SIZE = 64
            self.update_icon_size(64)
        event.ignore()  # Ignore the event to prevent scrolling




    def update_icon_size(self, size):
        # Update the size of each icon and adjust their position
        global ICON_SIZE
        ICON_SIZE = size
        for x in range(self.rows):
            for y in range(self.cols):
                self.desktop_icons[x][y].update_size(size)
                self.desktop_icons[x][y].setPos(SIDE_PADDING + y * (size + HORIZONTAL_PADDING), 
                                TOP_PADDING + x * (size + VERTICAL_PADDING))

        # Update the scene rectangle and visibility after resizing icons
        self.update_icon_visibility()


    # Debug function to find furthest visible row, col (not point but furthest row with a visible object and furthest column with a visible object)
    def find_largest_visible_index(self):
        largest_visible_row = -1
        largest_visible_column = -1

        # Find the largest visible row
        for row in range(self.rows):
            for column in range(self.cols):
                if self.desktop_icons[row][column].isVisible():
                    largest_visible_row = max(largest_visible_row, row)

        # Find the largest visible column
        for column in range(self.cols):
            for row in range(self.rows):
                if self.desktop_icons[row][column].isVisible():
                    largest_visible_column = max(largest_visible_column, column)

        return largest_visible_row, largest_visible_column
    
    def pause_video(self):
        QMetaObject.invokeMethod(MEDIA_PLAYER, "pause", Qt.QueuedConnection)
    def play_video(self):
        QMetaObject.invokeMethod(MEDIA_PLAYER, "play", Qt.QueuedConnection)

    def background_setting(self):
        bg_setting = get_setting("background_source")
        exists_video = os.path.exists(BACKGROUND_VIDEO)
        exists_image = os.path.exists(BACKGROUND_IMAGE)
        if bg_setting == "first_found":
            if exists_video:
                return True, False
            elif exists_image:
                return False, True
            return False, False
        elif bg_setting == "both":
            return exists_video, exists_image
        elif bg_setting == "video_only":
            return exists_video, False
        elif bg_setting == "image_only":
            return False, exists_image

        return False, False
    
    def render_bg(self):
        # Store old version to tell if it has changed after loading new video.
        old_bg_video = BACKGROUND_VIDEO
        self.load_bg_from_settings()
        self.load_video, self.load_image = self.background_setting()
        if self.load_video:
            if old_bg_video != BACKGROUND_VIDEO:
                self.set_video_source(BACKGROUND_VIDEO)
            self.scene.setBackgroundBrush(QBrush())
        else:
            MEDIA_PLAYER.stop()  # Stop the playback
            MEDIA_PLAYER.setSource(QUrl())  # Clear the media source

        if self.load_image:
            background_pixmap = QPixmap(BACKGROUND_IMAGE)
            self.scene.setBackgroundBrush(QBrush(background_pixmap.scaled(self.size(),
                                                    Qt.KeepAspectRatioByExpanding, 
                                                    Qt.SmoothTransformation)))
        elif not self.load_image:
            # Access the secondary color from the parent class, with a default fallback
            secondary_color = getattr(self.parent(), 'secondary_color', '#202020')

            # Set the background color based on the secondary color
            if secondary_color == '#4c5559':
                color = QColor(secondary_color)
            elif secondary_color == '#202020':
                color = QColor(secondary_color)
            else:
                # Light mode: lighten the primary light color
                bright_color = QColor(self.parent().primary_light_color)
                lighter_color = bright_color.lighter(120)  # Lighten the color by 20%
                color = QColor(lighter_color)

            # Set the background color as a solid brush
            self.scene.setBackgroundBrush(QBrush(color))
        
    def load_bg_from_settings(self):
        global BACKGROUND_VIDEO, BACKGROUND_IMAGE
        BACKGROUND_VIDEO = get_setting("background_video")
        BACKGROUND_IMAGE = get_setting("background_image")
    
    def set_bg(self, background_video, background_image):
        global BACKGROUND_VIDEO, BACKGROUND_IMAGE
        BACKGROUND_VIDEO = background_video
        BACKGROUND_IMAGE = background_image
        self.render_bg()

    def set_video_source(self, video_path):
        MEDIA_PLAYER.setSource(QUrl.fromLocalFile(video_path))
        MEDIA_PLAYER.setPlaybackRate(1.0)
        MEDIA_PLAYER.play()
    
    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            MEDIA_PLAYER.setPosition(0)
            MEDIA_PLAYER.play()


    def show_grid_menu(self, row, col):
        menu = Menu(None, row, col, parent=self)
        main_window_size = self.parent().size()
        main_window_height = main_window_size.height()
        dialog_width = main_window_size.width() / 3
        dialog_height = main_window_size.height() / 2

        # Get the desktop icon's screen position (relative to QGraphicsView)
        icon_pos = self.get_icon_position(row, col)
        
        # Convert the icon's position to global screen coordinates
        global_icon_pos = self.mapToGlobal(icon_pos)

        # Available space around the icon (based on global screen coordinates)
        screen_geometry = self.parent().screen().geometry()
        space_left = global_icon_pos.x()
        space_right = screen_geometry.width() - global_icon_pos.x() - ICON_SIZE - HORIZONTAL_PADDING

        # If menu would extend below, adjust y to fit within main window
        if global_icon_pos.y() + dialog_height > main_window_height:  
            adjusted_y = main_window_height - dialog_height
        else:
            adjusted_y = global_icon_pos.y()

        # Compare available space and decide menu placement based on the side with more room
        if space_right >= space_left and space_right >= dialog_width:
            logger.info("Menu right")
            menu.move(global_icon_pos.x() + (ICON_SIZE + HORIZONTAL_PADDING), adjusted_y)
        elif space_left >= dialog_width:
            logger.info("Menu left")
            menu.move(global_icon_pos.x() - dialog_width, adjusted_y)
        else:
            logger.info("Menu center")
            menu.move(
                (screen_geometry.width() - dialog_width) / 2,
                (screen_geometry.height() - dialog_height) / 2,
            )

        menu.resize(dialog_width, dialog_height)
        menu.exec()

    def get_icon_position(self, row, col):
        # Calculate the position of the icon based on row and col
        x_pos = SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING)
        y_pos = TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING)
        
        # Return the position as a QPoint
        return QPoint(x_pos, y_pos)



    # returns base DATA_DIRECTORY/[row, col]
    def get_data_icon_dir(self, row, col):
        data_directory = get_data_directory()
        data_path = os.path.join(data_directory, f'[{row}, {col}]')
        #make file if no file (new)
        if not os.path.exists(data_path):
            logger.info(f"Making directory at {data_path}")
            os.makedirs(data_path)
        logger.info(f"get_data_icon_dir: {data_path}")
        return data_path
    
    def get_autogen_icon_size(self):
        return AUTOGEN_ICON_SIZE
    
    def set_icon_path(self, row, col, new_icon_path):
        self.desktop_icons[row][col].update_icon_path(new_icon_path)

    def edit_mode_icon(self, row, col):
        self.desktop_icons[row][col].edit_mode_icon()

    def normal_mode_icon(self, row, col):
        self.desktop_icons[row][col].normal_mode_icon()

    def icon_dropped(self, pos):
        # Calculate the column based on the X position of the mouse
        col = (pos.x() - SIDE_PADDING) // (ICON_SIZE + HORIZONTAL_PADDING)

        # Calculate the row based on the Y position of the mouse
        row = (pos.y() - TOP_PADDING) // (ICON_SIZE + VERTICAL_PADDING)

        # Ensure the calculated row and column are within valid ranges
        if 0 <= row < self.prev_max_visible_rows and 0 <= col < self.prev_max_visible_columns:
            return int(row), int(col)

        # If out of bounds, return None
        return None, None

    
    def swap_icons(self, old_row, old_col, new_row, new_col):
        # Get the items to swap
        item1 = self.desktop_icons[old_row][old_col]
        item2 = self.desktop_icons[new_row][new_col]
        
        if item1 is None or item2 is None:
            # Handle cases where one of the items does not exist
            print("One of the items does not exist.")
            return

        # Calculate new positions
        icon_size = ICON_SIZE
        item1_new_pos = (SIDE_PADDING + new_col * (icon_size + HORIZONTAL_PADDING),
                        TOP_PADDING + new_row * (icon_size + VERTICAL_PADDING))
        item2_new_pos = (SIDE_PADDING + old_col * (icon_size + HORIZONTAL_PADDING),
                        TOP_PADDING + old_row * (icon_size + VERTICAL_PADDING))
        
        # Swap positions
        item1.setPos(*item1_new_pos)
        item2.setPos(*item2_new_pos)

        item1.row = new_row
        item1.col = new_col
        item2.row = old_row
        item2.col = old_col

        # Update the desktop_icons array to reflect the swap
        self.desktop_icons[old_row][old_col], self.desktop_icons[new_row][new_col] = (
            self.desktop_icons[new_row][new_col],
            self.desktop_icons[old_row][old_col]
        )

        swap_items_by_position(old_row, old_col, new_row, new_col)

        print(f"Swapped items at ({old_row}, {old_col}) with ({new_row}, {new_col})")


    #### Delete these Temporarily included just to allow changing icons sizes by setting.

    # Change this call from settings_menu.py when fully swapping new_grid and desktop_grid
    def update_label_size(self,size):
        self.update_icon_size(size)

    


class DesktopIcon(QGraphicsItem):
    def __init__(self, row, col, name, icon_path, executable_path, command_args, website_link, launch_option, icon_size=64, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.name = name
        self.icon_path = icon_path
        self.executable_path = executable_path
        self.command_args = command_args
        self.website_link = website_link
        self.launch_option = launch_option

        #self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

        self.icon_text = self.name
        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.padding = 30
        self.font = QFont(FONT, FONT_SIZE)

        self.border_width = 5
        self.border_color = QColor(Qt.red)

        self.edit_mode = False



    def update_size(self, new_size):
        self.icon_size = new_size
        self.prepareGeometryChange()

    def boundingRect(self) -> QRectF:
        text_height = self.calculate_text_height(self.icon_text)
        return QRectF(0, 0, self.icon_size, self.icon_size + text_height + self.padding)
    
    def edit_mode_icon(self):
        self.edit_mode = True
        self.update() 
    
    def normal_mode_icon(self):
        self.edit_mode = False
        self.update() 

    def paint(self, painter: QPainter, option, widget=None):
        if self.edit_mode:
            pen = QPen(self.border_color, self.border_width)
            painter.setPen(pen)
            rect = self.boundingRect()
            # Draw the border inside the square, adjusted for the border width
            adjusted_rect = rect.adjusted(self.border_width / 2, 
                                          self.border_width / 2, 
                                          -self.border_width / 2, 
                                          -self.border_width / 2)
            painter.drawRect(adjusted_rect)

        if not is_default(self.row, self.col):
            if not os.path.exists(self.icon_path) or self.icon_path == "" or self.icon_path == "unknown.png":
                painter.drawPixmap(0, 0, self.icon_size, self.icon_size, QPixmap("assets/images/unknown.png"))
            else:
                painter.drawPixmap(2, 2, self.icon_size-4, self.icon_size-2, QPixmap(self.icon_path))

            painter.setFont(self.font)

            lines = self.get_multiline_text(self.font, self.icon_text)

            # Define the outline color and main text color
            outline_color = QColor(0, 0, 0)  # Black outline Eventually will have a setting
            text_color = QColor(get_setting("label_color", "white"))  # Text label Color setting 

            for i, line in enumerate(lines):
                text_y = self.icon_size + self.padding / 2 + i * 15

                # Create a QPainterPath for the text outline
                path = QPainterPath()
                path.addText(0, text_y, self.font, line)

                # Draw the text outline with a thicker pen
                painter.setPen(QColor(outline_color))
                painter.setPen(QColor(outline_color))
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(outline_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)) # 4 = pixels of outline eventually will have a setting
                painter.drawPath(path)

                # Draw the main text in the middle
                painter.setPen(text_color)
                painter.drawText(0, text_y, line)
        # DesktopIcon is default (no fields set)
        else:
            if self.hovered:
                painter.drawPixmap(0, 0, self.icon_size, self.icon_size, QPixmap("assets/images/add.png"))
            else:
                # paint nothing
                pass
                

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
    
    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def mouseDoubleClickEvent(self, event):
        print(f"double clicked: icon fields = row: {self.row} col: {self.col} name: {self.name} icon_path: {self.icon_path}, executable path: {self.executable_path} command_args: {self.command_args} website_link: {self.website_link} launch_option: {self.launch_option} icon_size = {self.icon_size}")
        if event.button() == Qt.LeftButton and is_default(self.row, self.col):
            MEDIA_PLAYER.pause()
            #menu = Menu(None, parent=self)
            view = self.scene().views()[0]
            view.show_grid_menu(self.row, self.col)
            #menu.resize(dialog_width, dialog_height)
            
            #menu.exec()
            MEDIA_PLAYER.play()
        #if icon has an executable_path already (icon exists with path)
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
    
    def contextMenuEvent(self, event):
        global CONTEXT_OPEN
        CONTEXT_OPEN = True
        context_menu = QMenu()

        self.edit_mode_icon()

        # Edit Icon section
        
        logger.info(f"Row: {self.row}, Column: {self.col}, Name: {self.name}, Icon_path: {self.icon_path}, Exec Path: {self.executable_path}, Command args: {self.command_args}, Website Link: {self.website_link}, Launch option: {self.launch_option}")
        
        edit_action = QAction('Edit Icon', context_menu)
        edit_action.triggered.connect(self.edit_triggered)
        context_menu.addAction(edit_action)

        context_menu.aboutToHide.connect(self.context_menu_closed)
        context_menu.exec(event.screenPos())

    def context_menu_closed(self):
        logger.debug("Context menu closed")
        self.normal_mode_icon()
        #self.timer_right_click.timeout.connect(self.context_close)
        #self.timer_right_click.start(100) 

    def edit_triggered(self):
        MEDIA_PLAYER.pause()
        # Before this I need to set it into edit mode.
        view = self.scene().views()[0]
        view.show_grid_menu(self.row, self.col)
        #menu = Menu(None, self.row, self.col, parent=None)
        #main_window_width, main_window_height = self.get_view_size()
        #dialog_width = main_window_width / 2
        #dialog_height = main_window_height / 2
        #menu.resize(dialog_width, dialog_height)
        #menu.exec()
        # After this it should go back to normal mode.
        MEDIA_PLAYER.play()


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
        self.icon_path = icon_path
        self.update()

    # Override mousePressEvent
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.pos()  # Store the initial position
            event.accept()

    # Override mouseMoveEvent (to track dragging without moving)
    def mouseMoveEvent(self, event):
        if self.dragging:
            # Calculate the distance moved, but don't move the item
            distance = (event.pos() - self.start_pos).manhattanLength()
            if distance > 5:  # A threshold to consider as dragging
                # Optionally, you can change the cursor to indicate dragging
                self.setCursor(Qt.ClosedHandCursor)  # Example: Change cursor appearance


    def mouseReleaseEvent(self, event):
        views = self.scene().views()
        self.dragging = False

        if event.button() == Qt.RightButton:
            # If right-click, do not perform any action related to swapping
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
            self.row, self.col = view.icon_dropped(scene_pos)
            print(f"old_row: {old_row} old_col: {old_col} row: {self.row}, col: {self.col} (released at {scene_pos.x()}, {scene_pos.y()})")
            # Swap icons
            if self.row == None or self.col == None:
                self.row = old_row
                self.col = old_col
                logger.error("Icon dropped outside of visible icon range or bad return from icon_dropped, resetting self.row/self.col to old_row/old_col")
            elif old_row != self.row or old_col != self.col:
                logger.info("Swapping icons.")
                view.swap_icons(old_row, old_col, self.row, self.col)
            else:
                logger.info("Icon dropped at same location")
            
            
            self.update()





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DesktopGrid()
    window.show()
    sys.exit(app.exec())
