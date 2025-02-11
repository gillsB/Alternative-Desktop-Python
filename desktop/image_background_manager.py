from PySide6.QtWidgets import QGraphicsView, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QTransform
from util.settings import get_setting
import logging


logger = logging.getLogger(__name__)


class ImageBackgroundManager:
    def __init__(self, parent_view: QGraphicsView, parent= None):
        self.parent_view = parent_view
        self.background_item = None
        self.pixmap = None
        self.scene = self.parent_view.scene
        self.zoom_level = 1.00
        self.center_x = 0.00
        self.center_y = 0.00
        self.pixmap_width = 0
        self.pixmap_height = 0
        self.parent = parent

    def load_background(self, image_path: str):
        # If there's an existing background, remove it
        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None

        # Load the new image
        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            logger.error(f"Image background manager: Failed to load image: {image_path}")
            return
        logger.info(f"Successfully loaded background image: {image_path}")

        # Create a QGraphicsPixmapItem for the image
        self.background_item = QGraphicsPixmapItem(self.pixmap)
        if get_setting("bg_z_order", 0) == 0:
            self.background_item.setZValue(-3)
        else:
            self.background_item.setZValue(-1)

        scene_rect = self.scene.sceneRect()

        # Calculate the position to center the background in the scene
        self.pixmap_width = self.pixmap.width()
        self.pixmap_height = self.pixmap.height()
        center_x = (scene_rect.width() - self.pixmap_width) / 2
        center_y = (scene_rect.height() - self.pixmap_height) / 2
        self.background_item.setPos(center_x, center_y)
        self.scene.addItem(self.background_item)
        self.parent.apply_bg_fill()

        self.update_from_settings()

    # Refreshes background location/zoom to the adjustment/zoom stored in settings.
    def update_from_settings(self):
        # Move and zoom based on stored settings, if any
        self.move_background(-1 * get_setting("image_x_offset", 0.00), get_setting("image_y_offset", 0.00))
        self.zoom_background(get_setting("image_zoom", 1.00))

    def zoom_background(self, zoom_factor):
        self.zoom_level = zoom_factor
        self.update_background_transform()

    # These are static x_offset, y_offset i.e. calling move_background(-0.10, 0), then move_background(-0.05, 0) puts the image offset at (-0.05, 0) not (-0.15, 0)
    # Arguments are float values: -1 = bottom/left of image, 0 = center,  1 = top/right of image settings_menu versions are *100 int values (i.e. 100 = 1.00 float value)
    def move_background(self, x_offset, y_offset):
        if self.background_item:
            self.offset_x = -x_offset * (self.pixmap_width / 2)
            self.offset_y = y_offset * (self.pixmap_height / 2)
            self.center_x = (self.pixmap_width / 2) - self.offset_x
            self.center_y = (self.pixmap_height / 2) - self.offset_y
            self.update_background_transform()
        else:
            logger.warning("Trying to move a background_item that does not exist")

    def update_background_transform(self):
        if self.background_item:  # Check if image background item exists
            # Create the transform
            transform = QTransform()
            transform.translate(self.center_x + self.offset_x, self.center_y + self.offset_y) # Set transformation central point to focus point
            transform.scale(self.zoom_level, self.zoom_level) # Scale around that focus point
            transform.translate(-self.center_x, -self.center_y) # Revert back the transformation central point

            # Update the image item's transformation
            self.background_item.setTransform(transform)

    def remove_background(self):
        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None

    def set_z_value(self, value):
        logger.info(f"setting zvalue to {value}")
        self.background_item.setZValue(value)