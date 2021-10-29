from abc import ABC, abstractmethod


class Validator(ABC):
    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            return getattr(self, "default_value", None)

    def __set__(self, obj, value) -> None:
        # Some validators may return a value
        value_updated = self.validator(value)
        if value_updated:
            setattr(obj, self.private_name, value_updated)
        else:
            setattr(obj, self.private_name, value)

    @abstractmethod
    def validator(self, value):
        raise NotImplementedError(
            "Descriptors must create a `validator()` class that returns a boolean!",
        )
