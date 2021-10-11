from typing import Union

from xleapp.report._webicons import Icon


class FoundFiles:
    """Descriptor ensuring 'foundfiles' type"""

    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, type=None) -> object:
        return obj.__dict__.get(self.name) or set()

    def __set__(self, obj, value) -> None:
        obj.__dict__[self.name] = value


class WebIcon:
    """Descriptor ensuring 'web_icon' type"""

    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, icon_type=Icon) -> object:
        return obj.__dict__.get(self.name) or Icon.ALERT_TRIANGLE

    def __set__(self, obj, value) -> None:
        if isinstance(value, Icon) or isinstance(value, WebIcon):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                f"Got {type(value)} instead of {type(Icon)}! "
                f"Error setting Web Icon on {str(obj)}!",
            )


class ReportHeaders:
    """Descriptor ensuring 'report_headers' type"""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, report_type=None) -> Union[list, tuple]:
        return obj.__dict__.get(self.name) or ("Key", "Value")

    def __set__(self, obj, value) -> None:
        if ReportHeaders._check_list_of_tuples(value, bool_list=[]):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                "Error setting report headers! Expected list of tuples or tuple!",
            )

    @staticmethod
    def _check_list_of_tuples(values: list, bool_list: list[bool] = None) -> bool:
        """Checks list to see if its a list of tuples of strings

        Examples:

            Set headers for a single table
            self.report_headers = ('Timestamp', 'Account Desc.', 'Username',
                                   'Description', 'Identifier', 'Bundle ID')

            Set headers for more the one table
            self.report_headers = [('Timestamp', 'Account Desc.', 'Username',
                                    'Description', 'Identifier', 'Bundle ID'),
                                   ('Key', 'Value)]

            Anything else should fail to set.

        Args:
            values (list): values to be checked
            bool_list (list, optional): list of booleans of values checked.
                Defaults to [].

        Returns:
            bool: Returns true or false if values match for tuples of strings
        """
        bool_list = bool_list or []
        if values == []:
            return all(bool_list)
        else:
            if isinstance(values, tuple):
                idx = values
                values = []
            elif isinstance(values, list):
                idx = values[:1][0]
                values = values[1:]
            else:
                return False

            if isinstance(idx, list):
                return ReportHeaders._check_list_of_tuples(values, bool_list)
            elif isinstance(idx, tuple):
                bool_list.extend([isinstance(it, str) for it in idx])
            else:
                bool_list.extend([False])
            return ReportHeaders._check_list_of_tuples(values, bool_list)
