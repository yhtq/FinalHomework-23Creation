from collections.abc import Callable
from io import TextIOWrapper
from math import sqrt
from typing import Final

type Id = int
MaxId: Final[Id] = 2**32 - 1
class Settings:
    # 分别表示每个格子的长宽，以及格子的数量
    WIDTH = 40
    HEIGHT = 40
    NUM_BLOCKS_X = 20
    NUM_BLOCKS_Y = 20

XSize: Final[int] = Settings.WIDTH * Settings.NUM_BLOCKS_X
YSize: Final[int] = Settings.HEIGHT * Settings.NUM_BLOCKS_Y
RefSize: Final[int] = sqrt(XSize**2 + YSize**2)
# 用于浮点数的比较
MinDis: Final[float] = 1e-5 * float(RefSize)
# 用于鼠标吸附
MinAttachDis: Final[float] = 1e-2 * float(RefSize)
DeletedListLength: Final[int] = 50
Log: Final[bool] = True
ExtraCheck: Final[bool] = True
LogFile: Final[str] = "log.txt"
# LogLevel 越低日志越详细，也就是 level 越高越重要
LogLevel: Final[int] = 1
# 检查是否有循环依赖
CircleDetection: Final[bool] = True


def logWrapper() -> (Callable[[str, int], None], Callable[[], None], Callable[[], None]):
    if Log:
        logHandler: TextIOWrapper = open(LogFile, "a+")
        def log(message: str, level: int = LogLevel) -> None:
            nonlocal logHandler
            if level < LogLevel:
                return
            logHandler.write(message + "\n")
            logHandler.flush()
        def close() -> None:
            nonlocal logHandler
            logHandler.close()
        def reopen() -> None:
            nonlocal logHandler
            logHandler = open(LogFile, "a+")
        return log, close, reopen
    else:
        def log(message: str) -> None:
            pass
        def close() -> None:
            pass
        return log, close, close
temp = logWrapper()
log: Callable[[str, int], None] = temp[0]
closeLog: Callable[[], None] = temp[1]
reopenLog: Callable[[], None] = temp[2]
type Coordinate = tuple[float, float]
type DirectionVector = Coordinate

