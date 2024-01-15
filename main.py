import sys
import PyQt6 as Qt
if __name__ == "__main__":
    cur_py_version: tuple[int, int] = sys.version_info[0:2]
    if cur_py_version < (3, 12):
        print("请使用 Python 3.12 以上")
        sys.exit(1)
    print("Hello world")