from enum import Enum
from functools import lru_cache, singledispatch, singledispatchmethod
from io import TextIOWrapper
from typing import Any, Concatenate, Final, Literal, Optional
from collections.abc import Callable
import PyQt6 as Qt
import weakref as wr
import re
import sys
from defines import *
# 本文件定义了支持的几何对象类，包括点、线、圆
type DependencySet = set["BaseGraph"]
# 格式为 set(111, 222)
def dependencySetToStr(dependency: DependencySet) -> str:
    res = ", ".join([i.getId() for i in dependency])
    return f"set({res})" if res != "" else "set()"
def buildDependencyTreeFromStr(dependency_str: str) -> DependencySet:
    res = set()
    for i in dependency_str.split(","):
        i = i.strip()
        if i == "":
            continue
        res.add(BaseGraph.findObjectById(i))
    return res
def add(first: Coordinate, second: Coordinate) -> Coordinate:
    return (first[0] + second[0], first[1] + second[1])
def sub(first: Coordinate, second: Coordinate) -> Coordinate:
    return (first[0] - second[0], first[1] - second[1])
def mul(first: Coordinate, second: Coordinate) -> Coordinate:
    return (first[0] * second[0], first[1] * second[1])
class BaseGraph:
    # id 计数器
    __objectId: Id = 0
    # 这里由于 BaseGraph 的 name 未创建，必须使用 "BaseGraph" 进行标注
    # 对所有对象存储一个弱引用，也即对象存活时允许访问，但不影响引用计数。该字典会在对象析构时自动删除对象的键
    __idToObject: wr.WeakValueDictionary[Id, 'BaseGraph'] = wr.WeakValueDictionary()
    # 对象的名字（若有）
    __idToName: wr.WeakValueDictionary[Id, str] = wr.WeakValueDictionary()
    # 注意为了安全性起见所有构造函数的参数都应该是关键字参数
    def __init__(self,* , name: Optional[str] = None, id: Optional[Id] = None):
        if id is not None:
            if id in BaseGraph.__idToObject or id in BaseGraph.__idToName:
                raise Exception("id 重复")
            self.id = id
        else:
            self.id: Id = BaseGraph.__objectId
            BaseGraph.__objectId += 1
            BaseGraph.__objectId %= MaxId
            if BaseGraph.__objectId in BaseGraph.__idToObject:
                raise Exception("id 溢出并产生冲突")
        if name is not None:
            BaseGraph.__idToName[self.id] = name
        # 注意 Python 对于类变量默认传入引用，因此这里只是传入了弱引用
        BaseGraph.__idToObject[self.id] = self
        log(f"创建 {self.getTypeName()} 对象 id={self.id}", 5)
    def getTypeName(self):
        raise NotImplementedError
    def getId(self) -> int:
        return self.id
    def getName(self) -> Optional[str]:
        return BaseGraph.__idToName.get(self.id, None)
    class ErrorCommand(Exception):
        def __init__(self, command: str):
            super().__init__(f"{self.getTypeName} 类型命令格式错误: {command}")
    # 生成创建对象的命令字符串
    def objectToCommand(self) -> str:
        raise NotImplementedError
    # 试图通过弱引用全局字典找到对象，找不到则返回 None
    @staticmethod
    def findObjectById(id: Id) -> Optional['BaseGraph']:
        return BaseGraph.__idToObject.get(id, None)
    @staticmethod
    # 从命令字符串中解析出对象
    @staticmethod
    def commandToObject(command: str):
        log(f"尝试以命令 {command} 创建 {self.getTypeName} 对象", 4)
        try:
            # 注意我们的生成命令字符串就是 Python 构造函数的格式，可以直接 eval。当然这里会有安全风险但是在此先不考虑
            dependecy_str = re.search(r"dependency=set\((.*)\)", command).group(1)
            dependency_set = buildDependencyTreeFromStr(dependecy_str)
            command = re.sub(r"dependency=set\(.*\)", "dependency=dependency_set", command)
            return eval(command)
        except Exception as e:
            raise Point.ErrorCommand(command = command) from e
    def draw(self, painter: Qt.QtGui.QPainter):
        raise NotImplementedError
    # 返回可能吸附的最近点以及两点间的距离
    def attachTo(self, coor: Coordinate) -> (Coordinate, float):
        raise NotImplementedError
    # 检测指定点是否在对象上
    def on(self, coor: Coordinate) -> bool:
        (_, dis) = self.attachTo(coor)
        log(f"检测位置 {coor} 是否在 {self.objectToCommand()} 上，距最近点距离为：{dis}", 1)
        return dis < MinDis
    # 返回依赖的对象的引用
    def dependencyObject(self) -> DependencySet:
        raise NotImplementedError
    def __del__(self):
        log(f"析构 {self.getTypeName()} 对象 id={self.id}", 5)
