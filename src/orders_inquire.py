import sys
from Ui_orders_inquire import Ui_TabWidget
from PyQt5.QtWidgets import QTabWidget, QApplication,QVBoxLayout
from title_bar import FramelessWindow
from PyQt5.QtCore import QSize
StyleSheet = """
/*标题栏*/
TitleBar {
    background-color: red;
}
/*最小化最大化关闭按钮通用默认背景*/
#buttonMinimum,#buttonMaximum,#buttonClose {
    border: none;
    background-color: red;
}
/*悬停*/
#buttonMinimum:hover,#buttonMaximum:hover {
    background-color: red;
    color: white;
}
#buttonClose:hover {
    color: white;
}
/*鼠标按下不放*/
#buttonMinimum:pressed,#buttonMaximum:pressed {
    background-color: Firebrick;
}
#buttonClose:pressed {
    color: white;
    background-color: Firebrick;
}
"""

class Tabwidget_order(QTabWidget, Ui_TabWidget):
    def __init__(self, *args, **kwargs):
        super(Tabwidget_order, self).__init__(*args, **kwargs)
        self.setupUi(self)
        
        layout = QVBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_init()
     
    def text_init(self):
        # 设置查询命令
        with open('doc\inquire_order.txt', 'r', encoding='utf-8') as file_2:
            contents = file_2.read()
        self.textBrowser_2.setText(contents)
        
        # 设置保存命令
        with open('doc\others_exp.txt', 'r', encoding='utf-8') as file_3:
            contents = file_3.read()
        self.textBrowser_3.setText(contents)
        
        # 设置相关说明
        with open('doc\other_instructions.txt', 'r', encoding='utf-8') as file_4:
            contents = file_4.read()
        self.textBrowser_4.setText(contents)
        
        with open('doc\set_order.txt', 'r', encoding='utf-8') as file_1:
            contents = file_1.read()
        self.textBrowser_1.setText(contents)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    mainWnd = FramelessWindow()
    mainWnd.setWindowTitle('测试标题栏')
    # mainWnd.setWindowIcon(QIcon('ico\ck1.ico'))
    mainWnd.resize(QSize(650,500))
    # app.setStyle('Fusion')
    mainWnd.setWidget(Tabwidget_order(mainWnd))

    mainWnd.show()
    sys.exit(app.exec_())   
        
        









