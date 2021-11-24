# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ObjectContainer.ui'
#
# Created: Tue Aug 27 19:18:25 2013
#      by: qtpy UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from qtpy import QtCore, QtWidgets, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ObjectContainer(object):
    def setupUi(self, ObjectContainer):
        ObjectContainer.setObjectName(_fromUtf8("ObjectContainer"))
        ObjectContainer.resize(317, 426)
        self.verticalLayout = QtWidgets.QVBoxLayout(ObjectContainer)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(5, 5, 5, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.ObjectHeader = QtWidgets.QWidget(ObjectContainer)
        self.ObjectHeader.setObjectName(_fromUtf8("ObjectHeader"))
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.ObjectHeader)
        self.horizontalLayout.setContentsMargins(0,0,0,0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.buttonFold = QtWidgets.QToolButton(self.ObjectHeader)
        self.buttonFold.setMaximumSize(QtCore.QSize(20, 20))
        self.buttonFold.setCheckable(False)
        self.buttonFold.setChecked(False)
        self.buttonFold.setObjectName(_fromUtf8("buttonFold"))
        self.horizontalLayout.addWidget(self.buttonFold)
        self.labelName = QtWidgets.QLabel(self.ObjectHeader)
        self.labelName.setObjectName(_fromUtf8("labelName"))
        self.horizontalLayout.addWidget(self.labelName)
        self.verticalLayout.addWidget(self.ObjectHeader)
        self.container = QtWidgets.QWidget(ObjectContainer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.container.sizePolicy().hasHeightForWidth())
        self.container.setSizePolicy(sizePolicy)
        self.container.setObjectName(_fromUtf8("container"))
        self.verticalLayout.addWidget(self.container)

        self.retranslateUi(ObjectContainer)
        QtCore.QMetaObject.connectSlotsByName(ObjectContainer)

    def retranslateUi(self, ObjectContainer):
        ObjectContainer.setWindowTitle(QtWidgets.QApplication.translate("ObjectContainer", "Form", None ))
        self.buttonFold.setText(QtWidgets.QApplication.translate("ObjectContainer", "+", None ))
        self.labelName.setText(QtWidgets.QApplication.translate("ObjectContainer", "TextLabel", None ))