@singledispatch
def getDistanceToCoor(first: Any, other: Coordinate) -> float:
    raise NotImplementedError
@getDistanceToCoor.register
def getDistanceToCoor(first: Coordinate, other: Coordinate) -> float:
    return ((first[0] - other[0])**2 + (first[1] - other[1])**2)**0.5
    
class Point(BaseGraph):
    # 注意为了安全性起见所有构造函数的参数都应该是关键字参数
    def __init__(self, *, coor: Coordinate, dependency: DependencySet = set(), name: Optional[str] = None, id: Id = None):
        super().__init__(name, id)
        self.coor: Coordinate = coor
        self.dependency: DependencySet = dependency
    def getTypeName(self) -> Literal['Point']:
        return "Point"
    @lru_cache
    def objectToCommand(self) -> str:
        name: str | None = self.getName()
        id: Id = self.getId()
        dependency_str = dependencySetToStr(self.dependency)
        res = f"Point (coor={self.coor}, name={name}, id={id}, dependency={dependency_str})"
        return res

    def draw(self, painter: Qt.QtGui.QPainter):
        #painter.setPen(Qt.QtGui.QPen(Qt.QtCore.Qt.GlobalColor.black))
        #painter.drawPoint(self.coor[0], self.coor[1])
        #TODO
        pass
    def __sub__(self, other: 'Point') -> DirectionVector:
        return (self.coor[0] - other.coor[0], self.coor[1] - other.coor[1])
    def attachTo(self, coor: Coordinate) -> (Coordinate, float) :
        dis = getDistanceToCoor(self.coor, coor)
        log(f"计算点 id={self.getId()}, coor={self.coor} 到鼠标位置 {coor} 的距离为 {dis}", 1)
        return self.coor, dis
    def dependencyObject(self) -> DependencySet:
        return self.dependency
@getDistanceToCoor.register
def getDistanceToCoor(first: Point, other: Coordinate) -> float:
    return getDistanceToCoor(first.coor, other)
class LineType(Enum):
    # 无限长直线
    Infinite = 0
    # 射线
    Ray = 1
    # 线段
    Segment = 2
