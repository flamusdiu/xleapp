from tabnanny import filename_only
from xleapp.helpers.descriptors import Validator
from xleapp.artifacts.regex import Regex
from xleapp.report import WebIcon


class FoundFiles(Validator):
    """Descriptor ensuring 'foundfiles' type"""

    default_value: set = set()

    def validator(self, value):
        if not isinstance(value, set):
            raise TypeError(f"Expected {value!r} to be a set!")


class Icon(Validator):
    """Descriptor ensuring 'web_icon' type"""

    default_value: WebIcon = WebIcon["ALERT_TRIANGLE"]

    def validator(self, value):
        if value not in WebIcon:
            raise TypeError(f"Expected {str(value)} to be {repr(WebIcon)}! ")


class ReportHeaders(Validator):
    """Descriptor ensuring 'report_headers' type"""

    default_value: tuple = ()

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
            else:
                return False

            if isinstance(idx, list):
                return ReportHeaders._check_list_of_tuples(values, bool_list)
            elif isinstance(idx, tuple):
                bool_list.extend([isinstance(it, str) for it in idx])
            else:
                bool_list.extend([False])
            return ReportHeaders._check_list_of_tuples(values, bool_list)


class SearchRegex(Validator):
    """Descriptor ensuring 'regex' type"""

    default_value: set = set()

    def validator(self, *value) -> None:
        if not SearchRegex._check_list_of_tuples(value, bool_list=[]):
            raise TypeError(
                f"Expected {value!r} to be a list of list or tuple!",
            )

    @staticmethod
    def _check_list_of_tuples(*args: tuple[str], bool_list: list[bool] = None) -> bool:
        """Checks list to see if its a list of tuples of strings

        Examples:

            Set single search
            @Search("**/myregex")
            process(self) -> None:
                pass

            Set single search with options
            @Search("**/myregex", "return_on_first_hit")
            process(self) -> None:
                pass

            Set multiple searches
            @Search(("**/myregex"), ("**/my_other_regex"), ("**/my_next_regex"))
            process(self) -> None:
                pass

            Set multiple searches with options
            @Search(
                ("**/myregex", "return_on_first_hit"),
                ("**/my_other_regex", "return_on_first_hit", "file_names_only"),
                ("**/my_next_regex")
            )

            process(self) -> None:
                pass
            Anything else should fail to set.

        Args:
            values: values to be checked
            bool_list: list of booleans of values checked.
                Defaults to [].

        Returns:
            bool: Returns true or false if values match for tuples of strings
        """
        bool_list = bool_list or []

        args = args[0]

        if args == ():
            return all(bool_list)
        else:
            if isinstance(args, tuple):
                idx = args[:1][0]
                args = args[1:]
            else:
                return False

            if isinstance(idx, str):
                bool_list.extend([True])

            return SearchRegex._check_list_of_tuples(args, bool_list=bool_list)

    def __set__(self, obj, value) -> None:
        # Some validators may return a value
        self.validator(value)
        searches = []

        if isinstance(value, str):
            searches.extend([Regex(value)])
        else:
            for regex in value:
                if isinstance(regex, str):
                    regex_obj = Regex(
                        regex,
                        file_names_only="file_names_only" in regex,
                        return_on_first_hit="return_on_first_hit" in regex,
                    )
                else:
                    regex_obj = Regex(
                        regex[0],
                        file_names_only="file_names_only" in regex,
                        return_on_first_hit="return_on_first_hit" in regex,
                    )
                searches.extend([regex_obj])

        setattr(obj, self.private_name, tuple(searches))
