from typing import Concatenate, TypeVar
from enum import Enum
from defines import *
from graph import *
from functools import partial
import unittest
import sys
from weakref import WeakSet, WeakKeyDictionary
# 要求 python 3.12 及以上
if sys.version_info < (3, 12):
    raise Exception("Please use python 3.12 or above")


# 有限的双端列表，超出时会自动删除最早的元素
type T = TypeVar("T")
class FiniteQueue(list[T]):
    def __init__(self, max_length: int):
        self.max_length = max_length
    # 返回是否溢出
    def append(self, item: T) -> bool:
        res = False
        if len(self) >= self.max_length:
            self.pop(0)
            res = True
        super().append(item)
        return res


# 已经实现的图形对象
type AvailableGraph = Line | Point
# 对图形对象的操作
class OperationType(Enum):
    Create = 1,
    Delete = 2,
type Operation = tuple[OperationType, Id]
# 用于记录操作的历史
operation_list: FiniteQueue[Operation] = FiniteQueue(DeletedListLength)
# 用于记录撤回的操作，请注意 Operation 中存储的是刚刚撤回的操作
undo_list: FiniteQueue[Operation] = FiniteQueue(DeletedListLength)
# 用于记录活跃的对象，也就是要显示的对象
active_set: set[AvailableGraph] = set()
# 用于记录隐藏对象，应当被自然的回收因此使用弱引用
hide_set: WeakSet[AvailableGraph] = WeakSet()
# 用于为被删除后可能被撤回的对象提供暂存
deleted_list: FiniteQueue[AvailableGraph] = FiniteQueue(DeletedListLength)
# 用于记录所有对象的依赖信息，方向是向下的，也即 dict[A] 中的元素是所有依赖于 A 的元素。请保证不出现循环引用
dependency_tree: WeakKeyDictionary[BaseGraph, WeakSet[BaseGraph]] = WeakKeyDictionary()

def runtime_reset():
    operation_list.clear()
    undo_list.clear()
    active_set.clear()
    deleted_list.clear()
    BaseGraph.reset()
    closeLog()
    reopenLog()

# 为所有创建函数顺路记录进活跃对象，同时提供 name, id 参数。hide 参数表示是否是显式操作（从而对象将被画出并可以被撤回）。请保证构造函数仅有仅限关键字函数
# 请不要使用裸的构造函数而是使用下面的包装后的构造函数
def create_decorator[BaseGraph, **P](func: Callable[P, Callable[[str, DependencySet, Id], BaseGraph]]) -> Callable[Concatenate[bool, str, DependencySet, Id, P], BaseGraph]:
    def wrapper(*,hide: bool = False, name: Optional[str] = None, id: Optional[Id] = None, dependency: DependencySet = set(), **kwargs) -> BaseGraph:
        resFunc: Callable[[str, DependencySet, Id], BaseGraph] = func(**kwargs)
        res: BaseGraph = resFunc(name=name, dependency=dependency, id=id)
        if not hide:
            active_set.add(res)
            operation_list.append((OperationType.Create, id))
        else:
            hide_set.add(res)
        for i in res.dependencyObject():
            dependency_tree.setdefault(i, set()).add(res)
        return res
    return wrapper

def create_from_command(command: str) -> AvailableGraph:
    obj = BaseGraph.commandToObject(command)
    assert isinstance(obj, Line | Point)
    active_set.add(obj)
    return obj

@create_decorator
def create_point(*, coor: Coordinate):
    return partial(Point, coor=coor)

# 注意 LineType 包括 Segment, Segment, Ray，它们的 direction 分别是两个端点的差，射线方向，直线方向。
# 也就是说线段的方向向量需要指定方向和大小，射线只需要保证方向，直线则方向和大小都无关紧要
@create_decorator
def create_line_from_start_and_direction(*, start: Point, direction: DirectionVector, line_type: LineType):
    return partial(lineFromStartAndDirection, start=start, direction=direction, line_type=line_type)

@create_decorator
def create_line_from_start_coor_and_direction(*, start: Coordinate, direction: DirectionVector, line_type: LineType):
    start: Point = create_point(coor=start, hide=True)
    return partial(lineFromStartAndDirection, start=start, direction=direction, line_type=line_type)

