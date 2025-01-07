from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import Qt, QTimer, QUrl, QSizeF
from PySide6.QtGui import QColor, QTransform
from PySide6.QtMultimedia import QMediaPlayer
from util.settings import get_setting
import logging

logger = logging.getLogger(__name__)




MEDIA_PLAYER = None



class VideoBackgroundManager:
    def __init__(self, args=None, media_player=None):
        self.zoom_level = 1.0  # Initial zoom level
        self.offset_x = 0      # Initial horizontal offset
        self.offset_y = 0      # Initial vertical offset
        self.center_x = 0      # Anchor point X that works as the center/focal point of the scene upon which zooms in/out are focused upon
        self.center_y = 0      # Anchor point Y that works as the center/focal point of the scene upon which zooms in/out are focused upon
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
        self.scene_width = 0
        self.scene_height = 0
        global MEDIA_PLAYER
        MEDIA_PLAYER = media_player

        
    def get_video_aspect_ratio(self):
        video_sink = MEDIA_PLAYER.videoSink()
        if video_sink:
            video_frame = video_sink.videoFrame()
            if video_frame.isValid():
                logger.info(f"Setting video_width to  {video_frame.size().width()}")
                logger.info(f"Setting video_height to  {video_frame.size().height()}")
                self.video_width = video_frame.size().width()
                self.video_height = video_frame.size().height()
                self.video_item.setSize(QSizeF(self.video_width, self.video_height))
                self.scene_width = self.video_item.scene().sceneRect().width()
                self.scene_height = self.video_item.scene().sceneRect().height()

                self.center_x = self.video_width / 2
                self.center_y = self.video_height / 2
                logger.info(f"Center of video x = {self.center_x}, y = {self.center_y}")
                
                if self.video_width > 0 and self.video_height > 0:
                    return self.video_width / self.video_height
                
        return None  # Return None if dimensions aren't yet available

    def load_new_video(self):
        self.aspect_ratio = None
        self.init_center_point()

    def init_center_point(self):
        # At max wait 5 seconds (100 x 50ms)
        if self.aspect_ratio is None and self.aspect_count < 100:
            self.aspect_count += 1
            self.aspect_ratio = self.get_video_aspect_ratio()
            self.aspect_timer.start(50)
            return
        elif self.aspect_ratio is None:
            self.video_height = -1
            self.video_width = -1
            self.aspect_ratio = -1
        if self.video_item:
            # Move Video item to center BEFORE adjusting settings values. (init video_item location)
            self.center_video()

            # Initialize or update the red dot position
            if self.args.mode == "debug" or self.args.mode == "devbug":
                self.init_center_dot()

            self.move_video(-1 * get_setting("video_x_offset", 0.00), get_setting("video_y_offset", 0.00))
            self.zoom_video(get_setting("video_zoom", 1.00))

    def init_center_dot(self):
        if self.center_dot:
            self.video_item.scene().removeItem(self.center_dot)
        self.center_dot = QGraphicsEllipseItem(-5, -5, 10, 10)
        self.center_dot.setBrush(QColor("red"))
        self.center_dot.setPen(Qt.NoPen)
        self.video_item.scene().addItem(self.center_dot)
        self.center_dot.setPos(self.scene_width/2, self.scene_height/2)

    def zoom_video(self, zoom_factor):
        self.zoom_level = zoom_factor
        self.update_video_transform()

    # Move video to center within the scene(Initial setup of video item location)
    def center_video(self):
        if self.video_item:
            # Get dimensions of scene/video
            self.scene_width = self.video_item.scene().sceneRect().width()
            self.scene_height = self.video_item.scene().sceneRect().height()
            
            # Set the video position such that the center of the video is the center of the viewport(screen)
            # Centered values are the value of the top left based coordinate
            centered_x = (self.scene_width - self.video_width) / 2
            centered_y = (self.scene_height - self.video_height) / 2
            self.video_item.setPos(centered_x, centered_y)

            logger.info(f"Video item placed at: ({centered_x}, {centered_y})")

    # These are static x_offset, y_offset i.e. calling move_video(-0.10, 0), then move_video(-0.05, 0) puts the video offset at (-0.05, 0) not (-0.15, 0)
    # Arguments are float values: -1 = bottom/left of video, 0 = center,  1 = top/right of video settings_menu versions are *100 int values (i.e. 100 = 1.00 float value)
    def move_video(self, x_offset, y_offset):
        if self.video_item:
            self.offset_x = -x_offset * (self.video_width / 2)
            self.offset_y = y_offset * (self.video_height / 2)
            self.center_x = (self.video_width / 2) - self.offset_x
            self.center_y = (self.video_height / 2) - self.offset_y
            self.update_video_transform()
        else:
            logger.warning("Trying to move a video_item that does not exist")

    def update_video_transform(self):
        if self.video_item:  # Check if video item exists
            # Create the transform
            transform = QTransform()
            transform.translate(self.center_x + self.offset_x, self.center_y + self.offset_y)  # Set transformation central point to focus point
            transform.scale(self.zoom_level, self.zoom_level)  # Scale around that focus point
            transform.translate(-self.center_x, -self.center_y)  # Revert back the transformation central point

            # Update the video item's transformation
            self.video_item.setTransform(transform)

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            logger.info("QMediaPlayer loaded media")
        if status == QMediaPlayer.EndOfMedia:
            MEDIA_PLAYER.setPosition(0)
            MEDIA_PLAYER.play()

    def set_video_source(self, video_path):
        MEDIA_PLAYER.setSource(QUrl.fromLocalFile(video_path))
        MEDIA_PLAYER.setPlaybackRate(1.0)
        MEDIA_PLAYER.setLoops(QMediaPlayer.Infinite)
        MEDIA_PLAYER.play()
