from copy import copy
from enum import Enum
from functools import partial
from typing import Iterator
import core
from graph import Line, Point, LineType, BaseGraph
from defines import *
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QEvent, QPoint
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QPaintEvent

def find_closest_grid_x(x: float) -> (int, float):
    index = round(x / Settings.WIDTH)
    if index < 0:
        index = 0
    elif index > Settings.NUM_BLOCKS_X:
        index = Settings.NUM_BLOCKS_X
    return (index, abs(x -index * Settings.WIDTH))
def find_closest_grid_y(y: float) -> (int, float):
    index = round(y / Settings.HEIGHT)
    if index < 0:
        index = 0
    elif index > Settings.NUM_BLOCKS_Y:
        index = Settings.NUM_BLOCKS_Y
    return (index, abs(y -index * Settings.HEIGHT))

class AttachStatus(Enum):
    NoneAttached = 0,
    PointAttached = 1,
    OneLineAttached = 2,
    TwoLineAttached = 3,
    GridLineAttached = 4,
    GridAttached = 5

# 尝试将位置吸附至（活跃的）对象。策略为：
# 优先吸附点，若同时吸附到多点则随机选择一个
# 再考虑线，若同时吸附到多线则随机选择两个吸附到交点。线包括活跃对象中的线或者网格线（吸附到网格线不返回对象）
# 若吸附成功则返回吸附的坐标和对象，否则返回 None。如果吸附到交点，会返回两条直线和交点坐标
# immde_create 表示是否立刻创建对象，如果是则返回 point，否则返回坐标。吸附到点时会返回该点，否则新创建点
def pos_attach(coor: Coordinate, immde_create: bool = False, name: str = None) -> tuple[list[core.BaseGraph], Coordinate | Point, AttachStatus]:
    line_attached_first: Line | None = None
    coor_line_attached_first: Coordinate | None = None
    (index_x, dis_x) = find_closest_grid_x(coor[0])
    (index_y, dis_y) = find_closest_grid_y(coor[1])
    x_index_attached: bool = dis_x < MinAttachDis
    y_index_attached: bool = dis_y < MinAttachDis
    grid_attached = None
    grid_line_attached = None
    if x_index_attached and y_index_attached:
        if immde_create:
            point = core.create_point(coor=(index_x * Settings.WIDTH, index_y * Settings.HEIGHT), name=name)
            grid_attached = ([], point, AttachStatus.GridAttached)
        else:
            grid_attached = ([], (index_x * Settings.WIDTH, index_y * Settings.HEIGHT), AttachStatus.GridAttached)
    ori_active_set = copy(core.active_set)
    # 这是为了防止创建对象时发生迭代器失效的问题
    for i in ori_active_set:
        (target, dis) = i.attachTo(coor)
        if dis < MinAttachDis:
            match i:
                case Point():
                    log(f"吸附到点 {i.getId()}", 2)
                    if immde_create:
                        return ([i], i, AttachStatus.PointAttached)
                    else:
                        return ([i], i.coor, AttachStatus.PointAttached)
                case Line():
                    if x_index_attached or y_index_attached:
                        if immde_create:
                            if x_index_attached:
                                # l1 将网格线实例化从而得到交点
                                l1 = core.create_line_from_start_coor_and_direction(start=(index_x * Settings.WIDTH, 0), direction=(0, 1), hide=True, name=name, line_type=LineType.Infinite)
                                (point, status) = core.get_cross(i, l1, hide=True)
                            else:
                                l1 = core.create_line_from_start_coor_and_direction(start=(0, index_y * Settings.HEIGHT), direction=(1, 0), hide=True, name=name, line_type=LineType.Infinite)
                                (point, status) = core.get_cross(i, l1, hide=True)
                            match status:
                                case Line.CrossStatus.Parallel | Line.CrossStatus.CrossPointNotOnLine:
                                    log(f"吸附到线 {i.getId()} 但无交点", 4)
                                    line_attached_first = i
                                    coor_line_attached_first = target
                                case Line.CrossStatus.Coincide:
                                    log(f"吸附到线 {i.getId()} 但重合", 4)
                                    line_attached_first = i
                                    coor_line_attached_first = target
                                case Line.CrossStatus.Cross:
                                    log(f"吸附到线 {i.getId()} 且有交点 {point}", 4)
                                    line_attached_first = i
                                    coor_line_attached_first = target
                                    grid_line_attached = ([i], point, AttachStatus.GridLineAttached)
                        else:
                            if x_index_attached:
                                (cross_coor, cross_status) = i.crossDirection((index_x * Settings.WIDTH, 0), (0, 1))
                                log(f"吸附到线 {i.getId()} 与 x 网格线 {index_x} ", 4)
                            else:
                                (cross_coor, cross_status) = i.crossDirection((0, index_y * Settings.HEIGHT), (1, 0))
                                log(f"吸附到线 {i.getId()} 与 y 网格线 {index_y} ", 4)
                            match cross_status:
                                case Line.CrossStatus.Parallel | Line.CrossStatus.CrossPointNotOnLine:
                                    log(f"但无交点", 4)
                                    line_attached_first = i
                                    coor_line_attached_first = target
                                case Line.CrossStatus.Coincide:
                                    log(f"与网格线重合", 4)
                                    line_attached_first = i
                                    coor_line_attached_first = target
                                case Line.CrossStatus.Cross:
                                    log(f"且有交点 {cross_coor}", 4)
                                    #return ([i], cross_coor, AttachStatus.GridLineAttached)
                                    grid_line_attached = ([i], cross_coor, AttachStatus.GridLineAttached)

                    elif line_attached_first is None:
                        line_attached_first = i
                        coor_line_attached_first = target
                        log(f"吸附到第一条线 {i.getId()}", 4)
                    else:
                        if immde_create:
                            (cross, cross_status) = core.get_cross(line_attached_first, i, name=name)
                        else:
                            (cross_coor, cross_status) = line_attached_first.cross(i)
                            match cross_status:
                                case Line.CrossStatus.Parallel | Line.CrossStatus.CrossPointNotOnLine:
                                    log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()} 但无交点", 4)
                                    continue
                                case Line.CrossStatus.Coincide:
                                    log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()} 但重合", 4)
                                    continue
                                case Line.CrossStatus.Cross:
                                    log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()}", 4)
                                    if immde_create:
                                        return ([line_attached_first, i], cross, AttachStatus.TwoLineAttached)
                                    else:
                                        return ([line_attached_first, i], cross_coor, AttachStatus.TwoLineAttached)
    if grid_line_attached is not None:
        if immde_create:
            core.set_active(grid_line_attached[1])
        return grid_line_attached
    if line_attached_first is not None:
        log(f"吸附到线 {line_attached_first.getId()} 上的点 {coor_line_attached_first}", 4)
        if immde_create:
            return ([line_attached_first], core.create_point(coor=coor_line_attached_first, name=name), AttachStatus.OneLineAttached)
        else:
            return ([line_attached_first], coor_line_attached_first, AttachStatus.OneLineAttached)
    if grid_attached is not None:
        log(f"吸附到网格线 {index_x, index_y}", 2)
        return grid_attached
    if immde_create:
        return ([], core.create_point(coor=coor, name=name), AttachStatus.NoneAttached)
    else:
        return ([], coor, AttachStatus.NoneAttached)