@create_decorator
def create_line_from_start_coordinate_and_end_coordinate(*, start: Coordinate, end: Coordinate, line_type: LineType):
    start = create_point(coor=start, hide=True)
    end = create_point(coor=end, hide=True)
    return partial(lineFromStartPointAndEndPoint, startPoint=start, endPoint=end, line_type=line_type)

@create_decorator
def create_line_from_start_point_and_end_point(*, start: Point, end: Point, line_type: LineType):
    return partial(lineFromStartPointAndEndPoint, startPoint=start, endPoint=end, line_type=line_type)

def get_cross(line1: Line, line2: Line, hide: bool = False, name: Optional[str] = None, id : Optional[Id] = None, dependency: DependencySet = set()) -> Point | None:
    cross_coor: Coordinate | None = line1.cross(line2)
    if cross_coor is None:
        return None
    else:
        return create_point(coor=cross_coor, dependency=set([line1, line2]) | dependency, name=name, id=id, hide=hide)
    
def get_point_on_line(line: Line, coor: Coordinate, hide: bool = False, name: Optional[str] = None, id : Optional[Id] = None, dependency: DependencySet = set()) -> Point:
    if not line.on(coor):
        raise Exception(f"点 {coor} 不在直线 {line.objectToCommand()} 上")
    return create_point(coor=coor, dependency=set([line]) | dependency, name=name, id=id, hide=hide)

def delete(objectId: Id, add_to_operation: bool = True):
    obj = BaseGraph.findObjectById(objectId)
    if obj is None:
        raise Exception("Object 不存在")
    if obj not in active_set:
        raise Exception("Object 不在活跃对象中")
    active_set.remove(obj)
    # 请注意这里对象其实未必析构，因为可能被其他的活跃对象所依赖
    if add_to_operation:
        operation_list.append((OperationType.Delete, objectId))
    deleted_list.append(obj)

class UndoStatus(Enum):
    NoOperation = 1,
    UndoCreate = 2,
    UndoDelete = 3,
    UndoDeleteButObjectNotExist = 4,

class RedoStatus(Enum):
    NoOperation = 1,
    RedoCreate = 2,
    RedoDelete = 3,
    RedoDeleteButObjectNotExist = 4,

def undo() -> UndoStatus:
    if len(operation_list) == 0:
        return UndoStatus.NoOperation
    operation = operation_list.pop()
    match operation:
        case (OperationType.Create, id):
            delete(id, False)
            undo_list.append(operation)
            return UndoStatus.UndoCreate
        case (OperationType.Delete, id):
            obj = BaseGraph.findObjectById(id)
            if obj is None:
                return UndoStatus.UndoDeleteButObjectNotExist
            undo_list.append(operation)
            active_set.add(obj)
            return UndoStatus.UndoDelete

def redo() -> RedoStatus:
    if len(undo_list) == 0:
        return RedoStatus.NoOperation
    operation = undo_list.pop()
    match operation:
        case (OperationType.Create, id):
            obj = BaseGraph.findObjectById(id)
            if obj is None:
                return RedoStatus.RedoCreateButObjectNotExist
            active_set.add(obj)
            operation_list.append(operation)
            return RedoStatus.RedoCreate
        case (OperationType.Delete, id):
            delete(id, False)
            operation_list.append(operation)
            return RedoStatus.RedoDelete

