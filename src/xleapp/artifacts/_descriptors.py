import xleapp.report._webicons as web
from xleapp.helpers.descriptors import Validator


class FoundFiles(Validator):
    """Descriptor ensuring 'foundfiles' type"""

    default_value = set()

    def validator(self, value):
        if not isinstance(value, set):
            raise TypeError(f"Expected {value!r} to be a set!")


class WebIcon(Validator):
    """Descriptor ensuring 'web_icon' type"""

    default_value = web.WebIcon.ALERT_TRIANGLE

    def validator(self, value):
        if not isinstance(value, (web.WebIcon, WebIcon)):
            raise TypeError(f"Expected {value!r} to be {web.WebIcon!r}! ")


class ReportHeaders(Validator):
    """Descriptor ensuring 'report_headers' type"""

    default_value = ("Key", "Value")

    def validator(self, value) -> None:
        if not ReportHeaders._check_list_of_tuples(value, bool_list=[]):
            raise TypeError(
                f"Expected {value!r} to be a list of tuples or tuple!",
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
