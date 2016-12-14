from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg


def make_slider(value, min, max, orientation):
    # Create a slider. Set slider value to value.
    # Use min and max as minimum and maximum values.
    # orientation: 'horizontal' or 'vertical'
    slider = QtGui.QSlider()
    if orientation == 'horizontal':
        slider.setOrientation(QtCore.Qt.Horizontal)
    elif orientation == 'vertical':
        slider.setOrientation(QtCore.Qt.Vertical)
    slider.setMaximum(max)
    slider.setMinimum(min)
    slider.setValue(value)
    return slider


def make_spinbox(value, step, decimals, integer, min, max):
    # Create a spinbox.
    spinbox = pg.SpinBox(
                        value=value,
                        step=step,
                        decimals=decimals,
                        integer=integer)
    spinbox.setMinimum(min)
    spinbox.setMaximum(max)
    return spinbox


def make_combobox(comboList):
    # Create a combo box including all items in comboList.
    combobox = QtGui.QComboBox()
    for l in comboList:
        combobox.addItem(l)
    return combobox


def make_popup_menu(label, parent, menuList, selected, callBack):
    # Create popup menu
    aBar = QtGui.QToolBar()
    aButton = QtGui.QToolButton()
    aButton.setText(label)
    aButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
    aMenu = QtGui.QMenu(parent)
    portMapping = QtCore.QSignalMapper(parent)
    portGroup = QtGui.QActionGroup(parent, exclusive=True)
    for i, item in enumerate(menuList):
        act = portGroup.addAction(QtGui.QAction(item, parent, checkable=True))
        if i == selected:
            act.setChecked(True)
        aMenu.addAction(act)
        portMapping.setMapping(act, i)
        act.triggered.connect(portMapping.map)
    portMapping.mapped[int].connect(callBack)
    aButton.setMenu(aMenu)
    aBar.addWidget(aButton)
    return aBar
