# simple GUI for demonstration purposes of autofocus functionality
# coding: utf-8

import pyqtgraph as pg
import numpy as np
import cv2
from pyqtgraph.Qt import QtCore, QtGui
import sys
import af_gui as afg
import gui_builder as gb
import peak_search_lense_final as psl


class AfDemo(QtGui.QWidget):
    def __init__(self, parent):
        # Constructor
        QtGui.QWidget.__init__(self, parent)
        # Create sub layouts:
        # Box with AOI controls.
        self.aoiBox = afg.AOIBox(self, 512, 512)
        # Box with autofocus controls.
        self.afBox = afg.AfBox(self, 0, 5000, 20, 10)
        self.cam_connected = False
        self.lense_init = False
        self.drawing = False
        # Box with camera controls.
        self.camControl = afg.CameraControlBox(self)
        # Box with lense controls.
        self.lenseControl = afg.LenseControlBox(self)
        self.afX = 0
        self.afY = 0
        self.afN = 0
        # Initialize gui.
        self.init_gui()

    def applyMouseCB(self):
        # Activate mous callback.
        cv2.setMouseCallback('Video', self.draw_aoi_mouse)

    def draw_aoi(self):
        # Draw rectangle on video to display selected AOI.
        cv2.rectangle(
                        self.camControl.currImg,
                        (self.aoiBox.x1, self.aoiBox.y1),
                        (self.aoiBox.x2, self.aoiBox.y2),
                        (255, 255, 255))

    def camConnection(self):
        # Callback for camera connection changes.
        if self.camControl.cam_connected:
            # If camera is connected get and display info from camera.
            self.cam_connected = True
            self.cam = self.camControl.cam
            w = self.cam.Width()
            h = self.cam.Height()
            self.aoiBox.maxX = w
            self.aoiBox.maxY = h
            self.aoiBox.x2 = w
            self.aoiBox.y2 = h
            self.aoiBox.x2Edit.setText(str(w))
            self.aoiBox.y2Edit.setText(str(h))
            # if lense has already been connected: enable autofocus.
            if self.lenseControl.lense_init:
                pass
                self.afBox.startBtn.setEnabled(True)
        else:
            self.cam_connected = False
            self.afBox.startBtn.setEnabled(False)

    def lenseConnection(self):
        # Callback for lense connection changes
        if self.lenseControl.lense_init:
            self.lense_init = True
            self.lc = self.lenseControl.lc
            if self.camControl.cam_connected:
                # If camera has already been connected: enable autofocus.
                self.afBox.startBtn.setEnabled(True)
        else:
            self.lense_init = False
            self.afBox.startBtn.setEnabled(False)

    def draw_aoi_mouse(self, event, x, y, flags, param):
        # Callback function for AOI selection by drag&drop an video screen.
        # If left button is clicked save starting point.
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.aoiBox.x1 = x
            self.aoiBox.y1 = y
            self.aoiBox.x1Edit.setText(str(x))
            self.aoiBox.y1Edit.setText(str(y))
        # While mouse is moving: update end point coordinates.
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.aoiBox.x2 = x
                self.aoiBox.y2 = y
                self.aoiBox.x2Edit.setText(str(x))
                self.aoiBox.y2Edit.setText(str(y))
        elif event == cv2.EVENT_LBUTTONUP:
            # When button is released: set AOI to a minimum of
            # at least 20x20 and save end point.
            self.drawing = False
            if abs(x - self.aoiBox.x1) <= 20:
                x = self.aoiBox.x1 + 20
            if abs(y - self.aoiBox.y1) <= 20:
                y = self.aoiBox.y1 + 20
            self.aoiBox.x2 = x
            self.aoiBox.y2 = y
            self.aoiBox.x2Edit.setText(str(x))
            self.aoiBox.y2Edit.setText(str(y))

    def start_af(self):
        # Callback to start autofocus.
        # Set cursor to 'busy'.
        QtGui.QApplication.setOverrideCursor(
                            QtGui.QCursor(QtCore.Qt.WaitCursor))
        # Disable GUI.
        self.setEnabled(False)
        # Get currently selected AOI coordinates.
        roi = [
                self.aoiBox.x1,
                self.aoiBox.y1,
                self.aoiBox.x2,
                self.aoiBox.y2]
        # Stop video.
        if self.camControl.video_running:
            self.camControl.videoTimer.stop()
        # Start selected autofocus algorithm.
        if self.afBox.algorithm == 0:
            # Global peak single step algorithm.
            self.afX, self.afY, self.afN = psl.global_peak_single_step(
                                                            self.cam,
                                                            self.lc.focus,
                                                            self.afBox.fStep,
                                                            self.afBox.start,
                                                            self.afBox.stop,
                                                            roi)
            self.afX -= self.afBox.hyst  # add hysteresis
        elif self.afBox.algorithm == 1:
            # Global peak two step algorithm.
            self.afX, self.afY, self.afN = psl.global_peak_two_step(
                                                            self.cam,
                                                            self.lc.focus,
                                                            self.afBox.cStep,
                                                            self.afBox.fStep,
                                                            self.afBox.start,
                                                            self.afBox.stop,
                                                            roi,
                                                            self.afBox.hyst)
            self.afX -= self.afBox.hyst  # add hysteresis
        elif self.afBox.algorithm == 2:
            # Fibonacci algorithm.
            self.afX, self.afY, self.afN = psl.fibonacci_peak(
                                                            self.cam,
                                                            self.lc.focus,
                                                            self.afBox.start,
                                                            self.afBox.stop,
                                                            roi,
                                                            self.afBox.hyst,
                                                            4)
        # Restart video.
        if self.camControl.video_running:
            self.camControl.videoTimer.start(30)
        self.setEnabled(True)
        # Set focus to calculated position.
        self.lc.focus.go_to_position(self.afX)
        self.lenseControl.focusSlider.setValue(self.afX)
        QtGui.QApplication.restoreOverrideCursor()

    def init_gui(self):
        # Initialize gui.
        self.setWindowTitle('Main')
        mainLayout = QtGui.QGridLayout(self)
        headerFont = QtGui.QFont()
        headerFont.setPointSize(12)
        headerFont.setBold(True)

        # Create some labels.
        lLabel = QtGui.QLabel("Lense Controls")
        lLabel.setFont(headerFont)
        cLabel = QtGui.QLabel("Camera Controls")
        cLabel.setFont(headerFont)
        sLabel = QtGui.QLabel("AOI Controls")
        sLabel.setFont(headerFont)
        aLabel = QtGui.QLabel("AF Controls")
        aLabel.setFont(headerFont)

        # Add labels to layout.
        mainLayout.addWidget(
                                cLabel,
                                0,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                self.camControl,
                                1,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                lLabel,
                                2,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                self.lenseControl,
                                3,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                sLabel,
                                4,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                self.aoiBox,
                                5,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                aLabel,
                                6,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        mainLayout.addWidget(
                                self.afBox,
                                7,
                                0,
                                1,
                                1,
                                alignment=QtCore.Qt.AlignLeft)

        # Connect signals from sub widgets to callback functions.
        self.camControl.connection_changed.connect(self.camConnection)
        self.lenseControl.connection_changed.connect(self.lenseConnection)
        self.camControl.new_frame.connect(self.draw_aoi)
        self.camControl.video_start.connect(self.applyMouseCB)
        self.afBox.af_started.connect(self.start_af)
        self.afBox.startBtn.setEnabled(False)

    def closeEvent(self, event):
        cv2.destroyAllWindows()


def main():
    app = QtGui.QApplication(sys.argv)
    win = AfDemo(None)
    win.show()
    app.exec_()

if __name__ == "__main__":
    main()
