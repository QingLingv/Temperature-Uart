from Ui_use_instructions import Ui_TabWidget
from PyQt5.QtWidgets import QTabWidget

class Tabwidget_use_instructions(QTabWidget, Ui_TabWidget):
    def __init__(self):
        super(Tabwidget_use_instructions, self).__init__()
        self.setupUi(self)
        
        self.text_init()
        
    def text_init(self):
        # 设置连接界面
        with open('doc\connect_exp.txt', 'r', encoding='utf-8') as file_1:
            contents = file_1.read()
        self.textBrowser_1.setText(contents)
        
        # 设置操作命令
        with open('doc\manipulate_exp.txt', 'r', encoding='utf-8') as file_2:
            contents = file_2.read()
        self.textBrowser_2.setText(contents)
        
        # 设置其它说明
        with open('doc\others_exp.txt', 'r', encoding='utf-8') as file_3:
            contents = file_3.read()
        self.textBrowser_3.setText(contents)
        