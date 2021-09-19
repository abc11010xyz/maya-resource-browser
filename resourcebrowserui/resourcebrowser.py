import os

from maya import cmds
from maya import OpenMayaUI as omui

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2 import __version__
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide import __version__
    from shiboken import wrapInstance


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QWidget)


class Icon(QThread):

    SIZE = 32

    GRID_WIDTH = 120
    GRID_HEIGHT = 60

    PADDING = 5
    BORDER = 1

    @staticmethod
    def check_invalid(names):
        filtered = []

        if names:
            for name in names:
                _, ext = os.path.splitext(name)
                if ext in [".png", ".svg"]:
                    filtered.append(name)

        return filtered

    def __init__(self):
        super(Icon, self).__init__()

        self.item_size = None

        self.names = []
        self.items = {}

        self.set_names()
        self.set_items()

        QTimer.singleShot(1, self.start)

    def set_names(self):
        names = cmds.resourceManager(nameFilter="*")
        self.names = Icon.check_invalid(names)

    def set_items(self):
        self.set_item_size()

        for name in self.names:
            item = QListWidgetItem(name)
            item.setSizeHint(self.item_size)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            self.items[name] = item

    def set_item_size(self):
        item_width = Icon.GRID_WIDTH + Icon.BORDER*2 + Icon.PADDING*2
        item_height = Icon.GRID_HEIGHT + Icon.BORDER*2 + Icon.PADDING
        self.item_size = QSize(item_width, item_height)
    
    def run(self):
        for name in self.names:
            image = QImage(":/{}".format(name))

            size = max(image.size().width(), image.size().height())
            if size > Icon.SIZE:
                size = Icon.SIZE

            image = image.scaled(
                size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            pixmap = QPixmap()
            pixmap.convertFromImage(image)

            icon = QIcon()
            icon.addPixmap(pixmap, QIcon.Selected)

            self.items[name].setIcon(icon)


class ResourceBrowser(QWidget):

    VERSION = "0.0.1"

    TITLE = "Resource Browser"

    ICON_LIST_WGT_STYLE_SHEET = """
        QListWidget {
            border: none;
            padding-left: -%(add)spx;
        }
        QListWidget:selected {
            outline: none;
        }
        QListWidget::item {
            border: %(border)spx solid %(base_color)s;
            padding: %(padding)spx;
            margin-top: %(padding)spx;
        }
        QListWidget::item:selected:active {
            border: %(border)spx solid #5285a6;
            border-radius: 2px;
            background-color: rgba(82, 133, 166, 50);
        }
        QListWidget::item:selected:!active {
            border: %(border)spx solid rgba(82, 133, 166, 150);
            border-radius: 2px;
            background-color: rgba(82, 133, 166, 40);
        }
    """

    def __init__(self, parent=maya_main_window()):
        super(ResourceBrowser, self).__init__(parent)

        self.icon = Icon()

        self.setWindowTitle(ResourceBrowser.TITLE)
        self.setWindowFlags(Qt.WindowType.Window)

        self.init_ui()
        self.init_list_wgt()

    def init_ui(self):
        # WIDGET
        self.filter_le = QLineEdit()
        
        self.name_list_wgt = QListWidget()
        self.name_list_wgt.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.name_list_wgt.setStyleSheet("""
            QListWidget {
                border: none;
            }
        """)

        self.path_le = QLineEdit()
        self.path_le.setMinimumWidth(280)
        self.path_le.setReadOnly(True)
        self.path_le.setStyleSheet("padding-left: 1px;")

        self.icon_list_wgt = QListWidget()
        self.icon_list_wgt.setUniformItemSizes(True)
        self.icon_list_wgt.setViewMode(QListWidget.IconMode)
        self.icon_list_wgt.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.icon_list_wgt.setMovement(QListWidget.Static)

        # LAYOUT
        filter_form_layout = QFormLayout()
        filter_form_layout.addRow("Filter:", self.filter_le)

        name_layout = QVBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(6)
        name_layout.addLayout(filter_form_layout)
        name_layout.addWidget(self.name_list_wgt)

        name_widget = QWidget()
        name_widget.setFixedWidth(280)
        name_widget.setLayout(name_layout)

        path_form_layout = QFormLayout()
        path_form_layout.addRow("Path:", self.path_le)

        path_layout = QHBoxLayout()
        path_layout.addStretch()
        path_layout.addLayout(path_form_layout)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(6)
        icon_layout.addLayout(path_layout)
        icon_layout.addWidget(self.icon_list_wgt)

        icon_widget = QWidget()
        icon_widget.setMinimumWidth(312)
        icon_widget.setLayout(icon_layout)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        main_layout.addWidget(name_widget)
        main_layout.addWidget(icon_widget)

        # CONNECTION
        self.filter_le.editingFinished.connect(self.on_filter_editing_finished)
        self.name_list_wgt.itemClicked.connect(self.on_item_clicked)
        self.icon_list_wgt.itemClicked.connect(self.on_item_clicked)

    def on_filter_editing_finished(self):
        self.refresh_filtered_list_wgt()

    def on_item_clicked(self, item):
        sender = self.sender()

        list_wgt = self.name_list_wgt
        if sender == self.name_list_wgt:
            list_wgt = self.icon_list_wgt

        if not sender.selectedIndexes():
            return

        row = sender.selectedIndexes()[0].row()
        list_wgt.setCurrentRow(row)
        self.scroll_to_selected_index(list_wgt)

        text = item.text()
        self.path_le.setText(":/{}".format(text))

        self.selected_item_text = text

    def init_list_wgt(self):
        self.scrl_bar_width = self.icon_list_wgt.verticalScrollBar().sizeHint().width()
        self.icon_list_wgt_base_color = self.icon_list_wgt.palette().base().color().name()
        self.style_sheet = {
            "base_color": self.icon_list_wgt_base_color,
            "padding": Icon.PADDING,
            "border": Icon.BORDER,
        }

        self.filter_text = ""
        self.selected_item_text = ""

        self.filtered = self.icon.names

        self.set_item_width_height()
        self.refresh_list_wgt()

    def set_item_width_height(self):
        self.item_width = self.icon.item_size.width() + Icon.PADDING*2
        if self.item_width % 2:
            self.item_width += 1
        
        self.item_height = self.icon.item_size.height()
        if self.item_height % 2:
            self.item_height += 1

    def refresh_filtered_list_wgt(self):
        if self.set_filtered():
            self.refresh_list_wgt()

    def set_filtered(self):
        text = self.filter_le.text()
        if text == self.filter_text:
            return False
        
        self.filter_text = text

        text += "*"

        filtered = cmds.resourceManager(nameFilter=text)
        self.filtered = Icon.check_invalid(filtered)

        return True
    
    def refresh_list_wgt(self):
        self.clear_list_wgt()

        if self.filtered:
            if self.selected_item_text and self.selected_item_text in self.filtered:
                index = self.filtered.index(self.selected_item_text)
            else:
                index = 0
                self.selected_item_text = ""

            self.set_name_list_wgt()
            self.set_icon_list_wgt()

            for list_wgt in [self.name_list_wgt, self.icon_list_wgt]:
                list_wgt.setCurrentRow(index)
                self.scroll_to_selected_index(list_wgt)

            text = self.icon_list_wgt.item(index).text()
            self.path_le.setText(":/{}".format(text))

    def clear_list_wgt(self):
        self.name_list_wgt.clear()
        self.clear_icon_list_wgt()

        self.path_le.clear()

    def clear_icon_list_wgt(self):
        while self.icon_list_wgt.count():
            self.icon_list_wgt.takeItem(0)

    def set_name_list_wgt(self):
        self.name_list_wgt.addItems(self.filtered)

    def set_icon_list_wgt(self):
        for name in self.filtered:
            self.icon_list_wgt.addItem(self.icon.items[name])

    def resizeEvent(self, event):
        icon_list_wgt_width = self.icon_list_wgt.size().width() - self.scrl_bar_width - 1

        count = icon_list_wgt_width / self.item_width
        spacing = icon_list_wgt_width - self.item_width * count

        add = float(spacing) / count

        if icon_list_wgt_width > (self.item_width * self.icon_list_wgt.count()):
            add = 0

        self.icon_list_wgt.setGridSize(QSize(self.item_width + add, self.item_height))

        if add % 2:
            add -= 1

        self.style_sheet["add"] = str(add/2)

        self.icon_list_wgt.setStyleSheet(
            ResourceBrowser.ICON_LIST_WGT_STYLE_SHEET % self.style_sheet
        )

        self.scroll_to_selected_index(self.icon_list_wgt)

    def scroll_to_selected_index(self, list_wgt):
        if list_wgt.selectedIndexes():
            index = list_wgt.selectedIndexes()[0]
            list_wgt.scrollTo(index, QAbstractItemView.PositionAtCenter)

    def set_geometry(self):
        self.resize(1030, 590)

        geo = self.geometry()
        maya_frame_geo = maya_main_window().frameGeometry()
        geo.moveCenter(maya_frame_geo.center())

        self.setGeometry(geo)
    
    def showEvent(self, event):
        self.name_list_wgt.setFocus()
        self.set_geometry()

    def keyPressEvent(self, event):
        super(ResourceBrowser, self).keyPressEvent(event)
        event.accept()


def show_ui():
    global resource_browser

    try:
        resource_browser.close()
        resource_browser.deleteLater()
    except:
        pass

    resource_browser = ResourceBrowser()
    resource_browser.show()


if __name__ == "__main__":
    show_ui()