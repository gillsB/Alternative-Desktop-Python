from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QApplication, QDialog, QMenu, QMessageBox, QToolTip, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QSize, QRectF, QTimer, QMetaObject, QUrl, QPoint, QSizeF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPixmap, QBrush, QPainterPath, QPen, QAction, QMovie, QCursor, QPixmapCache, QTransform
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from util.settings import get_setting
from util.config import get_item_data, create_paths, is_default, get_data_directory, swap_items_by_position, update_folder, change_launch, set_entry_to_default
from desktop.desktop_grid_menu import Menu
from menus.run_menu_dialog import RunMenuDialog
from menus.display_warning import (display_no_successful_launch_error, display_file_not_found_error, display_no_default_type_error, display_failed_cleanup_warning, 
                                   display_path_and_parent_not_exist_warning, display_delete_icon_warning, display_cannot_swap_icons_warning)
from desktop.desktop_grid_menu import Menu
import sys
import os
import logging
import shlex
import subprocess
import send2trash
import time

logger = logging.getLogger(__name__)


# Global Padding Variables
TOP_PADDING = 20  # Padding from the top of the window
SIDE_PADDING = 20  # Padding from the left side of the window
VERTICAL_PADDING = 50  # Padding between image icons (space for icon Names)
HORIZONTAL_PADDING = 10 

MAX_ROWS = 10
MAX_COLS = 40

MEDIA_PLAYER = None
AUTOGEN_ICON_SIZE = 256

BACKGROUND_VIDEO = ""
BACKGROUND_IMAGE = ""


# Desktop Icon variables
ICON_SIZE = 128  # Overrided by settings
FONT_SIZE = 10
FONT = "Arial"

# edit_mode_icon variables
BORDER_WIDTH = 5
BORDER_COLOR = QColor(Qt.red)