# 注意三种类型的直线中, direction 分别由不同含义：
# 无限长直线中只表示方向向量
# 射线中同时表示射向的方向
# 线段中表示起点与终点之间的向量
class Line(BaseGraph):
    def __init__(self, *, startId: Id, direction: DirectionVector, line_type: LineType, dependency: DependencySet = set() ,name: Optional[str] = None, id: Id = None):
        # 请保证 startId 对应对象为 Point 类型，且不会在构造函数期间丢失引用而被析构。
        # dependency 中是否包含 start 均可
        # 注意为了安全性起见所有构造函数的参数都应该是关键字参数
        super().__init__(name, id=id)
        # 这里存储一份引用，保证起点对象不在之前被析构
        self.start: Optional[Point] = BaseGraph.__idToObject.get(startId, None)
        dependency.add(self.start)
        self.dependency: DependencySet = dependency
        self.line_type: LineType = line_type
        if self.start is None:
            raise Exception(f"起点 id={startId} 对象已被析构不存在")
        if not isinstance(self.start, Point):
            raise Exception(f"起点 id={startId} 对象类型错误")
        self.direction: DirectionVector = direction
    # 将点 coor 投影到直线上
    def __projectionToLine(self, coor: Coordinate) -> Coordinate:
        directionLen: float = (self.direction[0]**2 + self.direction[1]**2)**0.5
        # 获得单位向量
        unitDirection: tuple[float, float] = (self.direction[0] / directionLen, self.direction[1] / directionLen)
        # 注意这里的点积是向量点积
        projection: float = sum(mul(unitDirection, sub(coor, self.start.coor)))
        return add(self.start, (projection * i for i in unitDirection))
    def __projectionDistance(self, coor: Coordinate) -> float:
        projection_point = self.__projectionToLine(coor)
        return getDistanceToCoor(coor, projection_point)
    def getTypeName(self):
        return "Line"
    @lru_cache
    def objectToCommand(self) -> str:
        name: str | None = self.getName()
        name_str = f"name={name}" if name is not None else "name=None"
        dependency_str = dependencySetToStr(self.dependency)
        res = f"Line (start={self.start}, direction={self.direction}, line_type={self.line_type}, name={name_str}, id={self.getId()}, dependency={dependency_str})"
        log(f"生成 {self.getTypeName()} 对象 id={self.getId()} 的命令字符串为 {res}", 4)

    def attachTo(self, coor: Coordinate) -> (Coordinate, float):
        projection_point = self.__projectionToLine(coor)
        log(f"计算鼠标位置: {coor} 到 {self.objectToCommand()} 的投影点 {projection_point} ", 1)
        dis = getDistanceToCoor(projection_point, coor)
        log(f"计算鼠标位置: {coor} 到 {self.objectToCommand()} 的距离为 {dis} ", 1)
        dis_sign: (int, int) = tuple([1 if i >= 0 else -1 for i in self.direction])
        acceptedDisFromStart: (float, float) = tuple([- i * MinDis for i in dis_sign])
        acceptedDisFromEnd: (float, float) = tuple([i * MinDis for i in dis_sign])
        match self.line_type:
            case LineType.Infinite:
                return projection_point, dis
            case LineType.Ray:
                if  all([i >= j + delta for i, j, delta in zip(projection_point, self.start.coor, acceptedDisFromStart)]):
                    return projection_point, dis
                else:
                    return self.start.coor, getDistanceToCoor(self.start.coor, coor)
            case LineType.Segment:
                # 这里的两个 bool 分别表示是否在起点之后，是否在终点之前
                loc: (bool, bool) = \
                        (all([i >= j + delta for i, j, delta in zip(projection_point, self.start.coor, acceptedDisFromStart)]) \
                        ,all([i <= j + delta for i, j, delta in zip(projection_point, add(self.start.coor, self.direction), acceptedDisFromEnd)]))
                match loc:
                    case (True, True):
                        return projection_point, dis
                    case (False, True):
                        return self.start.coor, getDistanceToCoor(self.start.coor, coor)
                    case (True, False):
                        return add(self.start.coor, self.direction), getDistanceToCoor(add(self.start.coor, self.direction), coor)
                    case (False, False):
                        raise Exception(f"投影点点 {projection_point} 不在以起点为开始和与终点为开始的两条重合射线上，这是荒谬的")
    def draw(self, painter: Qt.QtGui.QPainter):
        #TODO
        pass
    def cross(self, other: "Line") -> Coordinate | None:
        # 计算两直线交点
        # 注意这里的 direction 是向量
        direction1 = self.direction
        direction2 = other.direction
        # 两直线平行
        if abs (direction1[0] * direction2[1] - direction1[1] * direction2[0]) < MinDis:
            return None
        # 否则，求解方程组
        # x1 + t1 * direction1[0] = x2 + t2 * direction2[0]
        # y1 + t1 * direction1[1] = y2 + t2 * direction2[1]
        # 注意这里的 t1, t2 是标量
        det: float = direction1[0] * direction2[1] - direction1[1] * direction2[0]
        t1: float = (other.start.coor[0] - self.start.coor[0]) * direction2[1] - (other.start.coor[1] - self.start.coor[1]) * direction2[0]
        t2: float = (other.start.coor[0] - self.start.coor[0]) * direction1[1] - (other.start.coor[1] - self.start.coor[1]) * direction1[0]
        t1 /= det
        t2 /= det
        x: float = self.start.coor[0] + t1 * direction1[0]
        y: float = self.start.coor[1] + t1 * direction1[1]
        if ExtraCheck:
            # 检查交点是否在两条直线上
            if not (self.__projectionDistance((x, y)) < MinDis and other.__projectionDistance((x, y)) < MinDis):
                raise Exception(f"计算交点时出现错误，交点不在两条直线上")
        (onFirst, onSecond) = (self.on((x, y)), other.on((x, y)))
        if onFirst and onSecond:
            return (x, y)
        else:
            return None
    def dependencyObject(self) -> DependencySet:
        return self.dependency
def line_create_decorator[**P](func: Callable[P, tuple[Point, DirectionVector, LineType, DependencySet]]) -> Callable[Concatenate[str, Id, P], Line]:
    # 这里传入 point 作为参数是为了防止函数运行中发生引用丢失
    def wrapper(*, name: str, id: Id, **kwargs) -> Line:
        (start, direction, line_type, dependency) = func(**kwargs)
        return Line(startId = start.getId(), direction = direction, line_type = line_type, dependency = dependency, name = name, id = id)
    return wrapper
@line_create_decorator
def lineFromStartCoorAndDirection(startCoor: Coordinate, direction: DirectionVector, line_type: LineType, dependency_set: DependencySet = set()):
    point = Point(startCoor)
    return point, direction, line_type, dependency_set

@line_create_decorator
def lineFromromStartCoorAndEndCoor(startCoor: Coordinate, endCoor: Coordinate, line_type: LineType, dependency_set: DependencySet = set()):
    direction = (endCoor[0] - startCoor[0], endCoor[1] - startCoor[1])
    point = Point(startCoor)
    return point, direction, line_type, dependency_set

@line_create_decorator
def lineFromStartPointAndEndPoint(startPoint: Point, endPoint: Point, line_type: LineType, dependency_set: DependencySet = set()):
    direction = endPoint - startPoint
    dependency_set.add(endPoint)
    return startPoint, direction, line_type, dependency_set


