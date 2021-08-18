import psycopg2
import json
from PyQt5 import QtGui, QtWidgets
from sshtunnel import open_tunnel
from monitor_windows import *


class Model(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
           cls._instance = super(Model, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        with open('config.json') as config_file:
            data = json.load(config_file)

        self.server = open_tunnel(
                ('8.8.8.8', 2225),
                ssh_username="user",
                ssh_password="12345",
                remote_bind_address=('localhost', 5432))
        self.server.start()

        try:
            self.conn = psycopg2.connect(database='las_db', user='postgres', password='postgres', host='localhost', port=self.server.local_bind_port, sslmode='require')
            self.cursor = self.conn.cursor()
        except IndexError:
            msg = QtWidgets.QMessageBox()
            msg.setWindowIcon(QtGui.QIcon("./img/icon.png"))
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Повідомлення")
            msg.setText("Не можливо підключитись до БД!!!")
            msg.addButton('Закрити', QtWidgets.QMessageBox.RejectRole)
            msg.exec()

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        self.server.close()


    def is_server(self, server_id):
        try:
            self.cursor.execute('SELECT * FROM servers WHERE id = %s', (server_id,))
            server = self.cursor.fetchone()
            return server
        except IndexError:
            return False

    def add_server(self, *args):
        print(args)
        self.cursor.execute("INSERT INTO servers(name_server, name_id, port, status, host, login_rdp, password_rdp, port_rdp, id_teamviewer, password_teamviewer, login_ssh, password_ssh, port_ssh, group_id, enable_rdp, enable_teamviewer, enable_ssh) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", args)
        self.conn.commit()

    def delete_server(self, *args):
        if len(args[0]) > 1:
            self.cursor.execute("DELETE FROM servers WHERE id IN %s", (tuple(args[0]),))
        else:
            self.cursor.execute("DELETE FROM servers WHERE id = %s", (args[0][0],))
        self.conn.commit()

    def update_server(self, *args):
        self.cursor.execute("UPDATE servers SET name_server = %s, name_id = %s, port = %s, status = %s, host = %s, login_rdp = %s, password_rdp = %s, port_rdp = %s, id_teamviewer = %s, password_teamviewer = %s, login_ssh = %s, password_ssh = %s, port_ssh = %s, group_id = %s, enable_rdp = %s, enable_teamviewer = %s, enable_ssh = %s WHERE id = %s ", args)
        self.conn.commit()

    def get_servers(self):
        self.cursor.execute("SELECT s.*, g.name_group FROM servers s LEFT JOIN groups g ON g.id = s.group_id ORDER BY s.name_id ASC")
        servers = self.cursor.fetchall()
        return servers

    def get_server(self, id_server):
        self.cursor.execute("SELECT * FROM servers WHERE id = %s", (id_server,))
        server = self.cursor.fetchone()
        return server

    def get_groups(self):
        self.cursor.execute("SELECT * FROM groups")
        groups = self.cursor.fetchall()
        return groups

    def checkConnect(self, form_db):
        msg = QtWidgets.QMessageBox()
        msg.setWindowIcon(QtGui.QIcon("./img/icon.png"))
        msg.setWindowTitle("Повідомлення")
        try:

            conn = psycopg2.connect(
                database=form_db.lineEditNameDB.text(),
                user=form_db.lineEditUserNameDB.text(),
                password=form_db.lineEditPasswordDB.text(),
                host=form_db.lineEditHostServer.text(),
                port=5432)

            self.cursor = conn.cursor()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Підключення до БД Успішне !!!")
        except psycopg2.OperationalError:
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Не можливо підключитись до БД !!!")
        msg.addButton('Закрити', QtWidgets.QMessageBox.RejectRole)
        msg.exec()
