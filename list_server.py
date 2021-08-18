import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from model import Model


class ListServer(QtWidgets.QWidget):
    mode = ''

    def __init__(self):
        super().__init__()

        self.online = QtGui.QIcon('img/icons/online.png')
        self.offline = QtGui.QIcon('img/icons/offline.png')
        self.dir_open = QtGui.QIcon('img/icons/dir_open.png')
        self.dir_closed = QtGui.QIcon('img/icons/dir_close.png')

    def setupUi(self):
        self.model = Model()
        self.view = QtWidgets.QTreeWidget()
        self.view.setIconSize(QtCore.QSize(20, 20))
        if self.mode == 'list':
            self.view.setHeaderLabels(["Назва сервера", "Адрес сервера", ""])
            self.view.setColumnWidth(0, 180)
            self.view.setColumnWidth(1, 100)
            self.setGeometry(0, 10, 300, 435)
            self.view.hideColumn(2)
        else:
            self.view.setHeaderLabels(["Назва сервера", "Адрес сервера", "Вибрати", ""])
            self.view.setColumnWidth(0, 180)
            self.view.setColumnWidth(1, 100)
            self.view.setColumnWidth(2, 55)

            self.view.hideColumn(3)

            self.setGeometry(0, 10, 360, 435)

        self.view.itemExpanded.connect(self.handleExpanded)
        self.view.itemCollapsed.connect(self.handleCollapsed)

        window_layout = QtWidgets.QVBoxLayout()
        window_layout.addWidget(self.view)
        self.setLayout(window_layout)

        servers = self.model.get_servers()

        self.set_list_servers(servers)

    def doubleClick(self, ev):
        self.view.itemDoubleClicked.connect(ev)

    def get_list_items(self):
        self.view.clear()
        servers = self.model.get_servers()
        self.set_list_servers(servers)

    def set_checkBox(self, item, id):
        widget = QtWidgets.QWidget()
        widget.setObjectName('checkBoxItem')
        lay_out = QtWidgets.QHBoxLayout(widget)
        lay_out.setAlignment(QtCore.Qt.AlignCenter)
        lay_out.setContentsMargins(0, 5, 0, 5)
        checkBox = QtWidgets.QCheckBox(widget)
        checkBox.setProperty('id', id)
        lay_out.addWidget(checkBox)
        self.view.setItemWidget(item, 2, widget)

    def handleExpanded(self, item):
        item.setIcon(0, QtGui.QIcon('img/icons/dir_open.png'))

    def handleCollapsed(self, item):
        item.setIcon(0, QtGui.QIcon('img/icons/dir_close.png'))

    def selected_items(self):
        selected = []
        items = self.view.findChildren(QtWidgets.QCheckBox)
        for i in items:
            if i.checkState() == QtCore.Qt.Checked:
                item = int(i.property('id'))
                selected.append(item)
        return selected

    def get_groups(self):
        groups = self.model.get_groups()
        group_items = {}
        for group in groups:
            group_item = QtWidgets.QTreeWidgetItem(self.view, [group[1]])
            group_item.setIcon(0, self.dir_closed)
            group_item.setExpanded(True)
            group_items[group[0]] = []
            group_items[group[0]] = {'item_group': group_item}
        return group_items

    def set_list_item(self, item, group):
        server = QtWidgets.QTreeWidgetItem(group['item_group'], [item[1], item[5]])
        server.setIcon(0, self.online if item[4] else self.offline)
        # server.setCheckState(2, QtCore.Qt.Unchecked)
        server.setData(3, 0, item[0])
        self.set_checkBox(server, item[0])

    def set_list_servers(self, *args):
        groups = self.get_groups()
        for item in args[0]:
            self.set_list_item(item, groups[item[14]])
