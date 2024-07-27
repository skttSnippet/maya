import maya.OpenMayaUI as omui_old

from shiboken2 import wrapInstance
from PySide2 import QtCore, QtGui, QtWidgets, QtUiTools

MAYA_WIN = wrapInstance(int(omui_old.MQtUtil.mainWindow()), QtWidgets.QWidget)

