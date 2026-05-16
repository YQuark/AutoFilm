import abc
import threading


class Multiton(abc.ABCMeta, type):
    """
    多例模式
    """

    _instances: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        key = (cls, args, frozenset(kwargs.items()))
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]

