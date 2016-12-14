import pyqtgraph as pg
import numpy as np
import cv2
import pypylon.pylon as py
import serial
from pyqtgraph.Qt import QtCore,  QtGui
import sys
import gui_builder as gb
import LenseController as af


def is_integer(s):
    # Check if a string represents an integer.
    try:
        int(s)
        return True
    except ValueError:
        return False


class CameraControlBox(QtGui.QWidget):
    '''
    Widget with simple camera controls:
    connect/disconnect cam
    start video/stop video
    slider to set exposure time
    '''
    # Create some signals to communicate with other widgets.
    connection_changed = QtCore.Signal()
    new_frame = QtCore.Signal()
    video_start = QtCore.Signal()
    video_stop = QtCore.Signal()

    def __init__(self,  parent):
        QtGui.QWidget.__init__(self,  parent)
        self.cam_connected = False
        self.video_running = False
        self.eMax = 200000
        self.eMin = 20
        self.init_gui()
        self.videoTimer = QtCore.QTimer()
        self.videoTimer.timeout.connect(self.update_video)

    def init_gui(self):
        # Initialize user interface.
        # Set sizes.
        self.setFixedWidth(300)
        self.setFixedHeight(100)
        sliderWidth = 200
        self.setWindowTitle('CameraControl')
        # Create main + sub layouts.
        mainLayout = QtGui.QGridLayout(self)
        btnLayout = QtGui.QGridLayout(self)
        expLayout = QtGui.QGridLayout(self)

        # Create Layout for cam connect/disconnect-
        # and video start/stop-buttons.
        # Button Layout Start++++++++++++++++++++++++++++
        # connect/disconnect-button
        self.connectBtn = QtGui.QPushButton("Connect Cam")
        # add callback function
        self.connectBtn.clicked.connect(self.connectDisconnectCam)
        # start/stop-video-button
        self.startStopBtn = QtGui.QPushButton("Start Video")
        # add callback function
        self.startStopBtn.clicked.connect(self.startStopVideo)
        self.startStopBtn.setEnabled(False)
        # Add Buttons to parent layout.
        btnLayout.addWidget(
                            self.connectBtn, 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        btnLayout.addWidget(
                            self.startStopBtn, 0, 1, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        # Button Layout Stop+++++++++++++++++++++++++++++

        # Create slider for exposure time.
        # Exposure Time Layout Start++++++++++++++++++++++++++++
        self.expSlider = gb.make_slider(
                                        self.eMin, self.eMin,
                                        self.eMax, 'horizontal')
        self.expSlider.setFixedWidth(sliderWidth)
        self.expSlider.setEnabled(False)
        self.expSlider.valueChanged.connect(self.slider_CB)
        self.expEdit = QtGui.QLineEdit('10')
        self.expEdit.setEnabled(False)
        # add callback function
        self.expEdit.returnPressed.connect(self.edit_CB)
        expLayout.addWidget(
                            self.expSlider, 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        expLayout.addWidget(
                            self.expEdit, 0, 1, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        # Exposure Time Layout Stop++++++++++++++++++++++++++++

        # Add sub layouts to main layout.
        mainLayout.addLayout(
                                btnLayout, 0, 0, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        mainLayout.addLayout(
                                expLayout, 1, 0, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)

    def startStopVideo(self):
        # Function that starts and stops video.
        if self.video_running:
            # if video is running:
            # stop timer
            self.videoTimer.stop()
            # emit video stopped signal
            self.video_stop.emit()
            # reset button text
            self.startStopBtn.setText('Start Video')
            self.video_running = False
            # enable connect/disconnect-button
            self.connectBtn.setEnabled(True)
            # destroy video window
            cv2.destroyAllWindows()
        else:
            # if video is not running:
            # create video window
            cv2.namedWindow("Video")
            # start timer
            self.videoTimer.start(30)
            # emit video start signal
            self.video_start.emit()
            # set start/stop-button text to "Stop Video"
            self.startStopBtn.setText('Stop Video')
            # disable connect/disconnect-button
            self.connectBtn.setEnabled(False)
            self.video_running = True

    def edit_CB(self):
        # Callback function for exposure time text edit
        # Check if input is integer.
        if is_integer(self.expEdit.text()):
            # Cast input to integer.
            T = int(self.expEdit.text())
            # Check if value is within exposure time
            # limits and set slider value accordingly.
            if T >= self.eMin and T <= self.eMax:
                self.cam.ExposureTime = T
                self.expSlider.setValue(T)
        else:
            # If input is no integer,  reset text to last
            # valid input (slider value).
            self.expEdit.setText(str(self.expSlider.value()))

    def slider_CB(self):
        # Callback function for exposure time slider
        # Get current slider value.
        T = self.expSlider.value()
        # Set edit text to slider value.
        self.expEdit.setText(str(T))
        # Set cam exposure time to current value.
        self.cam.ExposureTime = T

    def update_video(self):
        # Update current image in video window.
        # Grab one image.
        img = np.zeros((1, 1))
        if self.cam.NumReadyBuffers:
            res = self.cam.RetrieveResult(1000)
            if res:
                try:
                    if res.GrabSucceeded():
                        img = res.Array
                finally:
                    res.Release()
        # Save last image.
        self.currImg = img
        # Emit new frame signal.
        self.new_frame.emit()
        # Display new image in video window.
        cv2.imshow('Video', self.currImg)
        # Wait    1 ms.
        cv2.waitKey(1)

    def connectDisconnectCam(self):
        # Callback for connect/disconnect cam button.
        # If cam is connected: disconnect cam.
        if self.cam_connected:
            try:
                # Close cam.
                self.cam.Close()
                # Reset button text.
                self.connectBtn.setText('Connect Cam')
                # Disable video button.
                self.startStopBtn.setEnabled(False)
                self.cam_connected = False
                # Disable slider and text edit for exposure time.
                self.expEdit.setEnabled(False)
                self.expSlider.setEnabled(False)
            except:
                # If an error occured: display message box.
                msgBox = QtGui.QMessageBox()
                msgBox.setText("Cam Connection Error")
                msgBox.exec_()
        # If no cam is connected: try to connect to first device.
        else:
            try:
                # Try to create InstantCamera object from first device.
                self.cam = py.InstantCamera(
                        py.TlFactory.GetInstance().CreateFirstDevice())
                # Open cam.
                self.cam.Open()
                # Disable auto exposure.
                self.cam.ExposureAuto = "Off"
                # Disable auto gain.
                self.cam.GainAuto = "Off"
                # Get current exposure time.
                T = int(self.cam.ExposureTime())
                # Set exposure time text edit to current exposure time value.
                self.expEdit.setText(str(T))
                # Check if exposure time is within limits and
                # set slider and cam exposure time accordingly.
                if T > self.eMax:
                    self.expSlider.setValue(self.eMax)
                    self.cam.ExposureTime = self.eMax
                else:
                    self.expSlider.setValue(T)
                # Set button text to "Disconnect Cam".
                self.connectBtn.setText('Disconnect Cam')
                self.cam_connected = True
                # Enable start/stop-video-button.
                self.startStopBtn.setEnabled(True)
                # Enable text edit and slider for exposure time.
                self.expEdit.setEnabled(True)
                self.expSlider.setEnabled(True)
                self.cam.StartGrabbing(py.GrabStrategy_LatestImages)
            except:
                # Catch connection error with message box.
                msgBox = QtGui.QMessageBox()
                msgBox.setText("Cam Connection Error")
                msgBox.exec_()
        # Emit connection changed signal.
        self.connection_changed.emit()

    def closeEvent(self,  event):
        # On window close event: Destroy video window and close cam.
        cv2.destroyAllWindows()
        if self.cam_connected:
            self.cam.StopGrabbing()
            self.cam.Close()


class LenseControlBox(QtGui.QWidget):
    '''Widget with simple controls for zoom,  iris and focus motors
    '''
    # Create signal to let other widgets know,
    # that the lense connection status changed.
    connection_changed = QtCore.Signal()

    def init_gui(self):
        # Initialize user interface.
        gotoText = "Submit"
        sliderWidth = 250
        iMax = 100
        zMax = 500
        fMax = 500
        iMin = 0
        zMin = 0
        fMin = 0
        iPos = 0
        zPos = 0
        fPos = 0
        # Set size.
        self.setFixedWidth(700)
        self.setFixedHeight(200)
        # Set window title.
        self.setWindowTitle('LenseControl')
        # Create main layout.
        mainLayout = QtGui.QGridLayout(self)

        # Create layout for init-buttons.
        initLayout = QtGui.QGridLayout(self)
        # Create button to init all motors at the same time.
        self.initBtn = QtGui.QPushButton("Init Lense")
        self.initBtn.clicked.connect(self.init_all_motors)
        # Add init button to initLayout.
        initLayout.addWidget(
                            self.initBtn, 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        # Create parent lyout for iris,  zoom and focus layouts.
        ifzLayout = QtGui.QGridLayout(self)

        # Create iris controls layout.
        # Iris control start +++++++++++++++++++++++++++++++++++++++++++
        # Create iris slider,  set size and connect callback.
        isliderLayout = QtGui.QGridLayout(self)
        self.irisSlider = gb.make_slider(iPos, iMin, iMax, 'horizontal')
        self.irisSlider.valueChanged.connect(self.iSliderCB)
        self.irisSlider.setFixedWidth(sliderWidth)
        # Create labels.
        self.iLabel = QtGui.QLabel(str(iPos))
        self.imaxLabel = QtGui.QLabel(str(iMax))
        self.iminLabel = QtGui.QLabel(str(iMin))
        # Add elements to iris slider layout.
        isliderLayout.addWidget(
                                self.iLabel, 0, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        isliderLayout.addWidget(
                                self.irisSlider, 1, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        isliderLayout.addWidget(
                                self.iminLabel, 1, 0, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        isliderLayout.addWidget(
                                self.imaxLabel, 1, 2, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        # Create additional controls.
        # 'Go to' - button
        self.iGotoBtn = QtGui.QPushButton(gotoText)
        self.iGotoBtn.clicked.connect(self.iGoTo)
        # 'Enable' - checkbox
        self.iCheck = QtGui.QCheckBox('Enable')
        self.iCheck.setCheckState(QtCore.Qt.Checked)
        self.iCheck.setTristate(False)
        self.iCheck.stateChanged.connect(self.iEnableCB)
        # 'Init' - button
        self.iInitBtn = QtGui.QPushButton('Init')
        self.iInitBtn.clicked.connect(self.iInit)
        # Add iris controls to parent layout.
        ifzLayout.addWidget(
                                QtGui.QLabel("Iris :"), 0, 0,
                                1, 1, alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addLayout(
                                isliderLayout, 0, 1, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                                self.iGotoBtn, 0, 2, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                                self.iCheck, 0, 3, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                                self.iInitBtn, 0, 4, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        # Iris control stop +++++++++++++++++++++++++++++++++++++++++++

        # Create zoom controls layout.
        # Zoom control start +++++++++++++++++++++++++++++++++++++++++++
        # Create zoom slider,  set size and connect callback.
        zsliderLayout = QtGui.QGridLayout(self)
        self.zoomSlider = gb.make_slider(zPos, zMin, zMax, 'horizontal')
        self.zoomSlider.valueChanged.connect(self.zSliderCB)
        self.zoomSlider.setFixedWidth(sliderWidth)
        # Create labels.
        self.zLabel = QtGui.QLabel(str(zPos))
        self.zmaxLabel = QtGui.QLabel(str(zMax))
        self.zminLabel = QtGui.QLabel(str(zMin))
        # Add elements to zoom slider layout.
        zsliderLayout.addWidget(
                                self.zLabel, 0, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        zsliderLayout.addWidget(
                                self.zoomSlider, 1, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        zsliderLayout.addWidget(
                                self.zminLabel, 1, 0, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        zsliderLayout.addWidget(
                                self.zmaxLabel, 1, 2, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        # Create additional controls.
        # 'Go to' - button
        self.zGotoBtn = QtGui.QPushButton(gotoText)
        self.zGotoBtn.clicked.connect(self.zGoTo)
        # 'Enable' - checkbox
        self.zCheck = QtGui.QCheckBox('Enable')
        self.zCheck.setCheckState(QtCore.Qt.Checked)
        self.zCheck.setTristate(False)
        self.zCheck.stateChanged.connect(self.zEnableCB)
        # 'Init' - button
        self.zInitBtn = QtGui.QPushButton('Init')
        self.zInitBtn.clicked.connect(self.zInit)
        # Add zoom controls to parent layout.
        ifzLayout.addWidget(
                            QtGui.QLabel("Zoom :"), 1, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addLayout(
                            zsliderLayout, 1, 1, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                            self.zGotoBtn, 1, 2, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                            self.zCheck, 1, 3, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        ifzLayout.addWidget(
                            self.zInitBtn, 1, 4, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        # Zoom control stop +++++++++++++++++++++++++++++++++++++++++++

        # Create focus controls layout.
        # Focus control start +++++++++++++++++++++++++++++++++++++++++++
        # Create focus slider,  set size and connect callback.
        fsliderLayout = QtGui.QGridLayout(self)
        self.focusSlider = gb.make_slider(fPos, fMin, fMax, 'horizontal')
        self.focusSlider.valueChanged.connect(self.fSliderCB)
        self.focusSlider.setFixedWidth(sliderWidth)
        # Create labels.
        self.fLabel = QtGui.QLabel(str(fPos))
        self.fmaxLabel = QtGui.QLabel(str(fMax))
        self.fminLabel = QtGui.QLabel(str(fMin))
        # Add elements to focus slider layout.
        fsliderLayout.addWidget(
                                self.fLabel, 0, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        fsliderLayout.addWidget(
                                self.focusSlider, 1, 1, 1, 1,
                                alignment=QtCore.Qt.AlignCenter)
        fsliderLayout.addWidget(
                                self.fminLabel, 1, 0, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        fsliderLayout.addWidget(
                                self.fmaxLabel, 1, 2, 1, 1,
                                alignment=QtCore.Qt.AlignLeft)
        # Create additional controls.
        # 'Go to' - button
        self.fGotoBtn = QtGui.QPushButton(gotoText)
        self.fGotoBtn.clicked.connect(self.fGoTo)
        # 'Enable' - checkbox
        self.fCheck = QtGui.QCheckBox('Enable')
        self.fCheck.setCheckState(QtCore.Qt.Checked)
        self.fCheck.setTristate(False)
        self.fCheck.stateChanged.connect(self.fEnableCB)
        # 'Init' - button
        self.fInitBtn = QtGui.QPushButton('Init')
        self.fInitBtn.clicked.connect(self.fInit)
        # Add focus controls to parent layout.
        ifzLayout.addWidget(
                            QtGui.QLabel("Focus :"),
                            2,
                            0,
                            1,
                            1,
                            alignment=QtCore.Qt.AlignLeft
                            )
        ifzLayout.addLayout(
                            fsliderLayout,
                            2,
                            1,
                            1,
                            1,
                            alignment=QtCore.Qt.AlignLeft
                            )
        ifzLayout.addWidget(
                            self.fGotoBtn,
                            2,
                            2,
                            1,
                            1,
                            alignment=QtCore.Qt.AlignLeft
                            )
        ifzLayout.addWidget(
                            self.fCheck,
                            2,
                            3,
                            1,
                            1,
                            alignment=QtCore.Qt.AlignLeft
                            )
        ifzLayout.addWidget(
                            self.fInitBtn,
                            2,
                            4,
                            1,
                            1,
                            alignment=QtCore.Qt.AlignLeft
                            )
        # Focus control stop +++++++++++++++++++++++++++++++++++++++++++
        # Set spacing.
        ifzLayout.setVerticalSpacing(20)
        # Group 'Go to'-,  'Init'-buttons and checkboxes for easier access.
        self.gotoBtns = [self.iGotoBtn, self.zGotoBtn, self.fGotoBtn]
        self.initBtns = [self.iInitBtn, self.zInitBtn, self.fInitBtn]
        self.checkBoxes = [self.iCheck, self.zCheck, self.fCheck]
        # Disable all buttons and checkboxes.
        for i in range(3):
            self.gotoBtns[i].setEnabled(False)
            self.checkBoxes[i].setEnabled(False)
            self.initBtns[i].setEnabled(False)
        # Add sub layouts to main layout.
        mainLayout.addLayout(
                                initLayout,
                                0,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft
                                )
        mainLayout.addLayout(
                                ifzLayout,
                                1,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft
                                )

    def iInit(self):
        # Callback for iris init button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable button.
        self.setEnabled(False)
        # Send init command to iris motor.
        self.lc.iris.init_motor()
        # Enable button.
        self.setEnabled(True)
        # Reset iris slider value.
        self.irisSlider.setValue(0)
        # Restore cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def zInit(self):
        # Callback for zoom init button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable button.
        self.setEnabled(False)
        # Send init command to zoom motor.
        self.lc.zoom.init_motor()
        # Enable button.
        self.setEnabled(True)
        # Reset zoom slider value.
        self.zoomSlider.setValue(0)
        # Restore cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def fInit(self):
        # Callback for focus init button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable button.
        self.setEnabled(False)
        # Send init command to focus motor.
        self.lc.focus.init_motor()
        # Enable button.
        self.setEnabled(True)
        # Reset focus slider value.
        self.focusSlider.setValue(0)
        # Restore cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def iSliderCB(self):
        # Iris slider callback.
        # Set iris text edit text to slider value.
        self.iLabel.setText(str(self.irisSlider.value()))

    def zSliderCB(self):
        # Zoom slider callback.
        # Set zoom text edit text to slider value.
        self.zLabel.setText(str(self.zoomSlider.value()))

    def fSliderCB(self):
        # Focus slider callback.
        # Set focus text edit text to slider value.
        self.fLabel.setText(str(self.focusSlider.value()))

    def init_all_motors(self):
        # Initialize all motors.
        # Disable widget.
        self.setEnabled(False)
        # Create LenseController object.
        self.lc = af.LenseController()
        # Open controller.
        self.lc.open()
        # Enable widget.
        self.setEnabled(True)
        self.lense_init = True
        # Reset slider values to zero.
        self.zoomSlider.setValue(0)
        self.focusSlider.setValue(0)
        self.irisSlider.setValue(0)
        # Enable all buttons.
        for i in range(3):
            self.gotoBtns[i].setEnabled(True)
            self.checkBoxes[i].setEnabled(True)
            self.initBtns[i].setEnabled(True)
        # Get lense info.
        info = self.lc.get_lense_info()
        # Set slider values according to info.
        self.irisSlider.setMinimum(info[0])
        self.zoomSlider.setMinimum(info[1])
        self.focusSlider.setMinimum(info[2])
        self.irisSlider.setMaximum(info[6])
        self.zoomSlider.setMaximum(info[7])
        self.focusSlider.setMaximum(info[8])
        self.irisSlider.setValue(info[3])
        self.zoomSlider.setValue(info[4])
        self.focusSlider.setValue(info[5])
        # Set labels according to info
        self.iminLabel.setText(str(info[0]))
        self.zminLabel.setText(str(info[1]))
        self.fminLabel.setText(str(info[2]))
        self.iLabel.setText(str(info[3]))
        self.zLabel.setText(str(info[4]))
        self.fLabel.setText(str(info[5]))
        self.imaxLabel.setText(str(info[6]))
        self.zmaxLabel.setText(str(info[7]))
        self.fmaxLabel.setText(str(info[8]))
        # Emit connection change signal.
        self.connection_changed.emit()

    def iGoTo(self):
        # Callback for iris 'got to'-button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable widget.
        self.setEnabled(False)
        # Send 'go to'-command to lense.
        self.lc.iris.go_to_position(self.irisSlider.value())
        # Enable widget.
        self.setEnabled(True)
        # Reset cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def iEnableCB(self):
        # Iris enable-checkbox-callback.
        if self.iCheck.isChecked():
            # Send enable command.
            self.lc.iris.enable()
        else:
            # Send disable command.
            self.lc.iris.disable()

    def fEnableCB(self):
        # Focus enable-checkbox-callback.
        if self.fCheck.isChecked():
            # Send enable command.
            self.lc.focus.enable()
        else:
            # Send disable command.
            self.lc.focus.disable()

    def zEnableCB(self):
        # Zoom enable-checkbox-callback.
        if self.zCheck.isChecked():
            # Send enable command.
            self.lc.zoom.enable()
        else:
            # Send disable command.
            self.lc.zoom.disable()

    def zGoTo(self):
        # Callback for zoom 'got to'-button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable widget.
        self.setEnabled(False)
        # Send 'go to'-command to lense.
        self.lc.zoom.go_to_position(self.zoomSlider.value())
        # Enable widget.
        self.setEnabled(True)
        # Reset cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def fGoTo(self):
        # Callback for focus 'got to'-button.
        # Set cursor to 'busy'-cursor.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor)
                            )
        # Disable widget.
        self.setEnabled(False)
        # Send 'go to'-command to lense.
        self.lc.focus.go_to_position(self.focusSlider.value())
        # Enable widget.
        self.setEnabled(True)
        # Reset cursor.
        QtGui.QApplication.restoreOverrideCursor()

    def __init__(self, parent):
        # Constructor
        QtGui.QWidget.__init__(self, parent)
        self.lense_init = False
        self.init_gui()

    def closeEvent(self,  event):
        # on window close event:
        # close LenseController
        self.lc.close()


class SweepBox(QtGui.QWidget):
    sweep_started = QtCore.Signal()

    def __init__(self, parent, defaultPath):
        QtGui.QWidget.__init__(self, parent)
        self.defaultPath = defaultPath
        self.init_gui()

    def start_sweep(self):
        self.name = self.nameEdit.text()
        start = int(self.startSpin.value())
        stop = int(self.stopSpin.value())
        step = int(self.stepSpin.value())
        if stop > start:
            self.pos = np.arange(start, stop+step, step)
        elif stop < start:
            self.pos = np.arange(start, stop-step, -1*step)
        self.path = self.pathEdit.text()
        self.sweep_started.emit()

    def init_gui(self):
        pathWidth = 200
        self.setFixedWidth(300)
        self.setFixedHeight(200)
        self.setWindowTitle('Sweep')
        mainLayout = QtGui.QGridLayout(self)

        # EDIT LAYOUT
        editLayout = QtGui.QGridLayout(self)
        self.nameEdit = QtGui.QLineEdit()
        self.pathEdit = QtGui.QLineEdit(self.defaultPath)
        self.pathEdit.setFixedWidth(pathWidth)
        self.startSpin = gb.make_spinbox(0, 100, 0, True, 0, 5000)
        self.stopSpin = gb.make_spinbox(5000, 100, 0, True, 0, 5000)
        self.stepSpin = gb.make_spinbox(500, 10, 0, True, 0, 2500)
        self.startBtn = QtGui.QPushButton("Start Sweep")
        self.startBtn.clicked.connect(self.start_sweep)
        editLayout.addWidget(
                    QtGui.QLabel("Name: "),
                    0,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.nameEdit,
                    0,
                    1,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    QtGui.QLabel("Save Path: "),
                    1,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.pathEdit,
                    1,
                    1,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    QtGui.QLabel("Start"),
                    2,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    QtGui.QLabel("Stop"),
                    3,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    QtGui.QLabel("Step"),
                    4,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.startSpin,
                    2,
                    1,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.stopSpin,
                    3,
                    1,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.stepSpin,
                    4,
                    1,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        editLayout.addWidget(
                    self.startBtn,
                    5,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )
        mainLayout.addLayout(
                    editLayout,
                    0,
                    0,
                    1,
                    1,
                    alignment=QtCore.Qt.AlignLeft
                    )


def set_to_min_max(s, minS, maxS, def_value):
    # Check if integer value of string s is inside
    # the range of minS and maxS.
    # If not, clip to minS or maxS.
    if is_integer(s):
        x = int(s)
        if x < minS:
            x = minS
        elif x > maxS:
            x = maxS
        return x
    else:
        return def_value


class AOIBox(QtGui.QWidget):
    '''Widget with simple controls to select AOI.
    '''
    aoi_changed = QtCore.Signal()

    def __init__(self, parent, maxX, maxY):
        # Constructor
        QtGui.QWidget.__init__(self, parent)
        self.maxX = maxX
        self.maxY = maxY
        self.x1 = 0
        self.y1 = 0
        self.x2 = maxX
        self.y2 = maxY
        self.init_gui()

    def aoiCB(self):
        # Callback for changes in any of the AOI text edit fields.
        self.x1 = set_to_min_max(self.x1Edit.text(), 0, self.maxX, 0)
        self.x2 = set_to_min_max(self.x2Edit.text(), 0, self.maxX, 0)
        self.y1 = set_to_min_max(self.y1Edit.text(), 0, self.maxY, 0)
        self.y2 = set_to_min_max(self.y2Edit.text(), 0, self.maxY, 0)
        self.x1Edit.setText(str(self.x1))
        self.y1Edit.setText(str(self.y1))
        self.x2Edit.setText(str(self.x2))
        self.y2Edit.setText(str(self.y2))
        self.aoi_changed.emit()

    def init_gui(self):
        # Initialize user interface.
        self.setWindowTitle('AOIControls')
        mainLayout = QtGui.QGridLayout(self)

        # Controls for AOI Point 1
        p1Layout = QtGui.QGridLayout(self)
        p1Layout.addWidget(
                            QtGui.QLabel("P1: "), 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        p1Layout.addWidget(
                            QtGui.QLabel("x1: "), 0, 1, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        self.x1Edit = QtGui.QLineEdit()
        self.x1Edit.setText(str(0))
        p1Layout.addWidget(
                            self.x1Edit, 0, 2, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        p1Layout.addWidget(
                            QtGui.QLabel("y1: "), 0, 3, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        self.y1Edit = QtGui.QLineEdit()
        self.y1Edit.setText(str(0))
        p1Layout.addWidget(
                            self.y1Edit, 0, 4, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)

        # Controls for AOI Point 2
        p2Layout = QtGui.QGridLayout(self)
        p2Layout.addWidget(
                            QtGui.QLabel("P2: "), 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        p2Layout.addWidget(
                            QtGui.QLabel("x2: "), 0, 1, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        self.x2Edit = QtGui.QLineEdit()
        self.x2Edit.setText(str(self.maxX))
        p2Layout.addWidget(
                            self.x2Edit, 0, 2, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        p2Layout.addWidget(
                            QtGui.QLabel("y2: "), 0, 3, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        self.y2Edit = QtGui.QLineEdit()
        self.y2Edit.setText(str(self.maxY))
        p2Layout.addWidget(
                            self.y2Edit, 0, 4, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)

        # callbacks
        allEdits = [self.x1Edit, self.y1Edit, self.x2Edit, self.y2Edit]
        for edit in allEdits:
            edit.returnPressed.connect(self.aoiCB)

        mainLayout.addLayout(
                            p1Layout, 0, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)
        mainLayout.addLayout(
                            p2Layout, 1, 0, 1, 1,
                            alignment=QtCore.Qt.AlignLeft)


class AfBox(QtGui.QWidget):
    '''Widget with simple controls to select Autofocus-algorithm.
    '''
    # Create signal to inform other widgets,
    # that the autofocus is in progress.
    af_started = QtCore.Signal()

    def __init__(self, parent, minF, maxF, cStepMin, fStepMin):
        # Constructor
        QtGui.QWidget.__init__(self, parent)
        self.hyst = 0
        self.minF = minF
        self.maxF = maxF
        self.start = minF
        self.stop = maxF
        self.cStepMin = cStepMin
        self.cStep = cStepMin
        self.fStepMin = fStepMin
        self.fStep = fStepMin
        self.algorithm = 0
        self.init_gui()

    def update_af_edits(self, index):
        # Update (enable/disable) text edit fields
        # when algorithm selection is changed.
        self.algorithm = index
        if index == 0:
            self.pCStepEdit.setEnabled(False)
            self.pFStepEdit.setEnabled(True)
        elif index == 1:
            self.pCStepEdit.setEnabled(True)
            self.pFStepEdit.setEnabled(True)
        elif index == 2:
            self.pCStepEdit.setEnabled(False)
            self.pFStepEdit.setEnabled(False)

    def start_af(self):
        # Start autofocus.
        # Get focus start postion.
        start = set_to_min_max(
                        self.pStartEdit.text(), self.minF,
                        self.maxF, self.minF)
        # Get focus stop postion.
        stop = set_to_min_max(
                        self.pStopEdit.text(), self.minF,
                        self.maxF, self.maxF)
        # Correct invalid entries.
        if start == stop:
            start = self.minF
        if start == stop:
            stop = self.maxF
        # Check if start and stop are valid. Display message box if not.
        if start > stop:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Start Value must not be higher than Stop value!")
            msgBox.exec_()
        else:
            # Get coarse step from text edit.
            cStep = set_to_min_max(
                            self.pCStepEdit.text(), self.cStepMin,
                            round(abs(stop-start)/2.0), self.cStepMin)
            # Get fine step from text edit.
            fStep = set_to_min_max(
                            self.pFStepEdit.text(), self.fStepMin,
                            round(cStep/2.0), self.fStepMin)
            # Clip fine step to minimum step size.
            if fStep < self.fStepMin:
                fStep = self.fStepMin
            # Get hysteresis input.
            self.hyst = set_to_min_max(self.hystEdit.text(), -1000, 1000, 0)
            self.start = start
            self.stop = stop
            self.cStep = cStep
            self.fStep = fStep
            # Show corrected values in text edit fields.
            self.pStartEdit.setText(str(start))
            self.pStopEdit.setText(str(stop))
            self.pCStepEdit.setText(str(cStep))
            self.pFStepEdit.setText(str(fStep))
            self.af_started.emit()

    def init_gui(self):
        # Initialize GUI.
        # Create main and sub layout.
        mainLayout = QtGui.QGridLayout(self)
        leftLayout = QtGui.QGridLayout(self)

        # Create dropdown lit for algorithm selection.
        algList = [
                    "Global Peak Single Step",
                    "Global Peak Two Step",
                    "Fibonacci Peak"]
        self.algBox = gb.make_combobox(algList)
        self.connect(
                self.algBox, QtCore.SIGNAL('currentIndexChanged(int)'),
                self.update_af_edits)
        # Create start autofocus button.
        self.startBtn = QtGui.QPushButton("Start AF")
        self.startBtn.clicked.connect(self.start_af)
        # Add newly created widgets to layout.
        leftLayout.addWidget(
                        self.algBox, 0, 0, 1, 1,
                        alignment=QtCore.Qt.AlignLeft)
        leftLayout.addWidget(
                        self.startBtn, 1, 0, 1, 1,
                        alignment=QtCore.Qt.AlignLeft)

        # Create layout for edit fields.
        pSubLayout = QtGui.QGridLayout(self)
        self.pStartEdit = QtGui.QLineEdit()
        self.pStartEdit.setText(str(self.minF))
        self.pStopEdit = QtGui.QLineEdit()
        self.pStopEdit.setText(str(self.maxF))
        self.pCStepEdit = QtGui.QLineEdit()
        self.pCStepEdit.setText(str(self.cStep))
        self.pFStepEdit = QtGui.QLineEdit()
        self.pFStepEdit.setText(str(self.fStep))
        self.pStartEdit.setEnabled(True)
        self.pStopEdit.setEnabled(True)
        self.pCStepEdit.setEnabled(False)
        self.pFStepEdit.setEnabled(True)

        # Add edit widgets to sub layout.
        pSubLayout.addWidget(
                    QtGui.QLabel("Start:"), 0, 0, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    self.pStartEdit, 0, 1, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    QtGui.QLabel("Stop:"), 0, 2, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    self.pStopEdit, 0, 3, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    QtGui.QLabel("Coarse Step:"), 1, 0, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    self.pCStepEdit, 1, 1, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    QtGui.QLabel("Fine Step:"), 1, 2, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        pSubLayout.addWidget(
                    self.pFStepEdit, 1, 3, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)

        # Create hysteresis edit field.
        self.hystEdit = QtGui.QLineEdit()
        self.hystEdit.setText(str(40))

        # Add labels.
        mainLayout.addWidget(
                    QtGui.QLabel("Algorithm:"), 0, 0, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        mainLayout.addWidget(
                    QtGui.QLabel("Parameters:"), 0, 1, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        mainLayout.addWidget(
                    QtGui.QLabel("Hysteresis:"), 0, 2, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        # Add sub layouts.
        mainLayout.addLayout(
                    leftLayout, 1, 0, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        mainLayout.addLayout(
                    pSubLayout, 1, 1, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
        mainLayout.addWidget(
                    self.hystEdit, 1, 2, 1, 1,
                    alignment=QtCore.Qt.AlignLeft)
