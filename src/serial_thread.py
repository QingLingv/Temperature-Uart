import serial
import threading
import re
from PyQt5.QtCore import pyqtSignal, QObject, QTimer


class Qthread_function(QObject):
    # 这个信号用来开启启动函数
    signal_Serialstart = pyqtSignal()
    # 用来表示串口打开按钮
    signal_pushButton_Open = pyqtSignal(object)
    # 发个信号给 ui ，通知打开状态
    signal_pushButton_Open_flag = pyqtSignal(object)
    # 把接收的数据传到ui界面来处理
    signal_readData = pyqtSignal(object)
    # 接收数据再处理，筛选用
    signal_readData_disposal = pyqtSignal(object)
    # 发送信号创建
    signal_sendData = pyqtSignal(object)
    # 传递串口线程的id
    signal_serial_id = pyqtSignal(object)
    
    def __init__(self,parent=None):
        super().__init__(parent)
        
        self.state = 0 # 0:未打开 1:串口已经打开 2：串口已经关闭
        self.serial_ID = ''
        # 定时接收数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.receive_data)
     
    # 串口打开配置 
    def slot_pushButton_Open(self,parameter):
        if self.state == 0:
            self.ser.port = parameter['comboBox_uart']
            self.ser.baudrate = int(parameter['comboBox_baud'])
            self.ser.bytesize = int(parameter['comboBox_data'])
            self.ser.stopbits = int(parameter['comboBox_stop'])
            self.ser.parity = parameter['comboBox_check']
        
            try:
                self.ser.open()
                self.state = 1
                self.signal_pushButton_Open_flag.emit(self.state)
            except:
                self.signal_pushButton_Open_flag.emit(0)
                print("打开串口失败!")
                
            if self.ser.isOpen():
                # 启动接收数据
                self.timer.start(100)
        else:
            print("串口关闭")
            self.state = 0
            self.timer.stop()
            try:
                self.ser.close()
                self.signal_pushButton_Open_flag.emit(2)
            except:
                pass
    
    # 串口线程初始化            
    def SerialInit_func(self):
        self.serial_ID = str(threading.currentThread().ident)
        print("串口线程ID:",self.serial_ID)
        serial_ID = 'Serial ID:' + self.serial_ID
        self.signal_serial_id.emit(serial_ID)
        self.ser = serial.Serial()

    # 串口线程数据接收
    def receive_data(self):
        length = 0
        if self.ser.isOpen():
            try:
                # 获取接收到的数据长度
                num = self.ser.inWaiting()
            except:
                self.timer.stop()
                self.ser.close()
                return
            if num > 0:
                # data = self.ser.read_all()
                data = self.ser.read(num)
                length = len(data)
                  
            n = self.ser.inWaiting()
            length = length + n
            if length > 0 and n == 0:
                try:
                    # 统计接收字符的数量
                    self.signal_readData.emit(data) 
                except:
                    print('读取不完全')
    
    # 对读取的数据进行处理                
    def slot_readData_disposal(self, data):
        # 变回字符串
        data = data.decode('UTF-8')
        data_list = re.findall(r"\d+.?\d*",data)
        if data_list:
            # 列表中有值
            try:
                number_lcd = float(data_list[1])
                number_lcd = format(number_lcd,'.2f')

                self.signal_readData_disposal.emit(number_lcd)
            except:
                pass
        # 初始空列表，就置零
        else:
            pass
    
    # 发送数据函数
    def slot_sendData(self,send_data):
        if self.state != 1:
            return 
        # 调整数据格式
        send_data = send_data.encode('utf-8')
        self.ser.write(send_data)
        pass

