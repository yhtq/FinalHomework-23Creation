from collections.abc import Callable
from io import TextIOWrapper
from typing import Final

type Id = int
MaxId: Final[Id] = 2**32 - 1
# 用于鼠标点击时判断是否选中对象的最小距离
MinDis: Final[float] = 1e-2
Log: Final[bool] = True
ExtraCheck: Final[bool] = True
LogFile: Final[str] = "log.txt"
# LogLevel 越低日志越详细，也就是 level 越高越重要
LogLevel: Final[int] = 1
def logWrapper() -> (Callable[[str, int], None], Callable[[], None]):
    if Log:
        logWrapper: TextIOWrapper = open(LogFile, "a+")
        def log(message: str, level: int = LogLevel) -> None:
            if level < LogLevel:
                return
            logWrapper.write(message + "\n")
            logWrapper.flush()
        def close() -> None:
            logWrapper.close()
        return log, close
    else:
        def log(message: str) -> None:
            pass
        def close() -> None:
            pass
        return log, close
log: Callable[[str, int], None] = logWrapper()[0]
closeLog: Callable[[], None] = logWrapper()[1]
type Coordinate = tuple[float, float]

