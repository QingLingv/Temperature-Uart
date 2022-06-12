import time
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSignal, QThread, QDateTime, QTimer
from PyQt5.QtGui import QFont, QColor
from collections import deque

class Pyqtgraph_function(QThread):
    # 传递实时温度和设置温度两条曲线的数据
    psignal_pyqtgraph_draw  = pyqtSignal(list,list)
    # 设置的温度数据传回来
    psignal_pyqtgraph_tem_set = pyqtSignal(float)
    # 警告信息的传递
    psignal_pyqtgraph_warning = pyqtSignal(bool)
    # 文件保存信号传递
    psignal_pyqtgraph_savefile = pyqtSignal()
    # 清除数据
    psignal_pyqtgraph_clear = pyqtSignal()
    # 发送状态栏时间日期信号
    psignal_pyqtgraph_timedate = pyqtSignal(str)
    # 发送横纵坐标轴对应的数值
    psignal_pyqtgraph_notes = pyqtSignal(str)
    # 传送滚动信号
    psignal_pyqtgraph_scroll = pyqtSignal(list)
    # 传送差值信号
    psignal_pyqtgraph_sub = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.pyqtgraph_init()
        # 线程开启标志
        self.is_on = False
        self.list_real_tem = []
        self.list_set_tem = []
        # 滚动计数
        self.count = 0
        self.count_bool = True
        self.subtraction = []
        # 队列保存十个值
        self.queue = deque(maxlen=10)
        
        # 警告标志，表示数据删除后点击 draw 不报错，仅仅初始时刻报错
        self.warn_flag = True
        
        self.plotwidget = pg.PlotWidget()
        self.plotwidget.setBackground(background=None)
        self.graphics = pg.GraphicsLayoutWidget() 
        self.graphics.setBackground(background=None)
        self.p1 = self.graphics.addPlot(row=1, col=1)
        self.p2 = self.graphics.addPlot(row=1, col=2)
       
        # 定义线性区域
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)
        self.plotwidget.addItem(self.region, ignoreBounds=True)
        
        self.region.sigRegionChanged.connect(self.update)
    
        # 设置初始的 region 位置
        self.region.setRegion([2, 6])
        
        # 设置跟随鼠标移动的线
        # angle 控制线相对x轴正向的相对夹角
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setPen(pg.mkPen({'color': (146,146,246), 'width': 2}))
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.hLine.setPen(pg.mkPen({'color': (146,146,246), 'width': 2}))
        self.p1.addItem(self.vLine, ignoreBounds=True)
        self.p1.addItem(self.hLine, ignoreBounds=True) 
        
        self.vb = self.p1.vb       
        
        # 设置鼠标移动的触发，限制速率，移动则触发 mouseMoved 函数
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
        self.plotwidget_init()
        self.statusShowtime_pre()
        self.little_plot()
        #self.little_plots_background()
        # self.plotwidget_background()
    
        
    # 子图设置    
    def little_plot(self):
        self.p1.setAutoVisible(y=True)
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(8)
        font.setBold(True)
        font.setItalic(True)
        self.p1.getAxis('left').setTickFont(font)
        self.p1.getAxis('bottom').setTickFont(font)
       
        self.p2.getAxis('left').setTickFont(font)
        self.p2.getAxis('bottom').setTickFont(font)
        
        label_style = {"color": "#9b1e64","font-family": "Consolas", "font-size":"10pt","font-weight":"bold","font-style":"italic"}
        self.p2.getAxis('left').setLabel('Difference/℃', **label_style)
        self.p2.getAxis('bottom').setLabel('Time/s', **label_style)
        
        self.p1.sigRangeChanged.connect(self.updateRegion)
        label_style_title = {"color": "#9b1e64", "size":"12pt", "bold":True, "italic":True, "font":"Consolas"}
        self.p2.setTitle("Residual Plot", **label_style_title)
        
    # 跟随鼠标移动，提取鼠标的横轴值，并定义纵轴的值显示
    def mouseMoved(self, evt):
        pos = evt[0]
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            # 建议不用 int ，精度高时用 float，这样可以显示横坐标的小数
            index = int(mousePoint.x())
            if index > 0 and index < len(self.list_real_tem):
                 text = "<span style='color: rgb(155, 30, 100);'>time=%0.1f , </span><span style='color: rgb(14, 176, 201)'>real_tem=%0.1f</span> , <span style='color: red'>set_tem=%0.1f</span>" % (mousePoint.x(), self.list_real_tem[index], self.list_set_tem[index])
                 self.psignal_pyqtgraph_notes.emit(text)
            self.vLine.setPos(mousePoint.x()) 
            self.hLine.setPos(mousePoint.y())   

    # 设置原图放大区域被移动后的触发函数
    def update(self):
        self.region.setZValue(10)
        # # 调整放大区域的横轴显示区域坐标
        minX, maxX = self.region.getRegion()  
        self.p1.setXRange(minX, maxX, padding=0)
    
    # 线性区域更新
    def updateRegion(self, window, viewRange):
        rgn = viewRange[0]
        self.region.setRegion(rgn)
    
    # 差值图更新
    def draw_substractions(self, list_de): 
        global curve
        if self.count_bool:
            curve  = self.p2.plot(list_de, pen='m')
            self.count_bool = False
        for element in list_de:
            element = round(element, 2)
            self.queue.append(element)
        list_queue = list(self.queue)
        self.psignal_pyqtgraph_sub.emit(list_queue[-1])
        # 条件衡量
        if abs(list_queue[-1]) < 1:
            pass
        curve.setData(list_queue)
        self.count += 1 
        curve.setPos(self.count-8, 0)   
            
    # 开始绘图，需要把数据传过来   
    def pyqtgraph_draw(self,list_y1,list_y2):
        self.subtraction = list(map(lambda x: x[0]-x[1], zip(list_y1, list_y2)))
        self.psignal_pyqtgraph_scroll.emit(self.subtraction)
        try:  
            self.p1.plot(list_y1, pen=pg.mkPen({'color': QColor(14, 176, 201), 'width': 1}))
            self.p1.plot(list_y2, pen='r')
            self.plotwidget.plot(list_y1, pen=pg.mkPen({'color':QColor(14, 176, 201), 'width': 2}))
            self.plotwidget.plot(list_y2, pen=pg.mkPen(color='r', width=1))
        except:
            pass
    
    # 绘图设置   
    def pyqtgraph_init(self):
        # 设置前景（含坐标轴、线条、文本等）为黑色
        pg.setConfigOption('foreground', QColor(155, 30, 100))
        # 设置曲线看起来更光滑
        pg.setConfigOptions(leftButtonPan=True, antialias=True)
        # 设置绘图背景色为灰色
        pg.setConfigOption('background',"w")
        
    # 设置图形属性
    def plotwidget_init(self):
         # 显示图形网络
        self.plotwidget.showGrid(x=True,y=True)
        # self.plotwidget.setLabel(axis = 'left', text = 'temperature', units='℃')
        # self.plotwidget.setLabel(axis = 'bottom', text = 'second', units='s')
        label_style = {"color": "#9b1e64","font-family": "Consolas", "font-size":"12pt","font-weight":"bold","font-style":"italic"}
        # self.plotwidget.getAxis('left').setLabel('Temperature (℃)', **label_style)
        self.plotwidget.setLabel(axis = 'left', text = 'Temperature', units='℃',  **label_style)
        self.plotwidget.getAxis('bottom').setLabel('Time (s)', **label_style)
        # 增加标题以及修改字体样式
        label_style_title = {"color": "#9b1e64", "size":"15pt", "bold":True, "italic":True, "font":"Consolas"}
        self.plotwidget.setTitle("Temperature——Time Graph", **label_style_title)
        # 坐标轴字体更改
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        self.plotwidget.getAxis('left').setTickFont(font)
        self.plotwidget.getAxis('bottom').setTickFont(font)
       
    # 数据清除设置    
    def clear_lists(self):
        self.list_real_tem = []
        self.list_set_tem = []
        self.subtraction = []
        self.warn_flag = False
        self.plotwidget.clear()
        self.p1.clear()
        self.p2.clear()
        
        # 应当注意，删去图画之后，有些默认操作要还原
        self.plotwidget.addItem(self.region, ignoreBounds=True)
        self.p1.addItem(self.vLine, ignoreBounds=True)
        self.p1.addItem(self.hLine, ignoreBounds=True) 
        self.region.setRegion([2, 6])
        self.count_bool = True
        self.count = 0
    
    # 当前时间显示
    def showCurrentTime(self):
        time_current = QDateTime.currentDateTime()
        timeDisplay = time_current.toString('yyyy-MM-dd hh:mm:ss dddd')
        self.psignal_pyqtgraph_timedate.emit(timeDisplay)
    
    # 定时器更新时间
    def statusShowtime_pre(self):
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.showCurrentTime())
        self.timer.start(1000)  
    
    # 保存文件设置    
    def save_file(self):
        if self.list_set_tem and self.list_real_tem:
            list_file  = list(zip(self.list_set_tem, self.list_real_tem))
            # print(list_file)
            file_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            # file_path = "data//{}.txt".format(file_name)
            # with open(file_path, 'w') as file:
            #     for line in list_file:
            #         for element in line:
            #             file.write(str(element))
            #             file.write('\t')
            #         file.write('\n') 
            file_path = "D:\Tiny Uart Data\Single_Set\{}.txt".format(file_name)
            with open(file_path, 'w') as file:
                for line in list_file:
                    for element in line:
                        file.write(str(element))
                        file.write('\t')
                    file.write('\n')       
            self.psignal_pyqtgraph_warning.emit(True)
        else:
            self.psignal_pyqtgraph_warning.emit(False)
    
    # 实时温度列表更新           
    def recv_list_real_tem(self,numbers):
        self.number = float(numbers)
        self.list_real_tem.append(self.number) 
    
    # 设置温度更新列表     
    def recv_list_set_tem(self,ys_numbers):
        self.list_set_tem.append(ys_numbers)       
    
    # 线程重复操作函数
    def run(self):
        while self.is_on:
            self.sleep(1) 
            if self.list_real_tem and self.list_set_tem:
                self.psignal_pyqtgraph_draw.emit(self.list_real_tem,self.list_set_tem)
                # 调试使用
                # print(self.list_real_tem)
                # print(self.list_set_tem)
            elif self.warn_flag:
                self.psignal_pyqtgraph_warning.emit(False)
                self.is_on = False
            