class tests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.addCleanup(runtime_reset)
    def assertCoorEqual(self, coor1: Coordinate, coor2: Coordinate) -> None:
        dis = getDistanceToCoor(coor1, coor2)
        self.assertLessEqual(dis, MinDis)
    def test_point(self):
        p1 = create_point(name="A", id=1, dependency=set(), coor=(0.0, 0.0))
        self.assertEqual(p1.attachTo((0, 0.001)), ((0.0, 0.0), 0.001))
        p2 = create_point(name="B", id=2, dependency=set(), coor=(1.0, 0.0))
        create_point(name="C", id=3, dependency=set(), coor=(0.0, 1.0))
        delete(3)
        delete(p2.getId())
        self.assertEqual(len(active_set), 1)
        self.assertEqual(UndoStatus.UndoDelete, undo())
        self.assertEqual(len(active_set), 2)
        self.assertEqual(UndoStatus.UndoDelete, undo())
        self.assertEqual(len(active_set), 3)
        self.assertEqual(UndoStatus.UndoCreate, undo())
        delete(2)
        self.assertEqual(UndoStatus.UndoDelete, undo())
        self.assertEqual(RedoStatus.RedoDelete, redo())
        self.assertEqual(active_set, set([p1]))
        p1_command: str = p1.objectToCommand()
        p2_command: str = p2.objectToCommand()
        p3_command: str = BaseGraph.findObjectById(3).objectToCommand()
        runtime_reset()
        _p1 = create_from_command(p1_command)
        _p2 = create_from_command(p2_command)
        _p3 = create_from_command(p3_command)
        self.assertEqual(len(active_set), 3)
        self.assertEqual(0, len(_p3.dependency))
    def __test_line(self, line_type: LineType):
        p1 = create_point(name="A", coor=(0.0, 0.0), dependency=set(), hide=True)
        l1: Line = create_line_from_start_and_direction(name="l", id=1, dependency=set([p1]), start=p1, direction=(1.0, 0.0), line_type=line_type)
        self.assertEqual(UndoStatus.UndoCreate, undo())
        self.assertEqual(UndoStatus.NoOperation, undo())
        self.assertEqual(RedoStatus.RedoCreate, redo())
        self.assertEqual(len(l1.dependencyObject()), 1)
        self.assertEqual(l1.on((0.5, 0.0)), True)
        self.assertEqual(l1.on((1.5, 0.0)), True if line_type != LineType.Segment else False)
        self.assertEqual(l1.on((-1.5, 0.0)), False if line_type != LineType.Infinite else True)
        l2 = create_line_from_start_coordinate_and_end_coordinate(name="l", dependency=set(), start=(3.0, 0.0), end=(3.0, 1.0), line_type=line_type)
        cross_point: Coordinate | None = l1.cross(l2)
        expected_cross_point: Coordinate | None 
        match_expected: bool = False
        self.assertEqual(cross_point, l2.cross(l1))
        match line_type:
            case LineType.Segment:
                match_expected = True if cross_point is None else False
            case LineType.Ray | LineType.Infinite:
                expected_cross_point = (3.0, 0.0) 
                self.assertCoorEqual(cross_point, expected_cross_point)
                match_expected = True 
        self.assertEqual(match_expected, True)
        l2.start.move((0.0, -2.0))
        renew_obj(l2)
        cross_point = l1.cross(l2)
        self.assertEqual(cross_point, l2.cross(l1))
        # 交点应为 (2.0, 0.0)
        match line_type:
            case LineType.Segment:
                match_expected = True if cross_point is None else False
            case LineType.Ray | LineType.Infinite:
                expected_cross_point = (2.0, 0.0) 
                match_expected = True if getDistanceToCoor(cross_point, expected_cross_point) < 0.01 else False
        self.assertEqual(match_expected, True)
    def __test_cross(self, line_type: LineType):
        p1 = create_point(coor=(0.0, 0.0))
        p2 = create_point(coor=(2.0, 0.0))
        p3 = create_point(coor=(1.0, -1.0))
        p4 = create_point(coor=(1.0, 1.0))
        l1 = create_line_from_start_point_and_end_point(start=p1, end=p2, line_type=line_type)
        l2 = create_line_from_start_point_and_end_point(start=p3, end=p4, line_type=LineType.Segment)
        cross_point = get_cross(l1, l2)
        self.assertIn(cross_point, dependency_tree[l1])
        self.assertIn(cross_point, dependency_tree[l2])
        self.assertEqual(cross_point.coor, (1.0, 0.0))
        p1.move((1.1, 0.9))
        renew_obj(l1)
        renew_obj(cross_point)
        # 移动端点后，新的交点应为 (1.0, 1.0)
        expected_cross_point = (1.0, 1.0) if line_type == LineType.Infinite else None
        self.assertCoorEqual(cross_point.coor, expected_cross_point)
    def test_segment(self):
        self.__test_line(LineType.Segment)
        #self.__test_cross(LineType.Segment)
    def test_ray(self):
        self.__test_line(LineType.Ray)
        #self.__test_cross(LineType.Ray)
    def test_line(self):
        self.__test_line(LineType.Infinite)
        self.__test_cross(LineType.Infinite)


if __name__ == "__main__":
    unittest.main()
        






    