#def defaultKeyPressEvent(event: QtGui.QKeyEvent):
    #match event.key():
        #case QtCore.Qt.Key.

# 初始的方格，来自 https://stackoverflow.com/questions/39614777/how-to-draw-a-proper-grid-on-pyqt
class QS(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        width = Settings.NUM_BLOCKS_X * Settings.WIDTH
        height = Settings.NUM_BLOCKS_Y * Settings.HEIGHT
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)
        self.setWindowTitle("Grapher")
        self.draw_point_button = QtWidgets.QPushButton("画点")
        self.draw_line_button = QtWidgets.QPushButton("画直线")
        self.draw_ray_button = QtWidgets.QPushButton("画射线")
        self.draw_segment_button = QtWidgets.QPushButton("画线段")
        self.undo_button = QtWidgets.QPushButton("撤回")
        self.redo_button = QtWidgets.QPushButton("取消撤回")
        self.save_button = QtWidgets.QPushButton("保存")
        self.load_button = QtWidgets.QPushButton("加载")
        self.print_button = QtWidgets.QPushButton("发送至设备")
        self.draw_point_button.clicked.connect(self.create_point_tool)
        self.draw_line_button.clicked.connect(partial(self.create_line_tool, LineType.Infinite))
        self.draw_ray_button.clicked.connect(partial(self.create_line_tool, LineType.Ray))
        self.draw_segment_button.clicked.connect(partial(self.create_line_tool, LineType.Segment))
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.save_button.clicked.connect(self.save)
        self.load_button.clicked.connect(self.load)
        self.print_button.clicked.connect(self.send_to_device)
        self.layout = QtWidgets.QVBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.draw_point_button)
        self.buttonLayout.addWidget(self.draw_line_button)
        self.buttonLayout.addWidget(self.draw_ray_button)
        self.buttonLayout.addWidget(self.draw_segment_button)
        self.buttonLayout.addWidget(self.undo_button)
        self.buttonLayout.addWidget(self.redo_button)
        self.buttonLayout.addWidget(self.save_button)
        self.buttonLayout.addWidget(self.load_button)
        self.buttonLayout.addWidget(self.print_button)
        self.layout.addLayout(self.buttonLayout)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
        self.setLayout(self.layout)
        self.temp_point: Coordinate | None = None
        self.temp_line: (Coordinate, DirectionVector, LineType) | None = None
        self.selected_id: Id | None = None
        self.mouseMoveEvent = self.__mouseMoveEvent
        self.mousePressEvent = self.__mousePressEvent
        self.keyPressEvent = self.__keyPressEvent
    
    def send_to_device(self):
        # 将需要的数据发送到机械臂进行绘制
        for i in core.active_set:
            if isinstance(i, Line):
                if i.line_type == LineType.Segment:
                    if i.start is None or i.direction is None:
                        continue
                    start: Coordinate = i.start.coor
                    direction: DirectionVector = i.direction
                    end: Coordinate = (start[0] + direction[0], start[1] + direction[1])
                    # 这里写画线段的代码就行，或者独立出一个函数

    def __mousePressEvent(self, event: QMouseEvent) -> None:
        (x, y) = event.pos().x(), event.pos().y()
        print(f"鼠标点击 {x, y}")
        obj_list = pos_attach((x, y))[0]
        if len(obj_list) == 0:
            print("未选中任何对象")
            self.selected_id = None
        else:
            print(f"选中 {obj_list[0].getId()}")
            self.selected_id = obj_list[0].getId()
        self.update()
    def __mouseMoveEvent(self, event: QMouseEvent) -> None:
        (x, y) = event.pos().x(), event.pos().y()
        print(f"鼠标移动 {x, y}")
        if self.selected_id is not None:
            obj = BaseGraph.findObjectById(self.selected_id)
            if obj is None:
                print("选中的对象不存在")
                self.selected_id = None
            elif isinstance(obj, Point):
                #new_coor = pos_attach((x, y))[1]
                core.modify_point(obj, (x, y))
                self.update()
    def __keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == QtCore.Qt.Key.Key_Delete:
            if self.selected_id is not None:
                core.delete(self.selected_id)
                self.selected_id = None
                self.update()

    def action_finish(self):
        self.temp_point = None
        self.temp_line = None
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.setMouseTracking(False)
        self.mouseMoveEvent = None
        self.mousePressEvent = self.__mousePressEvent
        self.keyPressEvent = self.__keyPressEvent
        self.mouseMoveEvent = self.__mouseMoveEvent
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        self.painter = QtGui.QPainter(self)
        self.draw_all(self.painter)
        self.painter.end()

    def draw_point(self, coor: Coordinate | None, painter, color = QtCore.Qt.GlobalColor.black) -> None:
        # 以指定坐标画一个点
        pen = QtGui.QPen(color, 2, QtCore.Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(color, QtCore.Qt.BrushStyle.SolidPattern))
        if coor is not None:
            painter.drawEllipse(QPoint(int(coor[0]), int(coor[1])), 5, 5)

    def draw_line(self, start: Coordinate | None, direction: DirectionVector | None, line_type: LineType, painter, 
                  color=QtCore.Qt.GlobalColor.black,
                    width=2,
                  ):
        # 以指定参数画一条线，第二个参数意为方向向量（线段则起点到终点，射线则起点到方向向量，直线则只表示方向）
        if start is None or direction is None:
            return
        pen = QtGui.QPen(color, width, QtCore.Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        line1 = QtCore.QLineF(start[0], start[1], start[0] + direction[0] , start[1] + direction[1] )
        match line_type:
            case LineType.Infinite:
                line2 = QtCore.QLineF(start[0], start[1], start[0] - direction[0] , start[1] - direction[1] )
                line1.setLength(RefSize)
                line2.setLength(RefSize)
                line = QtCore.QLineF(line1.p2(), line2.p2())
            case LineType.Ray:
                line1.setLength(RefSize)
                line = line1
            case LineType.Segment:
                line = line1
        painter.drawLine(line)

    def draw_grid(self, painter):
        for x in range(0,Settings.NUM_BLOCKS_X+1):
            xc = x * Settings.WIDTH
            self.draw_line((xc, 0), (0, 1), LineType.Infinite, painter, color=QtCore.Qt.GlobalColor.gray, width=1)
            #self.draw_point((xc, 0), painter)

        for y in range(0,Settings.NUM_BLOCKS_Y+1):
            yc = y * Settings.HEIGHT
            self.draw_line((0, yc), (1, 0), LineType.Infinite, painter, color=QtCore.Qt.GlobalColor.gray, width=1)
            #self.draw_point((0, yc), painter)
        self.draw_point((XSize / 2, YSize / 2), painter)

    def draw_all(self, painter):
        # 画出所有的图形
        self.draw_grid(painter)
        for i in core.active_set:
            if i.getId() == self.selected_id:
                color = QtCore.Qt.GlobalColor.red
            else:
                color = QtCore.Qt.GlobalColor.black
            match i:
                case Point():
                    self.draw_point(i.coor, painter, color=color)
                case Line():
                    self.draw_line(i.start.coor, i.direction, i.line_type, painter, color=color)
        if self.temp_point is not None:
            self.draw_point(self.temp_point, painter)
        if self.temp_line is not None:
            (start, direction, line_type) = self.temp_line
            self.draw_line(start, direction, line_type, painter)

    # 画点
    def create_point_tool(self):
        # 创建点的工具
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)
        def mouseMove(event: QMouseEvent):
            # 鼠标移动时，如果有吸附则画出吸附的点，否则画出鼠标位置
            (x, y) = event.pos().x(), event.pos().y()
            print(f"鼠标移动 {x, y}")
            coor = pos_attach((x, y))[1]
            self.temp_point = coor
            self.update()
        def mouseClick(event: QMouseEvent):
            # 鼠标点击时，如果有吸附则创建点，否则创建鼠标位置的点
            (x, y) = event.pos().x(), event.pos().y()
            log(f"鼠标点击 {x, y}", 2)
            coor = pos_attach((x, y), immde_create=True)[1]
            self.update()
            self.action_finish()
        # 按 ESC 取消
        def keyPressEvent(event: QtGui.QKeyEvent):
            if event.key() == QtCore.Qt.Key.Key_Escape:
                self.action_finish()
        self.mouseMoveEvent = mouseMove
        self.mousePressEvent = mouseClick
        self.keyPressEvent = keyPressEvent

    # 画线
    def create_line_tool(self, line_type: LineType):
        # 创建线的工具
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)
        first_point: Coordinate | None = None
        def mouseMove(event: QMouseEvent):
            nonlocal first_point
            (x, y) = event.pos().x(), event.pos().y()
            coor = pos_attach((x, y))[1]
            if first_point is None:
                # 先画第一个点
                self.temp_point = coor
                self.update()
            else:
                # 画线
                self.temp_line = (first_point, (coor[0] - first_point[0], coor[1] - first_point[1]), line_type)
                self.update()
        def mouseClick(event: QMouseEvent):
            nonlocal first_point
            (x, y) = event.pos().x(), event.pos().y()
            coor = pos_attach((x, y))[1]
            if first_point is None:
                # 先画第一个点
                first_point = coor
                self.update()
            else:
                # 画线
                start = pos_attach(first_point, immde_create=True)[1]
                end = pos_attach(coor, immde_create=True)[1]
                core.create_line_from_start_point_and_end_point(start=start, end=end, line_type=line_type)
                self.update()
                self.action_finish()
        # 按 ESC 取消
        def keyPressEvent(event: QtGui.QKeyEvent):
            if event.key() == QtCore.Qt.Key.Key_Escape:
                self.action_finish()
        self.mouseMoveEvent = mouseMove
        self.mousePressEvent = mouseClick
        self.keyPressEvent = keyPressEvent


    # 撤回
    def undo(self):
        core.undo()
        self.update()

    # 重做
    def redo(self):
        core.redo()
        self.update()

    # 这里可以再做一个指定路径的或者偷懒默认路径
    def save(self):
        path = "save"
        core.save(path)

    def load(self):
        core.runtime_reset()
        path = "save"
        core.load(path)
        self.update()
qapp = QtWidgets.QApplication([])
mainWindow = QS()
mainWindow.show()
qapp.exec()

