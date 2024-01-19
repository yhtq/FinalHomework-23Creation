from enum import Enum
from typing import Iterator
import core
from graph import Line, Point, LineType
from defines import *
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QMouseEvent, QGraphicsSceneMouseEvent
class Settings:
    # 分别表示每个格子的长宽，以及格子的数量
    WIDTH = 20
    HEIGHT = 20
    NUM_BLOCKS_X = 20
    NUM_BLOCKS_Y = 20

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
# immde_create 表示是否立刻创建对象，如果是则返回 point，否则返回坐标
def pos_attach(coor: Coordinate, immde_create: bool = False, name: str = None) -> tuple[list[core.BaseGraph], Coordinate | Point, AttachStatus]:
    line_attached_first: Line | None = None
    coor_line_attached_first: Coordinate | None = None
    (index_x, dis_x) = find_closest_grid_x(coor[0])
    (index_y, dis_y) = find_closest_grid_y(coor[1])
    x_index_attached: bool = dis_x < MinAttachDis
    y_index_attached: bool = dis_y < MinAttachDis
    if x_index_attached and y_index_attached:
        log(f"吸附到网格线 {index_x, index_y}", 2)
        if immde_create:
            point = core.create_point(coor=(index_x * Settings.WIDTH, index_y * Settings.HEIGHT), name=name)
            return ([], point, AttachStatus.GridAttached)
        else:
            return ([], (index_x * Settings.WIDTH, index_y * Settings.HEIGHT), AttachStatus.GridAttached)

    for i in core.active_set:
        (target, dis) = i.attachTo(coor)
        if dis < MinAttachDis:
            match i:
                case Point():
                    log(f"吸附到点 {i.getId()}", 2)
                    return ([i], target)
                case Line():
                    if x_index_attached or y_index_attached:
                        if immde_create:
                            if x_index_attached:
                                l1 = core.create_line_from_start_coor_and_direction(start=(index_x * Settings.WIDTH, 0), direction=(0, 1), hide=True, name=name)
                                point = core.get_cross(i, l1)
                            else:
                                l1 = core.create_line_from_start_coor_and_direction(start=(0, index_y * Settings.HEIGHT), direction=(1, 0), hide=True, name=name)
                                point = core.get_cross(i, l1)
                            if point is None:
                                log(f"吸附到线 {i.getId()} 但无交点", 4)
                                continue
                            return ([i, l1], point, AttachStatus.GridLineAttached)
                        else:
                            if x_index_attached:
                                cross_coor = i.crossDirection((index_x * Settings.WIDTH, 0), (1, 0), name = name)
                            else:
                                cross_coor = i.crossDirection((0, index_y * Settings.HEIGHT), (0, 1), name=name)
                            if cross_coor is None:
                                log(f"吸附到线 {i.getId()} 但无交点", 4)
                                continue
                            return ([i], cross_coor, AttachStatus.GridLineAttached)

                    elif line_attached_first is None:
                        line_attached_first = i
                        coor_line_attached_first = target
                    else:
                        if immde_create:
                            cross = core.get_cross(line_attached_first, i, name=name)
                            if cross is None:
                                log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()} 但无交点", 4)
                                continue
                            else:
                                log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()}", 2)
                                return ([line_attached_first, i], cross, AttachStatus.TwoLineAttached)
                        else:
                            cross_coor = line_attached_first.cross(i)
                            if cross_coor is None:
                                log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()} 但无交点", 4)
                                continue
                            else:
                                log(f"吸附到线 {line_attached_first.getId()} 和 {i.getId()}", 2)
                                return ([line_attached_first, i], cross_coor, AttachStatus.TwoLineAttached)
    if line_attached_first is not None:
        log(f"吸附到线 {line_attached_first.getId()} 上的点 {coor_line_attached_first}", 2)
        if immde_create:
            return ([line_attached_first], core.create_point(coor_line_attached_first, name=name), AttachStatus.OneLineAttached)
        else:
            return ([line_attached_first], coor_line_attached_first, AttachStatus.OneLineAttached)
    if immde_create:
        return ([], core.create_point(coor=coor, name=name), AttachStatus.NoneAttached)
    else:
        return ([], coor, AttachStatus.NoneAttached)

def defaultKeyPressEvent(event: QtGui.QKeyEvent):
    match event.key():
        case QtCore.Qt.Key.

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
        self.keyPressEvent 
    
    def draw_line(start: Coordinate, direction: DirectionVector, line_type: LineType):
        # 以指定参数画一条线，第二个参数意为方向向量（线段则起点到终点，射线则起点到方向向量，直线则只表示方向）
        TODO
    def draw_grid(self):
        for x in range(0,Settings.NUM_BLOCKS_X+1):
            xc = x * Settings.WIDTH
            self.draw_line((xc, 0), (0, 1), LineType.Infinite)
            self.draw_point((xc, 0))

        for y in range(0,Settings.NUM_BLOCKS_Y+1):
            yc = y * Settings.HEIGHT
            self.draw_line((0, yc), (1, 0), LineType.Infinite)
            self.draw_point((0, yc))

    def draw_all(self):
        # 画出所有的图形
        for i in core.active_set:
            match i:
                case Point():
                    self.draw_point(i.coor)
                case Line():
                    self.draw_line(i.start, i.direction, i.line_type)

mainWindow = QS()

# 画点
def create_point_tool(widget: QS = mainWindow):
    # 创建点的工具
    widget.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
    widget.setMouseTracking(True)
    def finish():
        widget.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        widget.setMouseTracking(False)
        widget.mouseMoveEvent = None
        widget.mousePressEvent = None
    def mouseMove(event: QMouseEvent):
        # 鼠标移动时，如果有吸附则画出吸附的点，否则画出鼠标位置
        print(event.x(), event.y())
        coor = pos_attach((event.x(), event.y()))[1]
        widget.draw_point(coor)
    def mouseClick(event: QMouseEvent):
        # 鼠标点击时，如果有吸附则创建点，否则创建鼠标位置的点
        log(f"鼠标点击 {event.x(), event.y()}", 2)
        coor = pos_attach((event.x(), event.y()), immde_create=True)[1]
        widget.draw_point(coor)
        finish()
    # 按 ESC 取消
    def keyPressEvent(event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            finish()
    widget.mouseMoveEvent = mouseMove
    widget.mousePressEvent = mouseClick
    widget.keyPressEvent = keyPressEvent

# 画线
def create_line_tool(widget: QS = mainWindow):
    #TODO
    pass

# 撤回
def undo():
    core.undo()

# 重做
def redo():
    core.redo()

# 这里可以再做一个指定路径的或者偷懒默认路径
def save():
    path = "save.txt"
    core.save(path)

def load():
    path = "save.txt"
    core.load(path)

