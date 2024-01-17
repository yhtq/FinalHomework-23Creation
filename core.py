from typing import Concatenate, TypeVar
from enum import Enum
from defines import *
from graph import Line, Point, BaseGraph

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
# 用于记录撤回的操作
revocation_list: FiniteQueue[Operation] = FiniteQueue(DeletedListLength)
# 用于记录活跃的对象，也就是要显示的对象
active_set: set[AvailableGraph] = set()
# 用于为被删除后可能被撤回的对象提供暂存
deleted_list: FiniteQueue[AvailableGraph] = FiniteQueue(DeletedListLength)
# 用于记录所有对象的依赖信息，方向是向下的，也即 dict[A] 中的元素是所有依赖于 A 的元素。请保证不出现循环引用
# 好像没有意义，本身对象中已经存了一份依赖信息了
# dependency_tree: dict[Id, set[Id]] = {}

# 为所有创建函数顺路记录进活跃对象，同时提供 name, id 参数。请保证构造函数仅有仅限关键字函数
def create_decorator[BaseGraph, **P](func: Callable[P, BaseGraph]) -> Callable[Concatenate[str, Id, P], BaseGraph]:
    def wrapper(*, name: str, id: Id, **kwargs) -> BaseGraph:
        res: BaseGraph = func(name = name, id = id, **kwargs)
        active_set.add(res)
        # for i in res.dependencyObject():
        #     if ExtraCheck:
        #         if i not in dependency_tree:
        #             raise Exception("Dependency 未被创建")
        #     dependency_tree[i.getId()].add(res.getId())
        # dependency_tree[res.getId()] = set()
        operation_list.append((OperationType.Create, id))
        return res
    return wrapper

def delete(objectId: Id):
    obj = BaseGraph.findObjectById(objectId)
    if obj is None:
        raise Exception("Object 不存在")
    active_set.remove(obj)
    # 请注意这里对象其实未必析构，因为可能被其他的活跃对象所依赖
    operation_list.append((OperationType.Delete, objectId))
    deleted_list.append(objectId)




