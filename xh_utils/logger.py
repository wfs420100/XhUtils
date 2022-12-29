# wfs420100--2022/12/29
import os
import abc
import re
import time
import atexit
import queue
import threading
import logging
from logging import LogRecord
from pathlib import Path

if os.name == "nt":
    # noinspection PyPep8,PyPep8
    import win32con
    import win32file
    import pywintypes

    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # The default value
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    _overlapped = pywintypes.OVERLAPPED()  # noqa
else:
    import fcntl


class _BaseFileLock(metaclass=abc.ABCMeta):
    def __init__(self, lock_file_path: str):
        self.f = open(lock_file_path, 'a')

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplemented

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented


class _WindwosFileLock(_BaseFileLock):
    """
    已近经过测试，即使某个脚本把文件锁获得后，突然把那个脚本关了，另一个脚本也会获得文件锁。不会死锁导致代码无限等待。
    """

    def __enter__(self):
        self.hfile = win32file._get_osfhandle(self.f.fileno())  # noqa
        win32file.LockFileEx(self.hfile, LOCK_EX, 0, 0xffff0000, _overlapped)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # noinspection PyProtectedMember
        # hfile = win32file._get_osfhandle(self.f.fileno())
        win32file.UnlockFileEx(self.hfile, 0, 0xffff0000, _overlapped)


class _LinuxFileLock(_BaseFileLock):

    def __enter__(self):
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.f, fcntl.LOCK_UN)


def _get_filelock():
    return _WindwosFileLock if os.name == 'nt' else _LinuxFileLock


class _ConcurrentTimedRotatingFileHandler(logging.Handler):
    file_handler_list = list()
    has_start_emit_all_file_handler_process_id_set = set()
    __lock_for_rotate = threading.Lock()

    def __init__(self, pathdir: str, filename: str, back_count=10):
        super(_ConcurrentTimedRotatingFileHandler, self).__init__()
        self.pathdir = pathdir
        self.filename = filename
        self.back_count = back_count
        self.ext_match = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)  # 测试观察结果 TODO
        # self.ext_match = re.compile(r"^\d{2}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)  # 测试观察结果 TODO

        self.buffer_msgs_queue = queue.Queue()
        atexit.register(self.write_to_file)  # 如程序启动后立即结束，执行此钩子，防止不到最后一秒的日志没记录到
        self.file_handler_list.append(self)
        if os.getpid() not in self.has_start_emit_all_file_handler_process_id_set:
            self._start_emit_all_file_handler()
            self.__class__.has_start_emit_all_file_handler_process_id_set.add(os.getpid())

    def emit(self, record):
        """
        emti已经在logger.Handler方法中加锁，重置上次写入时间和清除buffer_msgs，不需要加锁
        :param record:
        :return:
        """
        try:
            msg = self.format(record)
            self.buffer_msgs_queue.put(msg)
        except ValueError:
            self.handleError(record)

    @classmethod
    def _start_emit_all_file_handler(cls):
        threading.Thread(target=cls._emit_all_file_handler, daemon=True).start()

    @classmethod
    def _emit_all_file_handler(cls):
        while True:
            for file_handler in cls.file_handler_list:
                file_handler.write_to_file()
            time.sleep(1)  # trick, 提升性能

    def write_to_file(self):
        buffer_msgs = ""
        while True:
            try:
                buffer_msgs += f"{self.buffer_msgs_queue.get(block=False)}\n"
            except queue.Empty:
                break
        if buffer_msgs:
            time_str = time.strftime("%Y-%m-%d")  # 测试观察结果 TODO
            # time_str = time.strftime('%H-%M-%S')  # 测试观察结果 TODO
            new_filename = f"{self.filename}.{time_str}"
            path_obj = Path(self.pathdir) / Path(new_filename)
            path_obj.touch(exist_ok=True)
            with path_obj.open(mode='a', encoding="utf8") as fa:
                fa.write(buffer_msgs)
            with _get_filelock()(self.pathdir / Path(f'_delete_{self.filename}.lock')):
                self._find_and_delete_files()

    def _find_and_delete_files(self):
        filename_list = os.listdir(self.pathdir)
        result = list()
        prefix = self.filename + "."
        plen = len(prefix)
        for _filename in filename_list:
            if _filename[:plen] == prefix:
                suffix = _filename[plen:]
                if self.ext_match.match(suffix): result.append(os.path.join(self.pathdir, _filename))
        if len(result) < self.back_count:
            result.clear()
        else:
            result.sort()
            result = result[:len(result) - self.back_count]

        for r in result: Path(r).unlink()


