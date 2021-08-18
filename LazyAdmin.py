import codecs
import os
import sys
import socket
import time
import json
import traceback
import win32con
import win32evtlog
import win32evtlogutil
import winerror
from PyQt5 import QtCore, QtWidgets, QtGui
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import QApplication
from monitor_windows import *
from form_server import Ui_Dialog
from list_server import ListServer
from model import Model

from monitor_windows import Ui_Monitor


class LazyMonitor(QtWidgets.QMainWindow):
    def resizeEvent(self, event):
        AppSize = self.geometry()
        self.ui.tabWidgets.setGeometry(QtCore.QRect(10, 10, AppSize.width() - 18, AppSize.height()))
        self.ui.GB_DB_TD.setGeometry(QtCore.QRect(320, 10, AppSize.width() - 355, AppSize.height() - 100))
        self.ui.GB_LS_TD.setGeometry(QtCore.QRect(10, 10, 300, AppSize.height() - 100))
        self.ui.GB_PS_TP.setGeometry(QtCore.QRect(10, 10, 360, AppSize.height() - 100))
        self.LSD.setGeometry(QtCore.QRect(0, 10, 300, AppSize.height() - 110))
        self.LSP.setGeometry(QtCore.QRect(0, 65, 360, AppSize.height() - 165))
        QtWidgets.QMainWindow.resizeEvent(self, event)

    def __init__(self):
        super().__init__()
        self.initUI()
        styleFile = "css/style.css"
        styleSheetStr = open(styleFile, "r").read()
        self.setStyleSheet(styleSheetStr)
        with open(os.path.realpath("config.json")) as config_file:
            data = json.load(config_file)
            self.salt = data['salt']

    def initUI(self):
        self.ui = Ui_Monitor()
        self.ui.setupUi(self)
        self.LSD = ListServer()
        self.LSP = ListServer()
        self.LSP.setupUi()
        self.LSP.setParent(self.ui.GB_PS_TP)
        self.LSD.mode = 'list'
        self.LSD.setupUi()
        self.LSD.setParent(self.ui.GB_LS_TD)
        self.ui.add_server.clicked.connect(self.add_server)
        self.ui.delete_server.clicked.connect(self.delete_server)
        self.ui.editDbConnect.clicked.connect(lambda: self.changeEditFormDB(True))
        self.ui.saveDbConnect.clicked.connect(lambda: self.changeEditFormDB(False))
        self.ui.checkDbConnect.clicked.connect(lambda: self.db.checkConnect(self.ui))
        self.loadSettings()
        self.setWindowTitle("Lazy Admin 3.0")
        app_icon = QtGui.QIcon()
        self.setWindowIcon(QtGui.QIcon("img/icon.png"))
        # self.setIconSize(QtCore.QSize(40, 40))
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon("img/icon.png"))
        self.tray_icon.show()
        self.tray_icon.setToolTip("LazyMonitor")
        self.tray_icon.activated.connect(self.onSystemTrayIconClicked)

        self.show()

    def onSystemTrayIconClicked(self, reason, menuWorker=None):
        if reason == QtWidgets.QSystemTrayIcon.Unknown:
            pass
        elif reason == QtWidgets.QSystemTrayIcon.Context:
            menuWorker.systemTrayMenuShowed.emit()
        elif reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            pass
        elif reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.setVisible(not self.isVisible())
        elif reason == QtWidgets.QSystemTrayIcon.MiddleClick:
            pass
        else:
            pass

    def loadSettings(self):
        with open('config.json') as config_file:
            data = json.load(config_file)
            for param in data['db']:
                self.ui.lineEditHostServer.setText(str(param['hostname']))
                self.ui.lineEditUserNameDB.setText(str(param['username']))
                self.ui.lineEditPasswordDB.setText(str(param['password']))
                self.ui.lineEditNameDB.setText(str(param['dbname']))

    def add_server(self):
        self.formDialog = QtWidgets.QDialog()
        self.formDialog.setWindowTitle("Додати")
        self.FormServer = Ui_Dialog()
        self.FormServer.setupUi(self.formDialog)
        model = Model()
        groups = model.get_groups()
        for group in groups:
            self.FormServer.select_group.addItem(group[1], group[0])
        self.FormServer.add_group.setIcon(QtGui.QIcon('img/add_group.png'))
        self.FormServer.buttonBox.accepted.connect(self.formSave)
        self.FormServer.buttonBox.rejected.connect(self.formDialog.close)
        self.formDialog.exec_()


    def delete_server(self):
        model = Model()
        self.LSP.items.clear()
        items = self.LSP.view.findChildren(QtWidgets.QCheckBox)
        for i in items:
            if i.checkState() == QtCore.Qt.Checked:
                item = int(i.property('id'))
                self.LSP.items.append(item)
        model.delete_server(self.LSP.items)
        self.LSP.items.clear()
        self.LSP.get_list_items()
        self.LSD.get_list_items()


    def formSave(self):
        cipher_suite = Fernet(self.salt)
        if self.FormServer.checkBox_rdp.isChecked():
            login_rdp = self.FormServer.lineEdit_login_rdp.text()
            password_rdp = cipher_suite.encrypt(bytes(self.FormServer.lineEdit_password_rdp.text(), "utf-8"))
            port_rdp = self.FormServer.lineEdit_port_rdp.text()
        else:
            login_rdp = ''
            password_rdp = ''
            port_rdp = 0

        if self.FormServer.checkBox_teamviewer.isChecked():
            id_teamviewer = int(self.FormServer.lineEdit_id_teamviewer.text())
            password_teamviewer = cipher_suite.encrypt(bytes(self.FormServer.lineEdit_password_teamviewer.text(), "utf-8"))
        else:
            id_teamviewer = 0
            password_teamviewer = ''

        if self.FormServer.checkBox_ssh.isChecked():
            login_ssh = self.FormServer.lineEdit_login_ssh.text()
            password_ssh = self.FormServer.lineEdit_password_ssh.text()
            port_ssh = self.FormServer.lineEdit_port_ssh()
        else:
            login_ssh = ''
            password_ssh = ''
            port_ssh = 0

        name = self.FormServer.lineEdit_name_server.text()
        name_id = self.FormServer.lineEdit_id_server.text()
        host = self.FormServer.lineEdit_host_server.text()
        port = int(self.FormServer.lineEdit_port_server.text())
        group = int(self.FormServer.select_group.currentData())
        model = Model()

        if model.is_server(name_id):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((host, int(port)))
                s.close()
                status = True
            except IndexError:
                status = False

            model.update_server(name, name_id, port, status, host, login_rdp, password_rdp, port_rdp, id_teamviewer, password_teamviewer, login_ssh, password_ssh, port_ssh, name_id)
        else:
            try:
                status = True
            except IndexError:
                status = False

            model.set_server(name, name_id, port, status, host, login_rdp, password_rdp, port_rdp, id_teamviewer, password_teamviewer, login_ssh, password_ssh, port_ssh, group)

        self.LSP.get_list_items()
        self.LSD.get_list_items()

    def changeEditFormDB(self, enable):

        if enable:

            self.ui.lineEditHostServer.setEnabled(True)
            self.ui.lineEditUserNameDB.setEnabled(True)
            self.ui.lineEditPasswordDB.setEnabled(True)
            self.ui.lineEditNameDB.setEnabled(True)
            self.ui.saveDbConnect.setEnabled(True)
            self.ui.checkDbConnect.setEnabled(True)
            self.ui.editDbConnect.setEnabled(False)
        else:
            data = {}
            data['db'] = []
            data['db'].append({
                'hostname': self.ui.lineEditHostServer.text(),
                'username': self.ui.lineEditUserNameDB.text(),
                'password': self.ui.lineEditPasswordDB.text(),
                'dbname': self.ui.lineEditNameDB.text(),
            })
            with open('config.json', 'w') as config_file:
                json.dump(data, config_file)
            self.loadSettings()
            self.ui.lineEditHostServer.setEnabled(False)
            self.ui.lineEditUserNameDB.setEnabled(False)
            self.ui.lineEditPasswordDB.setEnabled(False)
            self.ui.lineEditNameDB.setEnabled(False)
            self.ui.saveDbConnect.setEnabled(False)
            self.ui.checkDbConnect.setEnabled(False)
            self.ui.editDbConnect.setEnabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = LazyMonitor()
    sys.exit(app.exec_())
