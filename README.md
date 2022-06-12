
# Temperature-Uart-7.0

## 1. 概要

Temperature-Uart-7.0 工程文件，创建了基于通讯协议 RS232 的温控串口助手，使用 Qt Designer 进行界面设计，pyqt5进行逻辑功能的完善，pyserial 进行串口通信，pyqtgraph 进行数据的可视化。

## 2. 文件夹功能分类
- dist 文件夹：存放将主文件 tiny_uart_main.py 打包完成的可执行文件。因为打包比较大这里就没有上传，可以直接运行 src 文件夹中的 packaging.py 文件生成。
- doc 文件夹：存放串口工具需要显示的文本内容。
- ico 文件夹：存放串口工具需要使用的图片背景以及相关图标。
- src 文件夹：存放程序代码文件，包含 .ui 文件，.py文件以及 .ini文件等。
		- .ui 文件： Qt Designer 生成的界面设计文件，一般需要再创建 .py 文件进行内容的完善
		- .py 文件：主要用于完善 .ui 文件以及功能代码的编写，程序文件的打包以及界面的美化等
		- .ini 文件：配置文件

## 3. 相关说明
- 各个程序文件逻辑功能分立，保证各司其职，便于后期维护。
- 关于线程的使用，主要用到了串口线程和绘图线程上。其中为了保证功能分立，绘图线程中同时创建了绘图部件 plotwidget，将绘图、数据处理同时完成后，统一直接加载到主文件中的布局结构中。因为采用了多线程，又要保持线程之间的协同工作，所以采用了较多的 pyqtsignal 信号来传递信号，具体说明已经在代码中标注过。
- 本人为大四电子类学生，能力有限，其它未尽事宜可以再与我联系，我的邮箱是 jwang_vxa@163.com ，也欢迎在b站关注 仰望星空的小王，私信或评论区联系，谢谢支持！

## 4. 相关参考
- 环境配置参考：https://www.bilibili.com/video/BV1YK4y1d7GS?spm_id_from=333.337.search-card.all.click&vd_source=57a45656425c8d443346df47430a6b37
- 自定义标题栏参考博客：[PyQt：无边框自定义标题栏及最大化最小化窗体大小调整 - JYRoy - 博客园 (cnblogs.com)](https://www.cnblogs.com/jyroy/p/9461317.html)
- 项目介绍视频：[pyqt5温控串口助手介绍_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1rL4y1K7Am?spm_id_from=333.337.search-card.all.click&vd_source=57a45656425c8d443346df47430a6b37)