class _ColorFormatter(logging.Formatter):
    COLOR_CODE_MAP = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "bg_black": "40",
        "bg_red": "41",
        "bg_green": "42",
        "bg_yellow": "43",
        "bg_blue": "44",
        "bg_magenta": "45",
        "bg_cyan": "46",
        "bg_white": "47",
        "light_black": "1;30",
        "light_red": "1;31",
        "light_green": "1;32",
        "light_yellow": "1;33",
        "light_blue": "1;34",
        "light_magenta": "1;35",
        "light_cyan": "1;36",
        "light_white": "1;37",
        "light_bg_black": "100",
        "light_bg_red": "101",
        "light_bg_green": "102",
        "light_bg_yellow": "103",
        "light_bg_blue": "104",
        "light_bg_magenta": "105",
        "light_bg_cyan": "106",
        "light_bg_white": "107",
    }

    def __init__(self, fmt, datefmt):
        super(_ColorFormatter, self).__init__(fmt, datefmt)

    def parse_color(self, level_name):
        color_name = _ConfigLogger.LEVEL_COLOR_MAP.get(level_name, "")
        if not color_name: return color_name

        color_value = []
        color_name = color_name.split(",")
        for c_n in color_name:
            color_code = _ColorFormatter.COLOR_CODE_MAP.get(c_n, "")
            if color_code: color_value.append(color_code)

        return "\033[" + ";".join(color_value) + "m"

    def format(self, record: LogRecord) -> str:
        record.log_color = self.parse_color(record.levelname)
        message = super(_ColorFormatter, self).format(record) + "\033[0m"

        return message


class _ConfigLogger(object):
    LEVEL_COLOR_MAP = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }

    LEVEL_LOGGING_MAP = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "NOTSET": logging.NOTSET,
    }

    STDOUT_TEXT_FMT = "%(log_color)s[%(asctime)s] [%(name)s] [%(levelname)8s] [%(threadName)s] [%(filename)s:%(lineno)d] %(message)s"
    STDOUT_DATE_FMT = "%m-%d-%Y %H:%M:%S"
    FILE_TEXT_FMT = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(threadName)8s] [%(filename)s:%(lineno)d] %(message)s"
    FILE_DATE_FMT = "%m-%d-%Y %H:%M:%S"


class Logger(object):
    author_name, level_name = "wfs420100", "DEBUG"
    level = _ConfigLogger.LEVEL_LOGGING_MAP[level_name.upper()]

    logger = logging.getLogger(name=author_name)
    logger.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(_ColorFormatter(fmt=_ConfigLogger.STDOUT_TEXT_FMT, datefmt=_ConfigLogger.STDOUT_DATE_FMT))
    logger.addHandler(console_handler)

    @classmethod
    def init_logger(cls, log_pathdir="", log_filename="", is_split_logfile=False, author_name="wfs420100", level_name="DEBUG"):
        level = _ConfigLogger.LEVEL_LOGGING_MAP[level_name.upper()]

        cls.logger = logging.getLogger(name=author_name)
        cls.logger.setLevel(level)

        if "" != log_pathdir:
            os.makedirs(log_pathdir, exist_ok=True)
            if "" == log_filename: log_filename = f"log_{time.strftime('%Y%m%d_%H', time.localtime())}.log"

            file_handler = _ConcurrentTimedRotatingFileHandler(log_pathdir, log_filename) if is_split_logfile else logging.FileHandler(os.path.join(log_pathdir, log_filename), encoding="utf8")
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(fmt=_ConfigLogger.FILE_TEXT_FMT, datefmt=_ConfigLogger.FILE_DATE_FMT))
            cls.logger.addHandler(file_handler)

    @staticmethod
    def debug(msg):
        Logger.logger.debug(msg)

    @staticmethod
    def info(msg):
        Logger.logger.info(msg)

    @staticmethod
    def warning(msg):
        Logger.logger.warning(msg)

    @staticmethod
    def error(msg):
        Logger.logger.error(msg)

    @staticmethod
    def critical(msg):
        Logger.logger.critical(msg)


def starting():
    Logger.init_logger()
    Logger.debug("debug")
    Logger.info("info")
    Logger.warning("warning")
    Logger.error("error")


if __name__ == '__main__':
    print("wfs420100")
    starting()
