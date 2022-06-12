import time
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPalette, QBrush, QColor

class Pyqtgraph_Cycle_function(QThread):
    # 传递设置的温度列表，用以显示设置温度标签
    signal_set_tem_list = pyqtSignal(list)
    # 传递延时时间
    signal_dalay_time = pyqtSignal(int)
    # 传递计时开始信号
    signal_timer_start = pyqtSignal()
    # 传递计时结束信号
    signal_timer_stop = pyqtSignal()
    # 传递更换的温度值
    signal_alter_label_tem = pyqtSignal(int)
    # 传递实时和设置的单个值，集合成列表
    signal_real_set_tem = pyqtSignal(str, str)
    # 传递两个列表画图
    signal_real_set_tems_lists = pyqtSignal(list, list)
    # 删除信号
    signal_clear_lists = pyqtSignal()
    # 警告信号
    signal_warn_flag = pyqtSignal(bool)
    # 传递标签信号
    signal_label_notes = pyqtSignal(str)
    # 传递保存信号
    signal_cycle_save_files = pyqtSignal()
  
    def __init__(self):
        super().__init__()
        # 设置温度的列表
        self.set_tem_list = []
        # 实时设置的温度（动态）
        self.set_time_list = []
        # 实时温度的列表
        self.real_tem_list = []
        # 设置温度时间
        self.delay_time = 0
        # 计数相当于计时，从零开始
        self.count = 0
        # 循环绘图标志
        self.is_on = False
        # 警告标志，表示数据删除后点击 draw 不报错，仅仅初始时刻报错
        self.cycle_warn_flag = True
        
        self.plotwidget = pg.PlotWidget()
        # 背景透明化
        self.plotwidget.setBackground(background=None)
        
        # 用来计时
        self.timer = QTimer()
        self.timer.timeout.connect(self.label_alter_func)
      
        # 设置跟随鼠标移动的线
        # angle 控制线相对x轴正向的相对夹角
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setPen(pg.mkPen({'color': (146,146,246), 'width': 2}))
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.hLine.setPen(pg.mkPen({'color': (146,146,246), 'width': 2}))
        self.plotwidget.addItem(self.vLine, ignoreBounds=True)
        self.plotwidget.addItem(self.hLine, ignoreBounds=True) 
        
        # 设置鼠标移动的触发，限制速率，移动则触发 mouseMoved 函数
        self.proxy = pg.SignalProxy(self.plotwidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
        self.pyqtgraph_init()
        self.plotwidget_init()
    
    # 跟随鼠标移动，提取鼠标的横轴值，并定义纵轴的值显示
    def mouseMoved(self, evt):
        pos = evt[0]
        if self.plotwidget.sceneBoundingRect().contains(pos):
            mousePoint = self.plotwidget.plotItem.vb.mapSceneToView(pos)
            # 建议不用 int ，精度高时用 float，这样可以显示横坐标的小数
            index = int(mousePoint.x())
            if index > 0 and index < len(self.real_tem_list):
                 text = "<span style='color: rgb(155, 30, 100)'>time=%0.1f , </span><span style='color: rgb(67,178,68)'>real_tem=%0.1f</span> , <span style='color: red'>set_tem=%0.1f</span>" % (mousePoint.x(), self.real_tem_list[index], self.set_time_list[index])
                 self.signal_label_notes.emit(text)
            self.vLine.setPos(mousePoint.x()) 
            self.hLine.setPos(mousePoint.y())   
        
    # 发送改变标签的信号
    def timer_start_func(self):
        self.timer.start(1000) 
        
    def timer_stop_func(self):
        self.timer.stop() 
    
    # 发送标签
    def label_alter_func(self):
        if self.count < len(self.set_tem_list)*self.delay_time:
            self.count += 1
            # print(self.count)
            if self.count % self.delay_time == 0:
                index = self.count // self.delay_time
                try:
                    print(self.set_tem_list[index])
                    self.signal_alter_label_tem.emit(self.set_tem_list[index])
                except:
                    pass
        else:
            self.timer.stop()
    
    # 接收温度设置列表  
    def receive_tem_set_list(self, tem_list):
        self.set_tem_list = tem_list
        print(self.set_tem_list)
        
    # 接收延时时间
    def receive_delay_time(self, delay_time):
        self.delay_time = delay_time
        print(self.delay_time)
      
    # 收集实时温度数值    
    def collect_real_set_tem(self, real, set):
        # 放置设置温度列表
        self.set_time_list.append(int(set))
        # 实时温度的列表
        self.real_tem_list.append(float(real))
        
    def draw_tems(self, real_list, set_list):
        try:
            self.plotwidget.plot(real_list, pen=pg.mkPen({'color':QColor(67,178,68), 'width': 2}))
            self.plotwidget.plot(set_list, pen=pg.mkPen(color='r', width=1))
        except:
            pass
        
    def clear_cycle_lists(self):
        self.set_time_list = []
        self.real_tem_list = []
        self.plotwidget.clear()
        # 计数也要归零，不然影响下一次
        self.count = 0
        
        # 添加参考线
        self.plotwidget.addItem(self.vLine, ignoreBounds=True)
        self.plotwidget.addItem(self.hLine, ignoreBounds=True) 
    
    # 保存文件
    def multi_save_files(self):
        if self.set_time_list and self.real_tem_list:
            list_file  = list(zip(self.set_time_list, self.real_tem_list))
            file_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            file_path = "D:\Tiny Uart Data\Multi_Sets\{}.txt".format(file_name)
            with open(file_path, 'w') as file:
                for line in list_file:
                    for element in line:
                        file.write(str(element))
                        file.write('\t')
                    file.write('\n')       
            self.signal_warn_flag.emit(True)
        else:
            self.signal_warn_flag.emit(False) 
        
    # 绘图设置   
    def pyqtgraph_init(self):
        # 设置绘图背景色为灰色
        pg.setConfigOption('background',"#fffef8")
        # 设置前景（含坐标轴、线条、文本等）为黑色
        pg.setConfigOption('foreground','k')
        # 设置曲线看起来更光滑
        pg.setConfigOptions(leftButtonPan=True, antialias=True)
        
      # 设置图形属性
    def plotwidget_init(self):
         # 显示图形网络
        self.plotwidget.showGrid(x=True,y=True)
        label_style = {"color": "#9b1e64","font-family": "Consolas", "font-size":"12pt","font-weight":"bold","font-style":"italic"}
        self.plotwidget.setLabel(axis = 'left', text = 'Temperature', units='℃',  **label_style)
        self.plotwidget.getAxis('bottom').setLabel('Time (s)', **label_style)
        # 增加标题以及修改字体样式
        label_style_title = {"color": "#9b1e64", "size":"15pt", "bold":True, "italic":True, "font":"Consolas"}
        self.plotwidget.setTitle("Multi-target Temperature--Time Graph", **label_style_title)
        # 坐标轴字体更改
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        self.plotwidget.getAxis('left').setTickFont(font)
        self.plotwidget.getAxis('bottom').setTickFont(font)
        
    # 线程重复操作函数
    def run(self):
        while self.is_on:
            self.sleep(1)
            if self.set_time_list and self.real_tem_list:
                self.signal_real_set_tems_lists.emit(self.real_tem_list, self.set_time_list)
                # 调试使用
                # print(self.set_time_list)
                # print(self.real_tem_list)
            elif self.cycle_warn_flag:
                self.signal_warn_flag.emit(False)
                self.is_on = False
        