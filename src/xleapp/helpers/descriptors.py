import abc
import typing as t


class Validator(abc.ABC):
    """Abstract class for validator descriptors

    Attributes:
        default_value: sets default value for the concrete class
    """

    default_value: t.Any = ...

    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            return getattr(self, "default_value", None)

    def __set__(self, obj, value) -> None:
        if not value:
            setattr(obj, self.private_name, self.default_value)
            value = self.default_value

        # Some validators may return a value
        value_updated = self.validator(value)

        if value_updated:
            if value_updated == "None":
                value_updated = None
            setattr(obj, self.private_name, value_updated)
        else:
            setattr(obj, self.private_name, value)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} ()>"

    @abc.abstractmethod
    def validator(self, value: t.Any) -> t.Any:
        """Function ran to validate a value.

        Validators may return non boolean values.
        """
