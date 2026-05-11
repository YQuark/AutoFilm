import abc


class Singleton(abc.ABCMeta, type):
    """
    单例模式
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        key = cls
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]