class DesktopGrid(QGraphicsView):
    def __init__(self, args=None):
        super().__init__()
        self.setWindowTitle('Desktop Grid Prototype')
        self.setMinimumSize(400, 400)
        self.setAcceptDrops(True)

        self.args = args

        # Build paths for config and data directories (stored in config.py)
        create_paths()

        global ICON_SIZE, MAX_ROWS, MAX_COLS
        ICON_SIZE = get_setting("icon_size", 100)
        MAX_ROWS = get_setting("max_rows")
        MAX_COLS = get_setting("max_cols")

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Disable scroll bars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setDragMode(QGraphicsView.NoDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform) 


        # Initialize a timer for debouncing update_icon_visibility
        self.resize_timer = QTimer()
        self.resize_timer.setInterval(200)  # Adjust the interval to your preference (in ms)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_icon_visibility)

        # Set the scene rectangle to be aligned with the top-left corner with padding
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        self.scene.clear()
        self.load_bg_from_settings()
        self.load_video, self.load_image = self.background_setting()
        self.video_manager = VideoBackgroundManager(args)  # Create an instance of VideoBackgroundManager
        self.video_manager.video_item = QGraphicsVideoItem()  # Initialize the QGraphicsVideoItem
        self.scene.addItem(self.video_manager.video_item)  # Add video item to the scene
        self.video_manager.video_item.setZValue(-1)  # Set the Z value for rendering order
        logger.info(f"self.load_video = {self.load_video}, self.load_image = {self.load_image}")
        
        # Set up the media player in the video manager
        global MEDIA_PLAYER
        MEDIA_PLAYER = QMediaPlayer()
        MEDIA_PLAYER.setVideoOutput(self.video_manager.video_item)  # Set the video output
        MEDIA_PLAYER.setPlaybackRate(1.0)
        MEDIA_PLAYER.mediaStatusChanged.connect(self.video_manager.handle_media_status_changed)

        
        self.render_bg()
        self.populate_icons()



    def populate_icons(self):

        self.desktop_icons = {}

        for row in range(MAX_ROWS):
            for col in range(MAX_COLS):
                # Don't add empty icons
                if not is_default(row, col):
                    self.add_icon(row, col)


        # Attach a logger which logs every 100 times the first icon in self.desktop_icons is repainted (For detecting infinite paint loops)
        if self.desktop_icons:
            first_icon_key = next(iter(self.desktop_icons))
            first_icon = self.desktop_icons[first_icon_key]
            logger.info(f"Setting {first_icon_key} to log repaints")
            first_icon.log_paints = True

        # Initially update visibility based on the current window size
        self.update_icon_visibility()



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scene.setSceneRect(self.rect())
        self.video_manager.video_item.setSize(self.size())
        self.render_bg()

        # Prioritizes resizing window then redraws. i.e. slightly smoother dragging to size then slightly delayed redraw updates.
        self.resize_timer.start() 

        # Prioritizes drawing over resizing. i.e. always draw and always resize at the same time, thus resize can lag a bit more behind but desktop will always look to be the same.
        #self.scene.setSceneRect(0, 0, self.width(), self.height())
        #self.update_icon_visibility()


    # Iterates through every self.desktop_icons and sets visiblity
    def update_icon_visibility(self):
        view_width = self.viewport().width()
        view_height = self.viewport().height()

        self.max_visible_rows = min((view_height - TOP_PADDING) // (ICON_SIZE + VERTICAL_PADDING), MAX_ROWS)
        self.max_visible_columns = min((view_width - SIDE_PADDING) // (ICON_SIZE + HORIZONTAL_PADDING), MAX_COLS)

        for (row, col), icon in self.desktop_icons.items():
            if row < self.max_visible_rows and col < self.max_visible_columns:
                icon.setVisible(True)
            else:
                icon.setVisible(False)

    # Override to do nothing to avoid scrolling
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # Use .y() for vertical scrolling

        if delta > 0:
            #self.vertical_bg -= 0.05
            #self.zoom_bg -= 0.05
            self.video_manager.move_video(-1000,100)
            #self.video_manager.move_video(1, 0)
            pass
        elif delta < 0:
            #self.vertical_bg += 0.05
            self.video_manager.zoom_video(1.05)
            #self.scale_to_fit_width()
        if self.args.mode == "debug" or self.args.mode == "devbug":
            """
            row, col = self.find_largest_visible_index()
            logger.debug(f"Max row = {row} max col = {col}")
            #temporary override to test resizing icons.
            global ICON_SIZE
            global FONT_SIZE
            if ICON_SIZE == 64:
                ICON_SIZE = 128
                self.update_icon_size(128)
                FONT_SIZE = 18
                self.desktop_icons[(0,0)].update_font()
                # ERROR on purpose to test logging exceptions/traceback.
                print(f"{self.desktop_icons[(0,0)].names}")
            else:
                ICON_SIZE = 64
                self.update_icon_size(64)
                FONT_SIZE = 10
                self.desktop_icons[(0,0)].update_font()
                # ERROR on purpose to test logging exceptions/traceback.
                x = 1/0
            event.ignore()  # Ignore the event to prevent scrolling"""




    def update_icon_size(self, size):
        # Update the size of each icon and adjust their position
        global ICON_SIZE
        ICON_SIZE = size
        for (row, col), icon in self.desktop_icons.items():
            if icon is None:
                continue

            icon.update_size(size)
            icon.setPos(SIDE_PADDING + col * (size + HORIZONTAL_PADDING), 
                        TOP_PADDING + row * (size + VERTICAL_PADDING))
            icon.load_pixmap()

        # Update the scene rectangle and visibility after resizing icons
        self.update_icon_visibility()


    # Debug function to find furthest visible row, col (not point but furthest row with a visible object and furthest column with a visible object)
    def find_largest_visible_index(self):
        largest_visible_row = -1
        largest_visible_column = -1

        # Iterate through the dictionary to find the largest visible row and column
        for (row, col), icon in self.desktop_icons.items():
            if icon.isVisible():
                # Update largest visible row
                largest_visible_row = max(largest_visible_row, row)
                # Update largest visible column
                largest_visible_column = max(largest_visible_column, col)

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
        old_bg_video = BACKGROUND_VIDEO
        self.load_bg_from_settings()  # Load background settings through the manager
        self.load_video, self.load_image = self.background_setting()
        
        if self.load_video:
            if old_bg_video != BACKGROUND_VIDEO or MEDIA_PLAYER.mediaStatus() == QMediaPlayer.NoMedia:
                self.video_manager.set_video_source(BACKGROUND_VIDEO)  # Set video source through the manager
                logger.info("Set background video source")
            scaling_mode = get_setting("video_scaling_mode", "fit_width")  # Fetch the user-selected scaling mode
        
            if scaling_mode == "fit_width":
                pass  # Adjust scaling through the manager
            self.scene.setBackgroundBrush(QBrush())
        else:
            MEDIA_PLAYER.stop()  # Stop the playback
            MEDIA_PLAYER.setSource(QUrl())  # Clear the media source
            logger.warning("Disabled video playback and cleared source.")

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
        bg_video = get_setting("background_video")
        bg_img = get_setting("background_image")
        if BACKGROUND_VIDEO != bg_video or BACKGROUND_IMAGE != bg_img:
            BACKGROUND_VIDEO = bg_video
            BACKGROUND_IMAGE = bg_img
            logger.info(f"Reloaded BG global variables from settings VIDEO = {BACKGROUND_VIDEO}, IMAGE = {BACKGROUND_IMAGE}")

    def show_grid_menu(self, row, col, dropped_path=None):
        MEDIA_PLAYER.pause()
        menu = Menu(None, row, col, dropped_path, parent=self)
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
        MEDIA_PLAYER.play()
        if (row, col) in self.desktop_icons:
            self.desktop_icons[(row, col)].reload_from_config()

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
        if (row, col) in self.desktop_icons:
            self.desktop_icons[(row, col)].update_icon_path(new_icon_path)
        else:
            self.remove_temp_icon()
            # Add red border item
            self.temp_icon = TempIcon(col, row, new_icon_path)
            self.temp_icon.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                            TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
            self.scene.addItem(self.temp_icon)

    def edit_mode_icon(self, row, col):
        if (row, col) in self.desktop_icons:
            self.desktop_icons[(row, col)].edit_mode_icon()
        else:
            # Ensure only 1 red border icon exists at a time.
            self.remove_red_border_icon()
            # Add red border item
            self.red_border_item = RedBorderItem(col, row)
            self.red_border_item.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                            TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
            self.scene.addItem(self.red_border_item)

    def normal_mode_icon(self, row, col):
        if (row, col) in self.desktop_icons:
            self.desktop_icons[(row, col)].normal_mode_icon()

        self.remove_red_border_icon()
        self.remove_temp_icon()

    def remove_red_border_icon(self):
        if hasattr(self, 'red_border_item') and self.red_border_item is not None:
            self.scene.removeItem(self.red_border_item)
            self.red_border_item = None
    
    def remove_temp_icon(self):
        if hasattr(self, 'temp_icon') and self.temp_icon is not None:
            self.scene.removeItem(self.temp_icon)
            self.temp_icon = None

    def icon_dropped(self, pos):
        # Calculate the column based on the X position of the mouse
        col = (pos.x() - SIDE_PADDING) // (ICON_SIZE + HORIZONTAL_PADDING)

        # Calculate the row based on the Y position of the mouse
        row = (pos.y() - TOP_PADDING) // (ICON_SIZE + VERTICAL_PADDING)

        # Ensure the calculated row and column are within valid ranges
        if 0 <= row < self.max_visible_rows and 0 <= col < self.max_visible_columns:
            return int(row), int(col)

        # If out of bounds, return None
        return None, None

    
    def swap_icons(self, old_row, old_col, new_row, new_col):
        item1 = None
        item2 = None

        # Check the icon it was dragged to, if it exists continue this function, if default/not in self.desktop_icons call swap_with_blank_icon
        if (new_row, new_col) in self.desktop_icons:
            item2 = self.desktop_icons[(new_row, new_col)]
        else:
            self.swap_with_blank_icon(old_row, old_col, new_row, new_col)
            return
        item1 = self.desktop_icons[(old_row, old_col)]
        if item1 is None or item2 is None:
            # Handle cases where one of the items does not exist
            logger.error("One of the items attempting to swap does not exist.")
            return
        result = self.swap_folders(old_row, old_col, new_row, new_col)
        if result != True:
            logger.error("Failed swapping files. do not swap local icons")
            display_cannot_swap_icons_warning(result)
            item1.reload_from_config()
            item2.reload_from_config()
            return
        
        logger.info("folders successfully swapped")

        # Calculate new positions
        item1_new_pos = (SIDE_PADDING + new_col * (ICON_SIZE + HORIZONTAL_PADDING),
                        TOP_PADDING + new_row * (ICON_SIZE + VERTICAL_PADDING))
        item2_new_pos = (SIDE_PADDING + old_col * (ICON_SIZE + HORIZONTAL_PADDING),
                        TOP_PADDING + old_row * (ICON_SIZE + VERTICAL_PADDING))
        
        # Swap positions
        item1.setPos(*item1_new_pos)
        item2.setPos(*item2_new_pos)

        item1.row = new_row
        item1.col = new_col
        item2.row = old_row
        item2.col = old_col

        # Update the desktop_icons array to reflect the swap
        self.desktop_icons[(old_row, old_col)], self.desktop_icons[(new_row, new_col)] = (
            self.desktop_icons[(new_row, new_col)],
            self.desktop_icons[(old_row, old_col)]
        )

        swap_items_by_position(old_row, old_col, new_row, new_col)
        update_folder(new_row, new_col)
        update_folder(old_row, old_col)

        # Reload their fields to update their icon_path. This is a way to refresh fields, but will not update rows/col.
        # Row/col should be changed like the above, then call a refresh.
        item1.reload_from_config()
        item2.reload_from_config()
        logger.info(f"Swapped items at ({old_row}, {old_col}) with ({new_row}, {new_col})")

    def swap_folders(self, old_row, old_col, new_row, new_col):
        new_dir = self.get_data_icon_dir(new_row, new_col)
        exist_dir = self.get_data_icon_dir(old_row, old_col)

        # Stop the movie or it can receive permission errors as a file in use.
        if (new_row, new_col) in self.desktop_icons:
            self.desktop_icons[(new_row, new_col)].movie = None
        if (old_row, old_col) in self.desktop_icons:
            self.desktop_icons[(old_row, old_col)].movie = None
        
        
        if os.path.exists(new_dir) and os.path.exists(exist_dir):
            # Check for write permissions
            if not os.access(new_dir, os.W_OK) or not os.access(exist_dir, os.W_OK):
                logger.error(f"Permission denied on one of the directories: {new_dir}, {exist_dir}")
                return False
            
            try:
                # Swap folder names using temporary folder
                temp_folder = new_dir + '_temp'
                temp_folder = self.get_unique_folder_name(temp_folder)
                logger.info(f"making new folder name = {temp_folder}")
                
                retries = 2
                last_exception = None 
                for _ in range(retries):
                    try:
                        os.rename(new_dir, temp_folder)
                        break
                    except PermissionError as e:
                        last_exception = e
                        logger.warning(f"PermissionError when renaming {new_dir}, retrying... ({e})")
                        time.sleep(0.25)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"Unexpected error when renaming {new_dir}: {e}, retrying...")
                        time.sleep(0.25) 
                else:
                    raise OSError(f"Failed to rename after {retries} retries. \nError: {last_exception}")
                # Continue with the renaming process
                os.rename(exist_dir, new_dir)
                os.rename(temp_folder, exist_dir)

            except Exception as e:
                logger.error(f"Error during folder swap: {e}")
                if temp_folder and os.path.exists(temp_folder):
                    logger.info(f"Rolling back: renaming {temp_folder} back to {new_dir}.")
                    try:
                        os.rename(temp_folder, new_dir)
                    except Exception as rollback_error:
                        logger.error(f"Rollback failed: {rollback_error}")
                return e
        else:
            # get_data_directory should create the folders if they don't exist, so this should theoretically never be called
            logger.error("One or both folders do not exist")
            return "One or both folders do not exist"
        return True

    def swap_with_blank_icon(self, old_row, old_col, new_row, new_col):
        item1 = self.desktop_icons[(old_row, old_col)]

        item1_new_pos = (SIDE_PADDING + new_col * (ICON_SIZE + HORIZONTAL_PADDING),
                TOP_PADDING + new_row * (ICON_SIZE + VERTICAL_PADDING))
        
        item1.setPos(*item1_new_pos)
        item1.row = new_row
        item1.col = new_col
        icon = self.desktop_icons[(old_row, old_col)]
        del self.desktop_icons[(old_row, old_col)]
        self.desktop_icons[(new_row, new_col)] = icon

        swap_items_by_position(old_row, old_col, new_row, new_col)
        self.swap_folders(old_row, old_col, new_row, new_col)
        update_folder(new_row, new_col)
        #update_folder(old_row, old_col)

        item1.reload_from_config()

        logger.info(f"Swapped items at ({old_row}, {old_col}) with ({new_row}, {new_col})")



    def get_unique_folder_name(self, folder_path):
        counter = 1
        new_folder = folder_path
        while os.path.exists(new_folder):
            logger.error(f"Temp file seems to already exist {new_folder}, which seems to not have been removed/renamed after last cleanup.")
            display_failed_cleanup_warning(new_folder)
            new_folder = f"{folder_path}{counter}"
            counter += 1
        return new_folder
    
    def change_max_grid_dimensions(self, rows, cols):
        global MAX_ROWS, MAX_COLS
        MAX_ROWS = rows
        MAX_COLS = cols
        self.clear_icons()
        self.populate_icons()

    def set_cursor(self, cursor):
        QApplication.setOverrideCursor(QCursor(cursor))

    def clear_icons(self):
        for item in self.scene.items():
            if item != self.video_item:
                self.scene.removeItem(item)

    def mouseDoubleClickEvent(self, event):
        # Convert mouse position to scene coordinates
        scene_pos = self.mapToScene(event.pos())
        x = scene_pos.x()
        y = scene_pos.y()

        # Calculate the column and row from the scene coordinates
        icon_size = ICON_SIZE
        row = int((y - TOP_PADDING) // (icon_size + VERTICAL_PADDING))
        col = int((x - SIDE_PADDING) // (icon_size + HORIZONTAL_PADDING))

        # Ensure that the row/col is within the valid range
        if row < 0 or col < 0:
            return
        
        if row >= self.max_visible_rows or col >= self.max_visible_columns:
            logger.info("Icon outside of render distance would be called, thus return and do not call the icon.")
            return

        icon = self.desktop_icons.get((row, col))
        if icon:
            logger.info(f"Double-clicked on icon: {icon.name}")
            icon.double_click(event)  
        else:
            logger.info((f"Double-clicked at default icon row: {row}, column: {col}. Showing grid Menu."))
            self.show_grid_menu(row, col)

    def contextMenuEvent(self, event):
        # Get the global position of the event
        global_position = event.globalPos()
        view_position = self.mapFromGlobal(global_position)
        scene_position = self.mapToScene(view_position)
        x = scene_position.x()
        y = scene_position.y()

        # Calculate the column and row from the scene coordinates
        icon_size = ICON_SIZE
        row = int((y - TOP_PADDING) // (icon_size + VERTICAL_PADDING))
        col = int((x - SIDE_PADDING) // (icon_size + HORIZONTAL_PADDING))

        logger.info(f"Right click at row: {row}, column: {col}")

        # Ensure that the row/col is within the valid range
        if row < 0 or col < 0:
            return
        
        if row >= self.max_visible_rows or col >= self.max_visible_columns:
            logger.info("Icon outside of render distance would be called, thus return and do not show a context menu")
            return

        icon = self.desktop_icons.get((row, col))
        if icon:
            logger.info(f"Showing context menu for icon: {icon.name}")
            icon.context_menu(event)
        else:
            MEDIA_PLAYER.pause()
            context_menu = QMenu()
            self.edit_mode_icon(row, col)

            edit_action = QAction('Edit Icon', context_menu)
            edit_action.triggered.connect(lambda: self.show_grid_menu(row, col))
            context_menu.addAction(edit_action)

            context_menu.aboutToHide.connect(lambda: self.normal_mode_icon(row, col))
            context_menu.exec(event.globalPos())
            MEDIA_PLAYER.play()

            
    
    def add_icon(self, row, col):
        icon = self.desktop_icons.get((row, col))
        if icon is None:
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
                ICON_SIZE)
            icon_item.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                            TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
            self.desktop_icons[(row, col)] = icon_item
            self.scene.addItem(icon_item)

    def delete_icon(self, row, col):
        logger.info(f"delete_icon called with {row} {col}")
        try:
            self.scene.removeItem(self.desktop_icons[(row, col)])
            del self.desktop_icons[(row, col)]
        except Exception as e:
            logger.error(f"Problem removing deleted item from self.desktop_icons: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()


    def dropEvent(self, event):
        # Convert mouse position to scene coordinates
        scene_pos = self.mapToScene(event.pos())
        x = scene_pos.x()
        y = scene_pos.y()

        # Calculate the column and row from the scene coordinates
        icon_size = ICON_SIZE
        row = int((y - TOP_PADDING) // (icon_size + VERTICAL_PADDING))
        col = int((x - SIDE_PADDING) // (icon_size + HORIZONTAL_PADDING))

        logger.info(f"dropped at row: {row}, column: {col}")

        # Ensure that the row/col is within the valid range
        if row < 0 or col < 0:
            return
        
        if row >= self.max_visible_rows or col >= self.max_visible_columns:
            logger.info("Icon outside of render distance would be called, thus return and do not show a context menu")
            return

        icon = self.desktop_icons.get((row, col))
        if icon:
            icon.drop_event(event)
            event.acceptProposedAction()
        else:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()  # Get the list of dropped files (as URLs)
                if urls:
                    file_path = urls[0].toLocalFile()  # Convert the first URL to a local file path
                    event.acceptProposedAction()
                self.show_grid_menu(row, col, file_path)
        


class VideoBackgroundManager:
    def __init__(self, args=None):
        self.zoom_level = 1.0  # Initial zoom level
        self.offset_x = 0      # Initial horizontal offset
        self.offset_y = 0      # Initial vertical offset
        self.center_x = 0      # Center point X
        self.center_y = 0      # Center point Y
        self.video_width = 0   # Video width
        self.video_height = 0  # Video height
        self.video_item = None
        self.center_dot = None  # New attribute for the red dot
        self.aspect_timer = QTimer()
        self.aspect_timer.setSingleShot(True)
        self.aspect_timer.timeout.connect(self.init_center_point)
        self.args = args
        self.aspect_ratio = None
        self.aspect_count = 0
        
        
    def get_video_aspect_ratio(self):
        print("get_video called")
        video_sink = MEDIA_PLAYER.videoSink()
        if video_sink:
            print("video sink exists")
            video_frame = video_sink.videoFrame()
            if video_frame.isValid():
                print("frame is valid")
                print(f"Setting video_width to  {video_frame.size().width()}")
                print(f"Setting video_height to  {video_frame.size().height()}")
                self.video_width = video_frame.size().width()
                self.video_height = video_frame.size().height()
                if self.video_width > 0 and self.video_height > 0:
                    return self.video_width / self.video_height
        return None  # Return None if dimensions aren't yet available


    def init_center_point(self):
        # At max wait 2.5 seconds (50 x 50ms)
        if self.aspect_ratio is None and self.aspect_count < 50:
            self.aspect_count += 1
            print("aspect ratio none")
            self.aspect_ratio = self.get_video_aspect_ratio()
            self.aspect_timer.start(50)
            return
        elif self.aspect_ratio is None:
            self.video_height = -1
            self.video_width = -1
            self.aspect_ratio = -1
        if self.video_item:
            bounding_rect = self.video_item.boundingRect()
            self.center_x = bounding_rect.x() + (bounding_rect.width() / 2)
            self.center_y = bounding_rect.y() + (bounding_rect.height() / 2)
            print(f"x = {self.center_x}, y = {self.center_y}")

            # Initialize or update the red dot position
            if self.args.mode == "debug" or self.args.mode == "devbug":
                self.init_center_dot()

    def init_center_dot(self):
        if not self.center_dot:
            self.center_dot = QGraphicsEllipseItem(-5, -5, 10, 10)
            self.center_dot.setBrush(QColor("red"))
            self.center_dot.setPen(Qt.NoPen)
            self.video_item.scene().addItem(self.center_dot)

        self.center_dot.setPos(self.center_x, self.center_y)

    def zoom_video(self, zoom_factor):
        # Update the zoom level, change this eventually to use a static zoom number, not a % scaling every time its called.
        self.zoom_level *= zoom_factor
        # Update the transformation
        self.update_video_transform()

    # These are static x_offset, y_offset i.e. calling move_video(10, 0), then move_video(5, 0) puts the video offset at (5, 0) not (15, 0)
    def move_video(self, x_offset, y_offset):
        self.offset_x = x_offset
        bounding_rect = self.video_item.boundingRect()
        self.center_x = bounding_rect.x() + (bounding_rect.width() / 2) -self.offset_x
        self.offset_y = y_offset
        self.center_y = bounding_rect.y() + (bounding_rect.height() / 2) -self.offset_y
        self.update_video_transform()

    def update_video_transform(self):
        if self.video_item:  # Check if video item exists
            # Create the transform
            transform = QTransform()
            transform.translate(self.center_x + self.offset_x, self.center_y + self.offset_y)  # Move to center + offset
            transform.scale(self.zoom_level, self.zoom_level)  # Apply scaling
            transform.translate(-self.center_x, -self.center_y)  # Move back to center

            # Update the video item's transformation
            self.video_item.setTransform(transform)

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            print("loaded")
            self.init_center_point()
        if status == QMediaPlayer.EndOfMedia:
            MEDIA_PLAYER.setPosition(0)
            MEDIA_PLAYER.play()


    def set_video_source(self, video_path):
        MEDIA_PLAYER.setSource(QUrl.fromLocalFile(video_path))
        MEDIA_PLAYER.setPlaybackRate(1.0)
        MEDIA_PLAYER.setLoops(QMediaPlayer.Infinite)
        MEDIA_PLAYER.play()


       
    
    



class RedBorderItem(QGraphicsItem):
    def __init__(self, col, row):
        super().__init__()
        x_pos = SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING)
        y_pos = TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING)
        self.setPos(x_pos, y_pos)
    
    def boundingRect(self):
        return QRectF(0, 0, ICON_SIZE, ICON_SIZE)
    
    def paint(self, painter, option, widget=None):
        pen = QPen(BORDER_COLOR, BORDER_WIDTH)
        painter.setPen(pen)
        rect = self.boundingRect()
        adjusted_rect = rect.adjusted(BORDER_WIDTH/2, BORDER_WIDTH/2, -BORDER_WIDTH/2, -BORDER_WIDTH/2)
        painter.drawRect(adjusted_rect)



class TempIcon(QGraphicsItem):
    def __init__(self, col, row, new_icon_path):
        super().__init__()

        if os.path.exists(new_icon_path):
            self.pixmap = QPixmap(new_icon_path)
        # Grid_menu already passes back "assets/images/unknown.png" reference, if for some reason this is invalid, display a blank pixmap
        else:
            self.pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
            self.pixmap.fill(Qt.transparent)
        x_pos = SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING)
        y_pos = TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING)
        self.setPos(x_pos, y_pos)
    
    def boundingRect(self):
        return QRectF(0, 0, ICON_SIZE, ICON_SIZE)
    
    def paint(self, painter, option, widget=None):
        scaled_pixmap = self.pixmap.scaled(ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (ICON_SIZE - scaled_pixmap.width()) / 2
        y_offset = (ICON_SIZE - scaled_pixmap.height()) / 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)









class DesktopIcon(QGraphicsItem):
    def __init__(self, row, col, name, icon_path, executable_path, command_args, website_link, launch_option, icon_size=64, parent=None):
        super().__init__(parent)

        # Need to be changed manually usually by DesktopGrid (self.desktop_icons[(row, col)].row = X)
        self.row = row
        self.col = col
        self.pixmap = None

        # Reloaded fields can simply be refreshed to match current config by reload_from_config()
        self.name = name
        self.icon_path = icon_path
        self.executable_path = executable_path
        self.command_args = command_args
        self.website_link = website_link
        self.launch_option = launch_option

        self.movie = None # For loading a gif
        self.init_movie() # Load movie if .gif icon_path

        self.text_height = 0

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setAcceptDrops(True)

        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.padding = 30
        self.font = QFont(FONT, FONT_SIZE)

        self.edit_mode = False
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
        data = get_item_data(self.row, self.col)
        self.name = data['name']
        self.icon_path = data['icon_path']
        self.executable_path = data['executable_path']
        self.command_args = data['command_args']
        self.website_link = data['website_link']
        self.launch_option = data['launch_option']
        self.init_movie()
        self.load_pixmap()


    def update_font(self):
        self.font = QFont(FONT, FONT_SIZE)
        self.update()


    def update_size(self, new_size):
        self.icon_size = new_size
        self.prepareGeometryChange()

    def boundingRect(self) -> QRectF:
        self.text_height = self.calculate_text_height(self.name)
        return QRectF(0, 0, self.icon_size, self.icon_size + self.text_height + self.padding)
    
    def edit_mode_icon(self):
        self.edit_mode = True
        self.update() 
    
    def normal_mode_icon(self):
        self.edit_mode = False
        self.update() 

    def load_pixmap(self):
        if self.movie:
            return
        if self.icon_path and os.path.exists(self.icon_path):
            cached_pixmap = QPixmapCache.find(self.icon_path)
            if cached_pixmap:
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

            painter.setFont(self.font)

            lines = self.get_multiline_text(self.font, self.name)

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
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(outline_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)) # 4 = pixels of outline eventually will have a setting
                painter.drawPath(path)

                # Draw the main text in the middle
                painter.setPen(text_color)
                painter.drawText(0, text_y, line)

        if self.edit_mode:
            pen = QPen(BORDER_COLOR, BORDER_WIDTH)
            painter.setPen(pen)
            rect = self.boundingRect()
            # Draw the border inside the square, adjusted for the border width
            adjusted_rect = rect.adjusted(BORDER_WIDTH/2, BORDER_WIDTH/2, -BORDER_WIDTH/2, -BORDER_WIDTH/2)
            painter.drawRect(adjusted_rect)
                

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
        MEDIA_PLAYER.pause()
        context_menu = QMenu()

        self.edit_mode_icon()

        # Edit Icon section
        
        logger.info(f"Row: {self.row}, Column: {self.col}, Name: {self.name}, Icon_path: {self.icon_path}, Exec Path: {self.executable_path}, Command args: {self.command_args}, Website Link: {self.website_link}, Launch option: {self.launch_option}")
        
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
        MEDIA_PLAYER.play()

    def context_menu_closed(self):
        logger.debug("Context menu closed")
        self.normal_mode_icon()

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
            self.init_movie() # Load gif into movie if icon_path is .gif
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
                MEDIA_PLAYER.pause()
                logger.info("Swapping icons.")
                view.swap_icons(old_row, old_col, new_row, new_col)
            elif self.distance > 5:
                logger.info("Icon dropped at same location")
            
            
            self.update()
        MEDIA_PLAYER.play()

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

