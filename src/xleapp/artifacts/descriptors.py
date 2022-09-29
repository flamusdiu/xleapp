import xleapp.artifacts.regex as regex
import xleapp.helpers.descriptors as descriptors
import xleapp.report as report


class FoundFiles(descriptors.Validator):
    """Descriptor ensuring 'foundfiles' type"""

    default_value: set = set()

    def validator(self, value):
        if not isinstance(value, set):
            raise TypeError(f"Expected {value!r} to be a set!")


class Icon(descriptors.Validator):
    """Descriptor ensuring 'web_icon' type"""

    default_value: report.WebIcon = report.WebIcon["ALERT_TRIANGLE"]

    def validator(self, value):
        try:
            report.WebIcon(value)
        except ValueError:
            raise TypeError(f"Expected {str(value)} to be {repr(report.WebIcon)}!")


class ReportHeaders(descriptors.Validator):
    """Descriptor ensuring 'report_headers' type"""

    default_value: tuple = ()

    def validator(self, value) -> None:
        if not ReportHeaders._check_list_of_tuples(value, bool_list=[]):
            raise TypeError(
                f"Expected {value!r} to be a list of tuples or tuple!",
            )

    @staticmethod
    def _check_list_of_tuples(values: list, *, bool_list: list[bool] = None) -> bool:
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
            values: values to be checked
            bool_list: list of booleans of values checked.
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

            if isinstance(idx, tuple):
                for it in idx:
                    if isinstance(it, str):
                        bool_list.extend([True])
                    else:
                        return False

            return ReportHeaders._check_list_of_tuples(values, bool_list=bool_list)


class SearchRegex(descriptors.Validator):
    """Descriptor ensuring 'regex' type"""

    default_value: set = set()

    def validator(self, value) -> None:
        if not (isinstance(value, str) or (isinstance(value, tuple) and len(value) < 4)):
            raise TypeError(
                f"Expected {value!r} to be a str or tuple!",
            )

    def __set__(self, obj, value) -> None:
        # Some validators may return a value
        self.validator(value)
        searches = []

        if isinstance(value, str):
            searches.extend([regex.Regex(value)])
        else:
            searches.extend([regex.Regex(*value)])

        setattr(obj, self.private_name, tuple(searches))
