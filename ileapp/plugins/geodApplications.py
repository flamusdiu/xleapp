from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class GeodApplication(AbstractArtifact):
    def __post_init__(self):
        self.name = 'GeoD Application'
        self.category = 'Applications'
        self.web_icon = Icon.GRID
        self.report_headers = ("Creation Time", "Count ID", "Application")

    @timed
    @Search('**/com.apple.geod/AP.db')
    def process(self):
        fp = self.found
        cursor = fp.cursor()
        cursor.execute(
            """
            SELECT count_type, app_id, createtime
            FROM mkcount
            """,
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_list = []
            for row in all_rows:
                data_list.append((row[2], row[0], row[1]))
            self.data = data_list
