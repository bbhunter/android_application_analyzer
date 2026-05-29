import sys
import os

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QFileDialog,
    QTreeView,
    QFileSystemModel,
    QSplitter,
    QStackedWidget,
    QMessageBox
)

from PySide6.QtCore import QSize, Qt

from GlobalVariables import *


class Gui(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(QSize(1200, 700))
        self.setWindowTitle("Android Application Analyzer")

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        rootLayout = QVBoxLayout(centralWidget)
        rootLayout.setContentsMargins(8, 8, 8, 8)
        rootLayout.setSpacing(6)

        quit_action = QtGui.QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        # ─────────────────────────────────────────────────────────────
        # Row 1 : Device | App | Reload | Hide Default Apps
        # ─────────────────────────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.device_lable = QLabel("Select Device")

        self.cmbDevice = QComboBox()
        self.cmbDevice.setObjectName("cmbDevice")
        self.cmbDevice.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.app_label = QLabel("Select Application")

        self.cmbApp = QComboBox()
        self.cmbApp.setObjectName("cmbApp")
        self.cmbApp.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.btnReloadApps = QPushButton("Reload")

        self.chkHideDefaultApp = QCheckBox("Hide Default Apps")

        row1.addWidget(self.device_lable)
        row1.addWidget(self.cmbDevice)

        row1.addSpacing(10)

        row1.addWidget(self.app_label)
        row1.addWidget(self.cmbApp)

        row1.addWidget(self.chkHideDefaultApp)

        row1.addSpacing(10)

        row1.addWidget(self.btnReloadApps)

        rootLayout.addLayout(row1)

        # ─────────────────────────────────────────────────────────────
        # Row 2 : Tool buttons
        # ─────────────────────────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.btnPullData = QPushButton("Pull App Data")
        self.btnJDGUI = QPushButton("jdgui")
        self.btnMobSF = QPushButton("mobSF")
        self.btnAPKTool = QPushButton("apktool")
        self.btnReinstall = QPushButton("re-install")
        self.btnFridaSSLUnPin = QPushButton("frida-sslunpin")
        self.btnFridump = QPushButton("fridump")

        self.chkURLDecode = QCheckBox("URL Decode")
        self.chkHtmlDecode = QCheckBox("HTML Decode")
        self.chkSplitConfig = QCheckBox("split-config")

        # NEW
        self.chkLogcat = QCheckBox("Logcat")
        self.chkLogcat.setChecked(True)

        # ------------------------------------------------------------
        # Standard Tool Group
        # ------------------------------------------------------------

        standardToolGroup = QGroupBox("Standard Tools")

        standardToolLayout = QHBoxLayout()
        standardToolLayout.setSpacing(4)
        standardToolLayout.setContentsMargins(6, 6, 6, 6)

        standardToolLayout.addWidget(self.btnAPKTool)
        standardToolLayout.addWidget(self.btnJDGUI)
        standardToolLayout.addWidget(self.btnMobSF)

        standardToolGroup.setLayout(standardToolLayout)

        row2.addWidget(standardToolGroup)

        # ------------------------------------------------------------
        # Frida Group
        # ------------------------------------------------------------

        fridaGroup = QGroupBox("Frida Scripts")

        fridaLayout = QHBoxLayout()
        fridaLayout.setSpacing(4)
        fridaLayout.setContentsMargins(6, 6, 6, 6)

        fridaLayout.addWidget(self.btnFridaSSLUnPin)
        fridaLayout.addWidget(self.btnFridump)

        fridaGroup.setLayout(fridaLayout)

        row2.addWidget(fridaGroup)

        # ------------------------------------------------------------
        # Re-install + Split Config Group
        # ------------------------------------------------------------
        reinstallGroup = QGroupBox("Install")

        reinstallLayout = QHBoxLayout()
        reinstallLayout.setSpacing(4)
        reinstallLayout.setContentsMargins(6, 6, 6, 6)

        reinstallLayout.addWidget(self.chkSplitConfig)
        reinstallLayout.addWidget(self.btnReinstall)

        reinstallGroup.setLayout(reinstallLayout)

        row2.addWidget(reinstallGroup)

        # ------------------------------------------------------------
        # Standard Tool Group
        # ------------------------------------------------------------

        logcatAndAppViewGroup = QGroupBox("App Data")

        logcatAndAppViewLayout = QHBoxLayout()
        logcatAndAppViewLayout.setSpacing(4)
        logcatAndAppViewLayout.setContentsMargins(6, 6, 6, 6)

        logcatAndAppViewLayout.addWidget(self.btnPullData)
        logcatAndAppViewLayout.addWidget(self.chkLogcat)

        logcatAndAppViewGroup.setLayout(logcatAndAppViewLayout)

        row2.addWidget(logcatAndAppViewGroup)
        # ------------------------------------------------------------

        row2.addStretch()

        rootLayout.addLayout(row2)

        # ─────────────────────────────────────────────────────────────
        # Title Row
        # ─────────────────────────────────────────────────────────────
        row3 = QHBoxLayout()

        self.lblFileContent = QLabel("Logcat Logs")

        row3.addWidget(self.lblFileContent)
        row3.addStretch()

        row3.addWidget(self.chkURLDecode)
        row3.addWidget(self.chkHtmlDecode)

        rootLayout.addLayout(row3)

        # ─────────────────────────────────────────────────────────────
        # STACK WIDGET
        # ─────────────────────────────────────────────────────────────
        self.stackWidget = QStackedWidget()

        # ============================================================
        # PAGE 1 : LOGCAT
        # ============================================================
        self.logcatPage = QWidget()

        logcatLayout = QVBoxLayout(self.logcatPage)
        logcatLayout.setContentsMargins(0, 0, 0, 0)

        self.txtLogcat = QTextEdit()

        self.txtLogcat.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        logcatLayout.addWidget(self.txtLogcat)

        self.stackWidget.addWidget(self.logcatPage)

        # ============================================================
        # PAGE 2 : FILE BROWSER
        # ============================================================
        self.fileBrowserPage = QWidget()

        fileLayout = QVBoxLayout(self.fileBrowserPage)
        fileLayout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        # ------------------------------------------------------------
        # FILE SYSTEM MODEL
        # ------------------------------------------------------------
        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath("")

        # ------------------------------------------------------------
        # LEFT SIDE : TREE VIEW
        # ------------------------------------------------------------
        self.treeView = QTreeView()
        self.treeView.setModel(self.fileModel)

        self.treeView.setAnimated(True)
        self.treeView.setIndentation(18)
        self.treeView.setSortingEnabled(True)

        # Hide unnecessary columns
        self.treeView.hideColumn(1)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)

        # ------------------------------------------------------------
        # RIGHT SIDE : FILE CONTENT
        # ------------------------------------------------------------
        self.txtFileContent = QTextEdit()
        self.txtFileContent.setReadOnly(True)

        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.txtFileContent)

        self.splitter.setSizes([350, 850])

        fileLayout.addWidget(self.splitter)

        self.stackWidget.addWidget(self.fileBrowserPage)

        # Default page
        self.stackWidget.setCurrentWidget(self.logcatPage)

        rootLayout.addWidget(self.stackWidget, 1)

    # ─────────────────────────────────────────────────────────────
    # Close Event
    # ─────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        GlobalVariables.isClose = True

        # Stop the logcat thread cleanly before the window is destroyed.
        # Without this Qt destroys the QThread object while it is still
        # running, causing: QThread: Destroyed while thread is still running
        if hasattr(self, '_logcat_thread') and self._logcat_thread is not None:
            self._logcat_thread.stop()
            self._logcat_thread.wait(5000)  # give it up to 5 s to finish
            self._logcat_thread = None

        event.accept()

    def FolderExistPopup(self):
        reply = QMessageBox.question(
            self,
            "Folder Exists",
            f"Folder already exists: Delete it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            return True
        return False

    def ShowDirectoryView(self, dirPath):
        # --------------------------------------------------------
        # SHOW FOLDER IN TREE VIEW
        # --------------------------------------------------------
        root_index = self.fileModel.index(dirPath)

        self.treeView.setRootIndex(root_index)

        # Switch to file browser page
        self.chkLogcat.setChecked(False)

        self.stackWidget.setCurrentWidget(
            self.fileBrowserPage
        )

        self.lblFileContent.setText(
            f"Browsing : {dirPath}"
        )