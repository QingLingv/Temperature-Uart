import sys
import serial.tools.list_ports
import random
import qdarkstyle
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, QTimer, QSettings, QSize, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush

from Ui_tiny_uart import Ui_MainWindow
from serial_thread import Qthread_function
from pyqtgraph_single_set import Pyqtgraph_function
from pyqtgraph_multi_set import Pyqtgraph_Cycle_function 
from orders_inquire import Tabwidget_order
from use_instructions import Tabwidget_use_instructions
from title_bar import FramelessWindow, StyleSheet, Slider_Style_Disable

# 仅标题栏样式（不含三个按钮）
Title_Style = """
    background-color: rgb(46,49,124);
    border-top-left-radius:20px;
}
"""

# 滑动条样式表
Slider_Style_Enable = """
QSlider::groove:horizontal{ 
     height: 12px; 
     left: 0px; 
     right: 0px; 
     border:0px;   
     border-radius:6px;   
     background:rgba(0,0,0,50);
} 
QSlider::handle:horizontal{ 
     width:  10px; 
     height: 5px; 
     margin-top: -2px; 
     margin-bottom: -2px; 
     margin-left: 0px; 
     margin-right: 0px; 
	 background:rgba(252,140,35,1);
} 
QSlider::sub-page:horizontal{
     background:rgba(80,166,234,1);
}
"""

# 四个滑动条的状态
Slider_Dict={
    1:[True, False, False, False],
    2:[True, True, False, False],
    3:[True, True, True, False],
    4:[True, True, True, True]
}

# 滑动条列表
Sliders_List = []
# 连续设置的温度列表
Tems_time_List = []
# 步长增幅
Parameters_List= [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.3, 1.4, 1.5, 1.6, 
                  1.7, 1.8, 1.9, 2.0]

