import os
from PyQt5.QtCore import QDir, Qt, QUrl, QTime, QThread, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QVBoxLayout,
    QPushButton, QSizePolicy, QSlider, QStyle, QWidget, QListWidget, QListWidgetItem, QMainWindow, QAction,
    QInputDialog, QLineEdit, qApp, QProgressBar
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from pytube import YouTube
import sys

os.environ["QT_QPA_PLATFORM"] = "wayland"


class DownloadThread(QThread):
    download_complete = pyqtSignal(str)

    def __init__(self, url, video_directory, parent=None):
        super(DownloadThread, self).__init__(parent)
        self.url = url
        self.video_directory = video_directory
        self.default_resolution = "720p"

    def run(self):
        try:
            yt = YouTube(self.url)
            video_stream = yt.streams.filter(file_extension="mp4", progressive=True,
                                             resolution=self.default_resolution).first()

            if video_stream is not None:
                new_video_name = video_stream.title.lower().replace(' ', '') + '.mp4'
                video_file_path = os.path.join(self.video_directory, new_video_name)

                video_stream.download(self.video_directory)

                # Emit signal to indicate download completion
                self.download_complete.emit(new_video_name)
            else:
                # Video stream is not available
                print("Error downloading video: Video stream is not available.")
        except Exception as e:
            # Print the exception traceback for debugging
            import traceback
            traceback.print_exc()
            print(f"Error downloading video: {str(e)}")


