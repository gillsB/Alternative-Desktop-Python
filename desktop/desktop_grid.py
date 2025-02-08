from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QApplication, QMenu
from PySide6.QtCore import Qt, QRectF, QTimer, QMetaObject, QUrl, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QAction, QCursor
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from util.settings import get_setting
from util.config import get_icon_data, create_paths, is_default, get_data_directory, swap_icons_by_position, update_folder
from util.utils import TempIcon
from desktop.icon_edit_menu import Menu
from menus.display_warning import (display_failed_cleanup_warning,  display_cannot_swap_icons_warning)
from desktop.icon_edit_menu import Menu
from desktop.image_background_manager import ImageBackgroundManager
from desktop.video_background_manager import VideoBackgroundManager
from desktop.desktop_icon import DesktopIcon
import os
import logging
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

class DesktopGrid(QGraphicsView):
    def __init__(self, parent=None, args=None):
        super().__init__(parent)
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

        # Set up media player, VideoBackgroundManager and ImageBackgroundManager
        global MEDIA_PLAYER
        MEDIA_PLAYER = QMediaPlayer()
        self.scene.clear()
        self.load_bg_from_settings()
        self.load_video, self.load_image = self.background_setting()
        self.video_manager = VideoBackgroundManager(args, MEDIA_PLAYER)  # Create an instance of VideoBackgroundManager
        self.video_manager.video_item = QGraphicsVideoItem()  # Initialize the QGraphicsVideoItem
        self.scene.addItem(self.video_manager.video_item)  # Add video item to the scene
        self.video_manager.video_item.setZValue(-2)  # Set the Z value for rendering order
        MEDIA_PLAYER.setVideoOutput(self.video_manager.video_item)  # Set the video output
        MEDIA_PLAYER.setPlaybackRate(1.0)
        MEDIA_PLAYER.mediaStatusChanged.connect(self.video_manager.handle_media_status_changed)
        logger.info(f"self.load_video = {self.load_video}, self.load_image = {self.load_image}")

        self.image_background_manager = ImageBackgroundManager(self)


        
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

    # Calls reload_from_config() on all desktopIcons which ensures the Icons appearance is up to date and redraws all icons.
    def redraw_all_icons(self):
        for icon in self.desktop_icons.values():
            if isinstance(icon, DesktopIcon):
                icon.reload_from_config()



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scene.setSceneRect(self.rect())
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

    # Ignores wheel scrolling EXCEPT for when launched with "debug" or "devbug"
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # Use .y() for vertical scrolling

        if self.args.mode == "debug" or self.args.mode == "devbug":
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
                logger.error("Error triggering on purpose (debug mode enabled for this test)")
                print(f"{self.desktop_icons[(0,0)].names}")
            else:
                ICON_SIZE = 64
                self.update_icon_size(64)
                FONT_SIZE = 10
                self.desktop_icons[(0,0)].update_font()
                # ERROR on purpose to test logging exceptions/traceback.
                logger.error("Error triggering on purpose (debug mode enabled for this test)")
                x = 1/0

        event.ignore()  # Ignore the event to prevent scrolling



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
    
    def render_bg(self, bg_enabled = None, bg_color=None):
        old_bg_video = BACKGROUND_VIDEO
        self.load_bg_from_settings()
        self.load_video, self.load_image = self.background_setting()
        
        if self.load_video:
            if old_bg_video != BACKGROUND_VIDEO or MEDIA_PLAYER.mediaStatus() == QMediaPlayer.NoMedia:
                self.video_manager.set_video_source(BACKGROUND_VIDEO)
                logger.info(f"Set background video source = {BACKGROUND_VIDEO}")
                self.video_manager.load_new_video()
            else:
                self.video_manager.init_center_point()
        else:
            if MEDIA_PLAYER.playbackState() == QMediaPlayer.PlayingState:
                logger.info("Disabled video playback and cleared source.")
            MEDIA_PLAYER.stop()  # Stop the playback
            MEDIA_PLAYER.setSource(QUrl())  # Clear the media source


        if self.load_image:
            self.image_background_manager.load_background(BACKGROUND_IMAGE)
            
        else:
            # Remove image background_item if it exists.
            self.image_background_manager.remove_background()

        secondary_color = getattr(self.parent(), 'secondary_color', '#202020')
        custom_color = get_setting("custom_bg_fill", False)
        theme_name = getattr(self.parent(), 'theme_name', None)

        color = None

        # Base background color becomes "secondary_color" for dark mode, medium gray for No theme,
        #  and a lighter version of the theme's primaryLightColor for light themes.
        if theme_name.startswith('dark'):
            color = QColor(secondary_color)
        elif theme_name.startswith('none'):
            color = QColor('#303030')
        else:
            color = QColor(getattr(self.parent(), 'light_desktop_color', '#303030'))

        if bg_enabled != False:
            if (custom_color or bg_enabled) and bg_color == None:
                color = (QColor(get_setting("custom_bg_color", "white")))
            elif custom_color or bg_enabled:
                color = QColor(bg_color)

        # Set the background color as a solid brush
        if color != None:
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
        menu = Menu(None, row, col, dropped_path, parent=self)
        main_window_size = self.parent().size()
        main_window_height = main_window_size.height()
        dialog_width = min(main_window_size.width() / 3, 725)
        dialog_height = min(main_window_size.height() / 2, 550)

        logger.info(f"base monitor width: {main_window_size.width()} resize width: {main_window_size.width() / 3}")
        logger.info(f"base monitor height: {main_window_size.height()} resize height: {main_window_size.height() / 2}")
        logger.info(f"dialog_width set to {dialog_width}")
        logger.info(f"dialog_height set to {dialog_height}")

        # Get the desktop icon's screen position (relative to QGraphicsView)
        icon_pos = self.get_icon_position(row, col)
        
        # Convert the icon's position to global screen coordinates
        global_icon_pos = self.mapToGlobal(icon_pos)

        # Available space around the icon (based on global screen coordinates)
        screen_geometry = self.parent().screen().geometry()
        space_left = global_icon_pos.x()
        space_right = screen_geometry.width() - global_icon_pos.x() - ICON_SIZE - HORIZONTAL_PADDING

        # If menu would extend below taskbar, adjust y to fit within main window
        if global_icon_pos.y() + dialog_height > screen_geometry.bottom()-80:  
            logger.info("Adjusting y value up to ensure window appears fully on screen")
            # 80 to ensure it appears above taskbar
            adjusted_y = (screen_geometry.bottom() -80) - dialog_height
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
            self.temp_icon = TempIcon(col, row, new_icon_path, ICON_SIZE)
            self.temp_icon.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                            TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
            self.scene.addItem(self.temp_icon)

    def draw_red_border(self, row, col):
        # Ensure only 1 red border icon exists at a time.
        self.remove_red_border()
        # Add red border item
        self.red_border_item = RedBorderItem(col, row)
        self.red_border_item.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                        TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
        self.scene.addItem(self.red_border_item)

    def remove_red_border(self):
        if hasattr(self, 'red_border_item') and self.red_border_item is not None:
            self.scene.removeItem(self.red_border_item)
            self.red_border_item = None
    
    def remove_temp_icon(self):
        if hasattr(self, 'temp_icon'):
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
        icon1 = None
        icon2 = None

        # Check the icon it was dragged to, if it exists continue this function, if default/not in self.desktop_icons call swap_with_blank_icon
        if (new_row, new_col) in self.desktop_icons:
            icon2 = self.desktop_icons[(new_row, new_col)]
        else:
            self.swap_with_blank_icon(old_row, old_col, new_row, new_col)
            return
        icon1 = self.desktop_icons[(old_row, old_col)]
        if icon1 is None or icon2 is None:
            # Handle cases where one of the icons does not exist
            logger.error("One of the icons attempting to swap does not exist.")
            return
        result = self.swap_folders(old_row, old_col, new_row, new_col)
        if result != True:
            logger.error("Failed swapping files. do not swap local icons")
            display_cannot_swap_icons_warning(result)
            icon1.reload_from_config()
            icon2.reload_from_config()
            return
        
        logger.info("folders successfully swapped")

        # Calculate new positions
        icon1_new_pos = (SIDE_PADDING + new_col * (ICON_SIZE + HORIZONTAL_PADDING),
                        TOP_PADDING + new_row * (ICON_SIZE + VERTICAL_PADDING))
        icon2_new_pos = (SIDE_PADDING + old_col * (ICON_SIZE + HORIZONTAL_PADDING),
                        TOP_PADDING + old_row * (ICON_SIZE + VERTICAL_PADDING))
        
        # Swap positions
        icon1.setPos(*icon1_new_pos)
        icon2.setPos(*icon2_new_pos)

        icon1.row = new_row
        icon1.col = new_col
        icon2.row = old_row
        icon2.col = old_col

        # Update the desktop_icons array to reflect the swap
        self.desktop_icons[(old_row, old_col)], self.desktop_icons[(new_row, new_col)] = (
            self.desktop_icons[(new_row, new_col)],
            self.desktop_icons[(old_row, old_col)]
        )

        swap_icons_by_position(old_row, old_col, new_row, new_col)
        update_folder(new_row, new_col)
        update_folder(old_row, old_col)

        # Reload their fields to update their icon_path. This is a way to refresh fields, but will not update rows/col.
        # Row/col should be changed like the above, then call a refresh.
        icon1.reload_from_config()
        icon2.reload_from_config()
        logger.info(f"Swapped icons at ({old_row}, {old_col}) with ({new_row}, {new_col})")

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
        icon1 = self.desktop_icons[(old_row, old_col)]

        icon1_new_pos = (SIDE_PADDING + new_col * (ICON_SIZE + HORIZONTAL_PADDING),
                TOP_PADDING + new_row * (ICON_SIZE + VERTICAL_PADDING))
        
        icon1.setPos(*icon1_new_pos)
        icon1.row = new_row
        icon1.col = new_col
        icon = self.desktop_icons[(old_row, old_col)]
        del self.desktop_icons[(old_row, old_col)]
        self.desktop_icons[(new_row, new_col)] = icon

        swap_icons_by_position(old_row, old_col, new_row, new_col)
        self.swap_folders(old_row, old_col, new_row, new_col)
        update_folder(new_row, new_col)
        #update_folder(old_row, old_col)

        icon1.reload_from_config()

        logger.info(f"Swapped icons at ({old_row}, {old_col}) with ({new_row}, {new_col})")



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
            if item != self.video_manager.video_item:
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
        self.draw_red_border(row, col)
        if icon:
            logger.info(f"Showing context menu for icon: {icon.name}")
            context_menu = icon.context_menu(event)
        else:
            context_menu = QMenu()


            edit_action = QAction('Edit Icon', context_menu)
            edit_action.triggered.connect(lambda: self.show_grid_menu(row, col))
            context_menu.addAction(edit_action)

            context_menu.exec(event.globalPos())

        self.remove_red_border()
        self.remove_temp_icon()

    # Preview an icon with the font_size changed. Make sure to reload_icon upon close/after or it will get stuck.
    def preview_font_size_change(self, row, col, font_size):
        icon = self.desktop_icons.get((row, col))
        if icon:
            icon.update_font(font_size)
            logger.info(f"Updated font size to {font_size} for icon {row}, {col}")
        else:
            logger.warning(f"No icon found at {row} {col} preview the font size change")

    # Preview an icon with the font_color changed. Make sure to reload_icon upon close/after or it will get stuck.
    def preview_font_color_change(self, row, col, font_color):
        icon = self.desktop_icons.get((row, col))
        if icon:
            icon.update_font_color(font_color)
            logger.info(f"Updated font color to {font_color} for icon {row}, {col}")
        else:
            logger.warning(f"No icon found at {row} {col} to preview the font color change.")

    # Ensures all variables are up to date and repaints the icon (including name label).
    def reload_icon(self, row, col):
        icon = self.desktop_icons.get((row, col))
        if icon:
            icon.reload_from_config()
            logger.info(f"Reloaded icon at ({row}, {col})")
        else:
            logger.warning(f"No icon found at ({row}, {col}) to reload.")
    
    def add_icon(self, row, col):
        icon = self.desktop_icons.get((row, col))
        if icon is None:
            icon_item = DesktopIcon(
                row, 
                col, 
                ICON_SIZE)
            icon_item.setPos(SIDE_PADDING + col * (ICON_SIZE + HORIZONTAL_PADDING), 
                            TOP_PADDING + row * (ICON_SIZE + VERTICAL_PADDING))
            self.desktop_icons[(row, col)] = icon_item
            self.scene.addItem(icon_item)
        else:
            self.reload_icon(row, col)

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




class RedBorderItem(QGraphicsItem):
    def __init__(self, col, row):
        super().__init__()
    
    def boundingRect(self):
        return QRectF(0, 0, ICON_SIZE, ICON_SIZE)
    
    def paint(self, painter, option, widget=None):
        border_width = get_setting("border_width", 5)
        color = QColor(get_setting("border_color", "#ff0000"))
        pen = QPen(color, border_width)
        painter.setPen(pen)
        rect = self.boundingRect()
        adjusted_rect = rect.adjusted(border_width/2, border_width/2, -border_width/2, -border_width/2)
        painter.drawRect(adjusted_rect)