class Main_Interface(QMainWindow, Ui_MainWindow):
    # 用以判断是哪个引起定时器
    pyqtsignal_single_start = pyqtSignal(bool)
    
    def __init__(self):
        super(Main_Interface, self).__init__()
        
        self.setupUi(self)
        self.mainwindow_init()
        self.ui_init_connect()
        
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # 启用定时器来自动采集数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Temperature_Ask_times)
        
        # 实例化创建的指令查询页面
        self.Order_Ask = Tabwidget_order()
        # 实例化用户操作页面
        self.Use_Notes = Tabwidget_use_instructions()
        
        # 创建串口子线程
        self.set_Serial_QThread()
        # 创建绘图子线程
        self.set_Pyqtgraph_QThread()
        # 创建连续绘图子线程
        self.set_Pyqtgraph_Cycle_QThread()
        
        # 创建温度设置数据列表
        self.tem_set_list = []
        # 创建状态栏的切换信号
        self.status_flag = True
        # 温度查询切换信号
        self.single_or_cycle = True
        # 仿真数值设定
        self.send_num = 20
        # 设定的数值记录
        self.set_num = 0
        
        # 创建菜单栏设置功能提示
        self.set_flag = False
        # 创建菜单栏刷新功能提示
        self.refresh_flag = False
        # 滑动条标志
        self.slider_flag = False
        # 单次设置开启权限
        self.single_is_on = True
        # 多次设置开启权限
        self.multi_is_on = True
        # 文件保存位置，以示区分
        self.save_file_flags = True
        
        # 这里刷新串口要放在 刷新标志之后
        self.uart_refresh()
        self.config_parameter_init()
        
        self.dark_theme_flag = True
        # 显示当前主线程 ID
        self.main_ID = int(QThread.currentThreadId())
        print("主线程ID:",self.main_ID)

        # 绑定信号
        self.pyqtsignal_single_start.connect(self.Temperature_Ask_times_todo)
        self.plotwidgets_install()   
        
    def plotwidgets_install(self):
        # 装载图形化部件
        self.horizontalLayout_plotwidget.addWidget(self.Pyqtgraph_Function.plotwidget)
        self.verticalLayout.addWidget(self.Pyqtgraph_Function.graphics)
        # 装载连续绘图部件
        self.horizontalLayout_cycle.addWidget(self.Pyqtgraph_Cycle_Function.plotwidget)
       
    # 串口、主窗口线程号码    
    def main_serial_id_init(self, serial_id):
        self.label_main_id.setText('Main ID:'+str(self.main_ID))
        self.label_serial_id.setText(serial_id)
    
    # 主窗口相关设置初始化    
    def mainwindow_init(self):
        # 设置标题
        # self.setWindowTitle(APP_NAME)
        self.menuBar.hide()
        # 初始化状态栏
        self.label_space1.setText('')
        self.label_space2.setText('Loading......')
        self.statusBar.addWidget(self.label_space1, 4)
        self.statusBar.addWidget(self.label_space2, 2)
        self.statusBar.addWidget(self.progressBar, 10)

        # 创建下数据保存路径
        # 创建目录
        if not os.path.exists("D:\Tiny Uart Data\Single_Set"):
            os.mkdir("D:\Tiny Uart Data\Single_Set")
        if not os.path.exists("D:\Tiny Uart Data\Multi_Sets"):
            os.mkdir("D:\Tiny Uart Data\Multi_Sets")
    
    # 状态栏状态设置    
    def mainwindow_statubar(self, timedate):
        #设置状态栏
        if self.status_flag:
            self.statusBar.removeWidget(self.label_space1)
            self.statusBar.removeWidget(self.label_space2)
            self.statusBar.removeWidget(self.progressBar)
            self.status_flag = False
        if self.pushButton_open.text() == '关闭串口':     
            self.label_datetime.setText(self.comboBox_uart.currentText() + ' | ' + timedate + '  ')
        else:
            self.label_datetime.setText('未连接端口' + ' | ' + timedate + '  ')
        self.statusBar.addPermanentWidget(self.label_datetime)
    
    # 配置文件参数设置
    def config_parameter_init(self):
        self.settings = QSettings("src\config.ini", QSettings.IniFormat)
        self.settings.setIniCodec("UTF-8")
        
        # self.config_uart_baud = self.settings.value("SETUP/UART_BAUD", 0, type=int)
        # 初始化参数
        self.config_uart_baud = self.settings.value("SETUP/UART_BAUD")
        self.comboBox_baud.setCurrentText(self.config_uart_baud)
        self.config_uart_data = self.settings.value("SETUP/UART_DATA")
        self.comboBox_data.setCurrentText(self.config_uart_data)
        self.config_uart_stop = self.settings.value("SETUP/UART_STOP")
        self.comboBox_baud.setCurrentText(self.config_uart_stop)
        self.config_uart_check = self.settings.value("SETUP/UART_CHECK")
        self.comboBox_baud.setCurrentText(self.config_uart_check)
        # print(self.config_uart_baud)
        # self.settings.setValue('tt','opdasda')
        
        if self.set_flag:
            QMessageBox.information(self,'提示信息','配置参数成功!')
        self.set_flag = True
     
    # 设置串口线程     
    def set_Serial_QThread(self):
        # 新建串口线程
        self.Serial_QThread = QThread()
        # 实例化方法
        self.QThread_Function = Qthread_function()
        # 将方法移动到线程里面
        self.QThread_Function.moveToThread(self.Serial_QThread)
        # 启动线程
        self.Serial_QThread.start()
        # 将信号连接槽函数
        self.QThread_Function.signal_Serialstart.connect(self.QThread_Function.SerialInit_func)
        # 发出信号，运行函数
        self.QThread_Function.signal_Serialstart.emit()
        # 将按钮打开信号和槽连接
        self.QThread_Function.signal_pushButton_Open.connect(self.QThread_Function.slot_pushButton_Open)
        # 连接串口打开通知信号
        self.QThread_Function.signal_pushButton_Open_flag.connect(self.slot_pushButton_Open_flag)
        # 连接读取信号按钮
        self.QThread_Function.signal_readData.connect(self.ui_readData)
        self.QThread_Function.signal_readData.connect(self.QThread_Function.slot_readData_disposal)
        # 连接数据处理之后的LCD显示函数
        self.QThread_Function.signal_readData_disposal.connect(self.Temperature_Ask_times_display)
        # 连接发送信号和槽
        self.QThread_Function.signal_sendData.connect(self.QThread_Function.slot_sendData)
        # 连接串口线程信号发送和槽函数
        self.QThread_Function.signal_serial_id.connect(self.main_serial_id_init)
      
    # 设置绘图线程    
    def set_Pyqtgraph_QThread(self):
        # 实例方法
        self.Pyqtgraph_Function =  Pyqtgraph_function()
        # 绑定子线程，使得子线程之间直接通信
        self.QThread_Function.signal_readData_disposal.connect(self.Pyqtgraph_Function.recv_list_real_tem)
        self.Pyqtgraph_Function.psignal_pyqtgraph_tem_set.connect(self.Pyqtgraph_Function.recv_list_set_tem)
        # 传递处理好的列表
        self.Pyqtgraph_Function.psignal_pyqtgraph_draw.connect(self.Pyqtgraph_Function.pyqtgraph_draw)
        # 信号提示报错
        self.Pyqtgraph_Function.psignal_pyqtgraph_warning.connect(self.draw_message_func)
        # 文件保存信号传递绑定
        self.Pyqtgraph_Function.psignal_pyqtgraph_savefile.connect(self.Pyqtgraph_Function.save_file)
        # 绑定数据清除按钮信号和函数
        self.Pyqtgraph_Function.psignal_pyqtgraph_clear.connect(self.Pyqtgraph_Function.clear_lists)
        # 绑定时间信号给状态栏
        self.Pyqtgraph_Function.psignal_pyqtgraph_timedate.connect(self.mainwindow_statubar)
        # 绑定横纵坐标数据
        self.Pyqtgraph_Function.psignal_pyqtgraph_notes.connect(self.label_notes_set)
        # 绑定滚轮信号
        self.Pyqtgraph_Function.psignal_pyqtgraph_scroll.connect(self.Pyqtgraph_Function.draw_substractions)
        # 绑定插值信号给标签显示
        self.Pyqtgraph_Function.psignal_pyqtgraph_sub.connect(self.label_sub_func)
    
    # 设置连续绘图子线程
    def set_Pyqtgraph_Cycle_QThread(self):
        # 实例方法
        self.Pyqtgraph_Cycle_Function =  Pyqtgraph_Cycle_function()
        # 绑定设置温度列表信号
        self.Pyqtgraph_Cycle_Function.signal_set_tem_list.connect(self.Pyqtgraph_Cycle_Function.receive_tem_set_list)
        # 绑定设置温度时间信号
        self.Pyqtgraph_Cycle_Function.signal_dalay_time.connect(self.Pyqtgraph_Cycle_Function.receive_delay_time)
        # 绑定计时启动信号
        self.Pyqtgraph_Cycle_Function.signal_timer_start.connect(self.Pyqtgraph_Cycle_Function.timer_start_func)
        # 绑定计时停止信号
        self.Pyqtgraph_Cycle_Function.signal_timer_stop.connect(self.Pyqtgraph_Cycle_Function.timer_stop_func)
        # 绑定更换温度的信号
        self.Pyqtgraph_Cycle_Function.signal_alter_label_tem.connect(self.label_set_tem_alter)
        # 绑定实时和设置的温度值
        self.Pyqtgraph_Cycle_Function.signal_real_set_tem.connect(self.Pyqtgraph_Cycle_Function.collect_real_set_tem)
        # 绑定两个列表信号
        self.Pyqtgraph_Cycle_Function.signal_real_set_tems_lists.connect(self.Pyqtgraph_Cycle_Function.draw_tems)
        # 绑定清除信号
        self.Pyqtgraph_Cycle_Function.signal_clear_lists.connect(self.Pyqtgraph_Cycle_Function.clear_cycle_lists)
        # 绑定警告信号
        self.Pyqtgraph_Cycle_Function.signal_warn_flag.connect(self.draw_message_func)
        # 绑定标签内容传递信号
        self.Pyqtgraph_Cycle_Function.signal_label_notes.connect(self.label_notes_set_cycle)
        # 保存信号传递
        self.Pyqtgraph_Cycle_Function.signal_cycle_save_files.connect(self.Pyqtgraph_Cycle_Function.multi_save_files)
        
    # 绘图页面右标签设置   
    def label_sub_func(self, sub):
        self.label_sub.setText('real_tem - set_tem = ' + str(sub))
      
    # 绘图页面左标签设置          
    def label_notes_set(self, content):
        self.label_note.setText(content)
        
    # 连续绘图标签设置
    def label_notes_set_cycle(self, content):
        self.label_note_cycle.setText(content)

    # 绘图页面绘图功能函数   
    def pyqtgraph_draw_open(self, pushbutton_draw):
        if pushbutton_draw == self.pushButton_draw:
            self.Pyqtgraph_Function.is_on = True
            self.Pyqtgraph_Function.start()
        else:
            self.Pyqtgraph_Cycle_Function.is_on = True
            self.Pyqtgraph_Cycle_Function.start()
    
    # 绘图页面清理功能函数
    def pyqtgraph_draw_clear(self, pushbutton_clear):
        if pushbutton_clear == self.pushButton_clear:
            self.Pyqtgraph_Function.psignal_pyqtgraph_clear.emit()
        else:
            self.Pyqtgraph_Cycle_Function.signal_clear_lists.emit()
            """
            仿真代码
            """
        self.send_num = 20
            
    # 界面功能按钮绑定函数
    def ui_init_connect(self):
        '''
        创造部件容器,避免重复操作
        '''
        # 把生成的滑动条放入列表中
        Sliders_List.append(self.slider_tem_1)
        Sliders_List.append(self.slider_tem_2)
        Sliders_List.append(self.slider_tem_3)
        Sliders_List.append(self.slider_tem_4)
        '''
        ui 界面按钮设置
        '''
        # 关联串口刷新按钮
        self.pushButton_refresh.clicked.connect(self.uart_refresh)
        # 关联打开串口按钮
        self.pushButton_open.clicked.connect(self.uart_open) 
        # 关联发送数据按钮
        self.pushButton_send.clicked.connect(self.send_data)
        # 关联发送计数
        self.pushButton_clear_tx.clicked.connect(self.clear_send_num)
        # 关联接收计数
        self.pushButton_clear_rx.clicked.connect(self.clear_receive_num)
        # 单次开关关联查询温度
        self.pushButton_start.clicked.connect(lambda:self.auto_tem_start(self.pushButton_start))
        # 循环开关关联自动温度查询
        self.pushButton_cycle_start.clicked.connect(lambda:self.auto_tem_start(self.pushButton_cycle_start))
        # 循环开关关联设置温度标签变换
        self.pushButton_cycle_start.clicked.connect(self.cycle_timer_start)
        # 循环停止开关关联停止查询
        self.pushButton_cycle_stop.clicked.connect(lambda:self.auto_tem_stop(self.pushButton_cycle_stop))
        # 单次开关关联停止查询
        self.pushButton_stop.clicked.connect(lambda:self.auto_tem_stop(self.pushButton_stop))
        # 关联设置温度
        self.pushButton_tem_set.clicked.connect(self.Temperature_set)
        # 关联 16进制发送
        self.tx_lineEdit.textChanged.connect(self.checkBox_HexSend_func)
        self.checkBox_HexSend.stateChanged.connect(self.checkBox_HexSend_func)
        self.checkBox_AddEnd.stateChanged.connect(self.checkBox_HexSend_func)
        '''
        工具栏按钮设置
        '''
        self.action_zlcx.triggered.connect(self.order_ask_func)
        self.action_sx.triggered.connect(self.uart_refresh)
        self.action_set.triggered.connect(self.config_parameter_init)
        self.action_sysm.triggered.connect(self.User_Notes_func)
        self.action_zzjs.triggered.connect(self.author_func)
        self.action_alter_theme.triggered.connect(self.action_alter_theme_func)
        self.action_data.triggered.connect(self.action_data_func)
        '''
        绘图设置
        '''
        self.pushButton_draw.clicked.connect(lambda:self.pyqtgraph_draw_open(self.pushButton_draw))
        self.pushButton_draw_cycle.clicked.connect(lambda:self.pyqtgraph_draw_open(self.pushButton_draw_cycle))
        self.pushButton_save.clicked.connect(lambda:self.save_file_start(self.pushButton_save))
        self.pushButton_save_cycle.clicked.connect(lambda:self.save_file_start(self.pushButton_save_cycle))
        self.pushButton_clear.clicked.connect(lambda:self.pyqtgraph_draw_clear(self.pushButton_clear))
        self.pushButton_clear_cycle.clicked.connect(lambda:self.pyqtgraph_draw_clear(self.pushButton_clear_cycle))
        """
        循环绘图设置
        """
        self.slider_tem_1.valueChanged.connect(lambda:self.on_change_slider(self.slider_tem_1))
        self.slider_tem_2.valueChanged.connect(lambda:self.on_change_slider(self.slider_tem_2))
        self.slider_tem_3.valueChanged.connect(lambda:self.on_change_slider(self.slider_tem_3))
        self.slider_tem_4.valueChanged.connect(lambda:self.on_change_slider(self.slider_tem_4))
        self.slider_time.valueChanged.connect(lambda:self.on_change_slider(self.slider_time))
        self.slider_number.valueChanged.connect(self.slider_state_judge)
        self.pushButton_cycle.clicked.connect(self.cycle_check)
        
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.rx_lcdNumber.display(self.data_num_received)
            
        self.data_num_sended = 0
        self.tx_lcdNumber.display(self.data_num_sended) 
    
    # 给标签设置设定好的温度
    def cycle_timer_start(self):
        # 启动时间计时停留时间
        self.Pyqtgraph_Cycle_Function.signal_timer_start.emit()
    
    # 计时足够，更改目标温度值
    def label_set_tem_alter(self, next_tem):
        self.set_num = next_tem
        self.label_set_tem.setText(str(next_tem))

    # 检查循环设置的问题    
    def cycle_check(self):
        str1 = '设定了 ' + str(self.slider_number.value()) + ' 个温度值' + '\n'
        list_tem = []
        global Tems_time_List
        for i in range(self.slider_number.value()):
            list_tem.append(str(Sliders_List[i].value())+'℃')
            Tems_time_List.append(Sliders_List[i].value())
        # 将数据列表加停留时间发回去
        self.Pyqtgraph_Cycle_Function.signal_set_tem_list.emit(Tems_time_List)
        self.Pyqtgraph_Cycle_Function.signal_dalay_time.emit(self.slider_time.value())
        str2 = '设定的停留时间为 ' + str(self.slider_time.value()) + 's'
        message = str1 + ' '.join(list_tem) + '\n' + str2
        # 这里直接设置第一个温度
        self.label_set_tem.setText(str(Sliders_List[0].value()))
        QMessageBox.information(self, '提示信息', message)
        # 数据发送完就清空
        self.set_num = Tems_time_List[0]
        Tems_time_List = []
        
    # 判断其它滑动条是否可以使用
    def slider_state_judge(self):
        slider_state = Slider_Dict[self.slider_number.value()]
        for i in range(0,4):
            Sliders_List[i].setEnabled(slider_state[i])
            if slider_state[i]:
                Sliders_List[i].setStyleSheet(Slider_Style_Enable)
            else:
                Sliders_List[i].setStyleSheet(Slider_Style_Disable)
    
    # 标签与滑动条绑定
    def on_change_slider(self, slider):
        if slider == self.slider_tem_1:
            self.label_tem_1.setText(str(self.slider_tem_1.value())+'℃')
        elif slider == self.slider_tem_2:
            self.label_tem_2.setText(str(self.slider_tem_2.value())+'℃')
        elif slider == self.slider_tem_3:
            self.label_tem_3.setText(str(self.slider_tem_3.value())+'℃')
        elif slider == self.slider_tem_4:
            self.label_tem_4.setText(str(self.slider_tem_4.value())+'℃')
        else:
            self.label_time.setText(str(self.slider_time.value())+'s')
            
    # 创建目录 
    def action_data_func(self):
        # 打开指令
        os.system("start explorer D:\Tiny Uart Data") 
     
    # 作者信息绑定    
    def author_func(self):
        with open(r"doc\\author.txt", 'r', encoding='utf-8') as file:
            contents = file.read()
        QMessageBox.about(self, '作者信息', contents)    
    
    # 用户使用手册信息窗口绑定
    def User_Notes_func(self):
        # 当前窗口必须关闭才可以进入主窗口
        # self.Use_Notes.exec_() 
        self.Use_Notes.show()   
    
    # 指令查询按钮函数
    def order_ask_func(self):
        self.Order_Ask.show()
       
    # 文件保存按钮功能绑定    
    def save_file_start(self, pushbutton_save):
        if pushbutton_save == self.pushButton_save:
            # 更改存储文件位置标志
            self.save_file_flags = True
            self.Pyqtgraph_Function.psignal_pyqtgraph_savefile.emit() 
        else:
            self.save_file_flags = False
            self.Pyqtgraph_Cycle_Function.signal_cycle_save_files.emit()
    
    # 画画指令查询设置
    def draw_message_func(self, save_flag):
        if save_flag:
            if self.save_file_flags:
                QMessageBox.information(self,'提示信息','温度数据保存成功!\n保存位置:D:\Tiny Uart Data\Single_Set')
            else:
                QMessageBox.information(self,'提示信息','温度数据保存成功!\n保存位置:D:\Tiny Uart Data\Multi_Sets')
        else:
            QMessageBox.information(self,'警告信息','温度数据不存在!')
    
    # 串口刷新设置     
    def uart_refresh(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.comboBox_uart.clear()
        for port in port_list:
            # 端口名 + 端口名称
            # COM13     Arduino Uno (COM13)
            # print(port[0],port[1])
            self.Com_Dict["%s" % port[1]] = "%s" % port[0]
            self.comboBox_uart.addItem(port[1])
        # print(self.Com_Dict)
        # 如果没有检测到，那就设置为空，并且使得打开串口按钮不可按下
        if len(self.Com_Dict) == 0:
            self.comboBox_uart.setCurrentText("")
            self.pushButton_open.setEnabled(False)
        else:
            self.pushButton_open.setEnabled(True)
            
        if self.refresh_flag:
            QMessageBox.information(self,'提示信息','刷新成功!')
        self.refresh_flag = True

    # 串口参数配置
    def uart_open(self):
        self.set_parameter = {}
        self.set_parameter['comboBox_uart'] = self.Com_Dict[self.comboBox_uart.currentText()]
        self.set_parameter['comboBox_baud'] = self.comboBox_baud.currentText()
        self.set_parameter['comboBox_data'] = self.comboBox_data.currentText()
        self.set_parameter['comboBox_stop'] = self.comboBox_stop.currentText()
        self.set_parameter['comboBox_check']= self.comboBox_check.currentText()
        self.QThread_Function.signal_pushButton_Open.emit(self.set_parameter)
        
    # 读取数据设置
    def ui_readData(self,rec_data):
        rec_length = len(rec_data)
        self.data_num_received += rec_length
        self.rx_lcdNumber.display(self.data_num_received)
        
        # 设置要显示的内容
        if self.radioButton_hex.isChecked():
            rev_data = ''
            for i in range(0, len(rec_data)):
                rev_data = rev_data + '0x' +'{:02X}'.format(rec_data[i]) + ' '
            self.rx_textBrowser.insertPlainText(rev_data)
            self.rx_textBrowser.insertPlainText('\n')
        else:
            self.rx_textBrowser.insertPlainText(rec_data.decode('utf-8'))
        
        # 获取到 text 光标
        textCursor = self.rx_textBrowser.textCursor()
        # 滚动到底部
        textCursor.movePosition(textCursor.End)
        # 设置光标到text中去
        self.rx_textBrowser.setTextCursor(textCursor)

    # 串口开启按钮函数
    def slot_pushButton_Open_flag(self,sate):
        if sate == 0:
            QMessageBox.warning(self,'错误信息','串口已被占用,打开失败!')
            self.label_ck.setPixmap(QPixmap('ico\connect_zy.ico'))
        elif sate == 1:
            self.pushButton_open.setText('关闭串口')
            #self.pushButton_open.setStyleSheet("color:red")
            self.pushButton_open.setIcon(QIcon('ico\disconnect.ico'))
            self.label_ck.setPixmap(QPixmap('ico\connect_yes.ico'))
        else:
            self.pushButton_open.setText('打开串口')
            #self.pushButton_open.setStyleSheet("color:black")
            self.pushButton_open.setIcon(QIcon('ico\connect1.ico'))
            self.label_ck.setPixmap(QPixmap('ico\connect_no.ico'))
            # 关闭定时器！！！
            self.timer.stop()
            self.Pyqtgraph_Function.is_on = False
        
    # 发送数据设置
    def send_data(self):
        if self.pushButton_open.text() == '关闭串口':
            send_data = self.tx_lineEdit.text()
            send_data = self.send_data_adjust(send_data)
            # 发送出信号
            self.QThread_Function.signal_sendData.emit(send_data)
            
            send_length = len(send_data)
            self.data_num_sended += send_length
            self.tx_lcdNumber.display(self.data_num_sended) 
        else:
            QMessageBox.warning(self,'错误信息','请先连接串口!')
        
    # 发送数据格式调整 
    def send_data_adjust(self,senddata):
        if self.checkBox_AddEnd.checkState():
            senddata = senddata + '\r'
        return senddata
    
    # 十六进制发送显示设置                           
    def checkBox_HexSend_func(self):
        if self.checkBox_HexSend.checkState():
            send_text = self.tx_lineEdit.text()
            if self.checkBox_AddEnd.checkState():
                send_text = send_text + '\r'
            send_text_encode = send_text.encode('utf-8')
            send_hex = ''
            for i in range(0, len(send_text)):
                send_hex = send_hex + '0x' + '{:02X}'.format(send_text_encode[i]) + ' '
            self.Hex_textBrowser.setText(send_hex)
        else:
            self.Hex_textBrowser.setText('')   
    
    # 温度自动查询开始 
    def auto_tem_start(self, pushbutton):
        if self.pushButton_open.text() == '关闭串口':
            if pushbutton == self.pushButton_cycle_start:
                if self.multi_is_on:
                    # 告诉选择了多次
                    self.single_or_cycle = False
                    # 同时关闭单次设置权限
                    self.single_is_on = False
                else:
                    # 多次权限没打开
                    QMessageBox.warning(self,'开始失败','请先关闭单次温度设置!') 
            else:
                if self.single_is_on:
                     # 告诉设置了单次温度
                    self.single_or_cycle = True
                    # 同时关闭多次设置权限
                    self.multi_is_on = False
                else:
                    # 单次权限没打开
                    QMessageBox.warning(self,'开始失败','请先关闭多次温度设置!') 
            self.timer.start(1000)
        else:
            QMessageBox.warning(self,'温度查询失败','请先连接串口!') 
    
    # 温度自动查询停止        
    def auto_tem_stop(self, pushbutton):
        if self.pushButton_open.text() == '关闭串口':
            if pushbutton == self.pushButton_stop:
                # 同时也让画图停下！
                self.Pyqtgraph_Function.is_on = False
                # 把连续界面的数据删除
                self.Pyqtgraph_Cycle_Function.set_time_list = []
                self.Pyqtgraph_Cycle_Function.real_tem_list = []
                # 把多次设置权限打开
                self.multi_is_on = True
            else:
                # 当为连续设置时
                self.Pyqtgraph_Cycle_Function.signal_timer_stop.emit()
                self.Pyqtgraph_Cycle_Function.is_on = False
                # 把单页界面的数据删除
                self.Pyqtgraph_Function.list_real_tem = []
                self.Pyqtgraph_Function.list_set_tem = []
                self.Pyqtgraph_Function.subtraction = []
                # 把单次权限打开
                self.single_is_on = True
            self.timer.stop()
        else:
            QMessageBox.warning(self,'温度查询失败','请先连接串口!')       
    
    # 温度询问 命令发送  判断              
    def Temperature_Ask_times(self):
        if self.pushButton_open.text() == '关闭串口':
            self.pyqtsignal_single_start.emit(self.single_or_cycle)
        else:
            QMessageBox.warning(self,'温度查询失败','请先连接串口!')   
    
    # 温度询问，判断后执行
    def Temperature_Ask_times_todo(self, single_or_cycle):
        if single_or_cycle:
            # 使用 Arduino ，产生随机数来测试
            # a = random.uniform(10, 30)
            # order = 'TC1:TCACTUALTEMP?'+str(round(a,2))+'\r'
            # 真实的指令不需要随机数
            # order = 'TC1:TCACTUALTEMP?'+'\r'
            """
            这里作为仿真代码，实际使用不需要预设
            """
            if self.tem_set_lcdNumber.value() - self.send_num > 2:
                self.send_num += Parameters_List[random.randint(0,len(Parameters_List)-1)]
            elif 0 < self.tem_set_lcdNumber.value() - self.send_num <= 2:
                self.send_num += Parameters_List[random.randint(0,1)]
            elif self.send_num - self.tem_set_lcdNumber.value() > 2:
                self.send_num -= Parameters_List[random.randint(0,len(Parameters_List)-1)]
            else:
                self.send_num -= Parameters_List[random.randint(0,1)]
            
            order = 'TC1:TCACTUALTEMP?'+str(self.send_num)+'\r'
            self.tx_lcdNumber.display(self.data_num_sended) 
            self.data_num_sended += len(order)
            self.QThread_Function.signal_sendData.emit(order)
        else:
            """
            这里作为仿真代码，实际使用不需要预设
            """
            if self.set_num - self.send_num > 2:
                self.send_num += Parameters_List[random.randint(0,len(Parameters_List)-1)]
            elif 0 < self.set_num - self.send_num <= 2:
                self.send_num += Parameters_List[random.randint(0,1)]
            elif self.send_num - self.set_num > 2:
                self.send_num -= Parameters_List[random.randint(0,len(Parameters_List)-1)]
            else:
                self.send_num -= Parameters_List[random.randint(0,1)]
                
            order = 'TC1:TCACTUALTEMP?'+str(self.send_num)+'\r'
            self.data_num_sended += len(order)
            self.QThread_Function.signal_sendData.emit(order)
    
    # 温度询问显示 
    def  Temperature_Ask_times_display(self,number):
        # 这里的number 就是反馈处理好的温度数值
        if number:
            if self.single_or_cycle:
                self.tem_real_lcdNumber.display(number)
                # 在这里发送设置温度回去
                self.Pyqtgraph_Function.psignal_pyqtgraph_tem_set.emit(self.tem_set_lcdNumber.value())
            else:
                # self.label_real_tem.setText(str(number))  实物操作使用
                # text = self.label_set_tem.text()
                # self.Pyqtgraph_Cycle_Function.signal_real_set_tem.emit(number,text)
                # 仿真发回去的实时温度值不是返回指令提取的！！！！！
                a = self.send_num
                self.label_real_tem.setText(str(round(a,2)))
                text = self.label_set_tem.text()
                self.Pyqtgraph_Cycle_Function.signal_real_set_tem.emit(str(self.send_num),text)  
        else:
            print("没有数字!")  
    
    # 温度设置框            
    def Temperature_set(self):
        if self.pushButton_open.text() == '关闭串口':
            tem_value = self.doubleSpinBox.value()
            tem_value = format(tem_value,'.2f')
            # 添加设置的温度数据到列表中
            self.tem_set_list.append(tem_value)
            self.tem_set_lcdNumber.display(tem_value) 
            try:
                self.tem_set_last_lcdNumber.display(self.tem_set_list[-2])
            except:
                self.tem_set_last_lcdNumber.display(0)    
            
            order = 'TC1:TCADJUSTTEMP='+str(tem_value)+'\r'
            """
            仿真不需要再发送
            """
            # self.QThread_Function.signal_sendData.emit(order)       
        else:
            QMessageBox.warning(self,'温度设置失败','请先连接串口!')
            
    # 发送端清空数据        
    def clear_send_num(self):
        self.data_num_sended = 0
        self.tx_lcdNumber.display(self.data_num_sended)
        self.tx_lineEdit.clear()
        
    # 接收端数据清空
    def clear_receive_num(self):
        self.data_num_received = 0
        self.rx_lcdNumber.display(self.data_num_received)
        self.rx_textBrowser.clear()   
    
    # 模式切换函数    
    def action_alter_theme_func(self):
        if self.dark_theme_flag:
            self.dark_theme_flag = False
            self.action_alter_theme.setIcon(QIcon('ico\sun.ico'))
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            title_widget.titleBar.setStyleSheet(Title_Style)
            self.toolBar.setStyleSheet("background-color: rgb(25,35,45);")
            
        else:
            app.setStyle('Fusion')
            app.setStyleSheet(StyleSheet)
            self.toolBar.setStyleSheet("background-color:rgb(83,157,186);") 
            self.dark_theme_flag = True
            self.action_alter_theme.setIcon(QIcon('ico\moon.ico'))
    
        
# 控件添加函数  
class MainWindow(QWidget):
      def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.main_interface = Main_Interface()
        layout.addWidget(self.main_interface) 
     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(StyleSheet)
    title_widget = FramelessWindow()
    title_widget.resize(QSize(980,728))
    title_widget.setTitleBarHeight(40)
    title_widget.setWindowIcon(QIcon(r'ico\pika.ico'))
    title_widget.setIconSize(40)
    title_widget.setWindowTitle('温 控 调 试 助 手')
    title_widget.titleBar.titleLabel.setMargin(325)
    title_widget.setWidget(MainWindow(title_widget))  
    
    palette = QPalette()
    pix = QPixmap("ico\hbj.jpg")
    pix = pix.scaled(1000, 700)
    palette.setBrush(QPalette.Background, QBrush(pix))
    app.setPalette(palette)
    
    title_widget.show()
    sys.exit(app.exec_())