class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("PyQt Video Player Widget Example")

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.videoListWidget = QListWidget()
        self.videoListWidget.itemClicked.connect(self.videoSelected)
        self.videoListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.videoListWidget.customContextMenuRequested.connect(self.showContextMenu)

        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)
        fullscreen_action = QAction(QIcon('fullscreen.png'), '&Toggle Fullscreen', self)
        fullscreen_action.setShortcut('Ctrl+F')
        fullscreen_action.setStatusTip('Toggle Fullscreen')
        fullscreen_action.triggered.connect(self.toggleFullscreen)

        setVideoDirAction = QAction(QIcon('set_directory.png'), '&Set Video Directory', self)
        setVideoDirAction.setShortcut('Ctrl+D')
        setVideoDirAction.setStatusTip('Set Video Directory')
        setVideoDirAction.triggered.connect(self.setVideoDirectory)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(setVideoDirAction)
        fileMenu.addAction(exit_action)

        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(fullscreen_action)

        wid = QWidget(self)
        self.setCentralWidget(wid)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)

        self.rewindButton = QPushButton("Rewind 10s")
        self.rewindButton.clicked.connect(self.rewindBackward)
        controlLayout.addWidget(self.rewindButton)

        smallFullscreenButton = QPushButton("Fullscreen")
        smallFullscreenButton.clicked.connect(self.toggleFullscreen)
        smallFullscreenButton.setMaximumWidth(100)  # Set a maximum width to make it smaller
        controlLayout.addWidget(smallFullscreenButton)

        self.skipButton = QPushButton("Skip 10s")
        self.skipButton.clicked.connect(self.skipForward)
        controlLayout.addWidget(self.skipButton)

        # Create the refresh button
        refreshButton = QPushButton("Refresh")
        refreshButton.clicked.connect(self.refreshVideoPlayer)

        # Add the refresh button to the control layout
        controlLayout.addWidget(refreshButton)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)
        layout.addWidget(self.videoListWidget)

        # Create the delete button and set its size and alignment
        deleteButton = QPushButton("Delete Selected Video")
        deleteButton.setStyleSheet("background-color: red; color: white")
        deleteButton.clicked.connect(self.deleteSelectedVideo)

        # Create a layout for the delete button and align it to the right-top corner
        deleteLayout = QHBoxLayout()
        deleteLayout.addStretch()  # Add stretch to push the delete button to the right
        deleteLayout.addWidget(deleteButton)  # Add the delete button to the layout

        layout.addLayout(deleteLayout)  # Add the deleteLayout to the main layout

        downloadButton = QPushButton("Download YouTube Video")
        downloadButton.clicked.connect(self.downloadVideo)

        deleteLayout.addWidget(downloadButton)

        self.timelineLabel = QLabel()  # Initialize the timelineLabel
        controlLayout.addWidget(self.timelineLabel)  # Add the timelineLabel to the controlLayout

        self.auto_play = False
        self.current_video_index = 0

        self.autoPlayButton = QPushButton("Auto Play")
        self.autoPlayButton.setCheckable(True)
        self.autoPlayButton.setChecked(False)
        self.autoPlayButton.clicked.connect(self.toggleAutoPlay)

        controlLayout.addWidget(self.autoPlayButton)

        self.messageLabel = QLabel(self)
        self.messageLabel.setAlignment(Qt.AlignCenter)

        self.messageTimer = QTimer(self)
        self.messageTimer.timeout.connect(self.clearMessage)

        self.messageTimer.stop()

        layout.addWidget(self.messageLabel)

        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)

        self.mediaPlayer.error.connect(self.handleError)

        # Enable keyboard focus for the window
        self.setFocusPolicy(Qt.StrongFocus)

        self.video_directory = '/home/user/Videos'  # Default video directory
        self.download_thread = DownloadThread("", "")  # Placeholder, will be set in downloadVideo method
        self.download_thread.download_complete.connect(self.onDownloadComplete)

    def toggleAutoPlay(self):
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.playNextVideo()

    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Video File", "",
                                                  "Video Files (*.mp4 *.avi *.mkv);;All Files (*)", options=options)
        if fileName:
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
            self.mediaPlayer.play()
    def playNextVideo(self):
        video_count = self.videoListWidget.count()
        if video_count > 0:
            self.current_video_index = (self.current_video_index + 1) % video_count
            video_item = self.videoListWidget.item(self.current_video_index)
            video_path = os.path.join(self.video_directory, video_item.text())
            video_url = QUrl.fromLocalFile(video_path)
            self.mediaPlayer.setMedia(QMediaContent(video_url))
            self.playButton.setEnabled(True)
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if state == QMediaPlayer.StoppedState and self.auto_play:
            self.playNextVideo()
        else:
            if state == QMediaPlayer.PlayingState:
                self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            elif state == QMediaPlayer.PausedState:
                self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            else:
                self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        self.updateTimelineLabels()

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
        self.updateTimelineLabels()

    def setPosition(self, position):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.setPosition(position)
        else:
            # If the media player is not in the PlayingState, start playing
            self.mediaPlayer.setPosition(position)
            self.mediaPlayer.play()

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def videoSelected(self, item):
        video_path = os.path.join(self.video_directory, item.text())

        # Use QUrl.fromLocalFile directly without additional conversions
        video_url = QUrl.fromLocalFile(video_path)

        # Set the media with the corrected QUrl
        self.mediaPlayer.setMedia(QMediaContent(video_url))

        self.playButton.setEnabled(True)
        self.mediaPlayer.play()  # Autoplay when clicking on the video list item

    def downloadVideo(self):
        url, okPressed = QInputDialog.getText(self, "Download YouTube Video", "Enter YouTube URL:", QLineEdit.Normal,
                                              "")
        if okPressed and url:
            # Set the URL, directory, and resolution for the download thread
            self.download_thread.url = url
            self.download_thread.video_directory = self.video_directory

            # Start the download thread
            self.download_thread.start()

    def onDownloadComplete(self, new_video_name):
        # This method is called when the download is complete
        video_path = os.path.join(self.video_directory, new_video_name)

        item = QListWidgetItem(new_video_name)
        self.videoListWidget.addItem(item)

        # Show success message
        self.showMessage(f"Video downloaded successfully: {new_video_name}", success=True)
        # Select the newly added video in the list
        self.videoListWidget.setCurrentItem(item)
        self.updateVideoList()

    def showMessage(self, message, success=True):
        self.messageLabel.setText(f"<font color={'green' if success else 'red'}>{message}</font>")
        self.messageLabel.show()
        self.messageTimer.start(5000)  # Display message for 5 seconds

    def clearMessage(self):
        self.messageLabel.clear()
        self.messageLabel.hide()
        self.messageTimer.stop()

    def skipForward(self):
        current_position = self.mediaPlayer.position()
        self.mediaPlayer.setPosition(current_position + 10000)  # Skip forward 10 seconds

    def rewindBackward(self):
        current_position = self.mediaPlayer.position()
        self.mediaPlayer.setPosition(max(0, current_position - 10000))  # Rewind 10 seconds

    def updateTimelineLabels(self):
        current_position = self.mediaPlayer.position()
        total_duration = self.mediaPlayer.duration()

        current_time = QTime(0, 0)
        current_time = current_time.addMSecs(current_position)

        total_time = QTime(0, 0)
        total_time = total_time.addMSecs(total_duration)

        timeline_text = f"{current_time.toString('mm:ss')} / {total_time.toString('mm:ss')}"
        self.timelineLabel.setText(timeline_text)

    def showContextMenu(self, position):
        menu = self.videoListWidget.createStandardContextMenu()
        remove_action = menu.addAction("Remove Video")
        action = menu.exec_(self.videoListWidget.mapToGlobal(position))
        if action == remove_action:
            selected_items = self.videoListWidget.selectedItems()
            for item in selected_items:
                row = self.videoListWidget.row(item)
                self.videoListWidget.takeItem(row)
                video_path = os.path.join(self.video_directory, item.text())
                os.remove(video_path)

    def deleteSelectedVideo(self):
        selected_items = self.videoListWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.videoListWidget.row(item)
                self.videoListWidget.takeItem(row)
                video_path = os.path.join(self.video_directory, item.text())
                os.remove(video_path)
                self.showMessage(f"Video deleted successfully: {item.text()}", success=True)
                self.refreshVideoPlayer()
        else:
            self.showMessage("No video selected for deletion.", success=False)

    def updateVideoList(self):
        # Reload video files from the directory
        video_files = [f for f in os.listdir(self.video_directory) if f.endswith(('.mp4', '.avi', '.mkv'))]

        # Clear existing items in the video list widget
        self.videoListWidget.clear()

        # Populate the list with the updated video files
        for video_file in video_files:
            item = QListWidgetItem(video_file)
            self.videoListWidget.addItem(item)

        # Restore the current item if it exists
        current_item = self.videoListWidget.currentItem()
        if current_item:
            current_item_text = current_item.text()
            for i in range(self.videoListWidget.count()):
                if self.videoListWidget.item(i).text() == current_item_text:
                    self.videoListWidget.setCurrentItem(self.videoListWidget.item(i))
                    break

    def refreshVideoPlayer(self):
        # Stop and clear the current media
        self.mediaPlayer.stop()
        self.mediaPlayer.setMedia(QMediaContent())

        # Clear the video list selection
        self.videoListWidget.clearSelection()

        # Clear the timeline labels
        self.timelineLabel.clear()

        # Disable the play button
        self.playButton.setEnabled(False)

        # Clear the error label
        self.errorLabel.clear()

        # Reload video files from the directory
        video_files = [f for f in os.listdir(self.video_directory) if f.endswith(('.mp4', '.avi', '.mkv'))]

        # Clear existing items in the video list widget
        self.videoListWidget.clear()

        # Populate the list with the updated video files
        for video_file in video_files:
            item = QListWidgetItem(video_file)
            self.videoListWidget.addItem(item)

        # Restore the current item if it exists
        current_item = self.videoListWidget.currentItem()
        if current_item:
            current_item_text = current_item.text()
            for i in range(self.videoListWidget.count()):
                if self.videoListWidget.item(i).text() == current_item_text:
                    self.videoListWidget.setCurrentItem(self.videoListWidget.item(i))
                    break

    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            # Space bar pressed, toggle play/pause
            self.play()
        elif event.key() in (Qt.Key_Left, Qt.Key_R):
            # Left arrow key or 'R' key pressed, rewind 10 seconds
            self.rewindBackward()
        elif event.key() in (Qt.Key_Right, Qt.Key_S):
            # Right arrow key or 'S' key pressed, skip forward 10 seconds
            self.skipForward()
        elif event.key() == Qt.Key_Escape:
            # Escape key pressed, exit fullscreen
            if self.isFullScreen():
                self.showNormal()
        elif event.key() == Qt.Key_F:
            # 'F' key pressed, toggle fullscreen
            self.toggleFullscreen()
        elif event.key() == Qt.Key_D:
            # 'D' key pressed, set video directory
            self.setVideoDirectory()

    def setVideoDirectory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Video Directory", QDir.homePath())
        if directory:
            self.video_directory = directory
            self.refreshVideoPlayer()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.show()
    sys.exit(app.exec_())
