import datetime
import re
from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon


@dataclass
class AppConduit(AbstractArtifact):
    def __post_init__(self):

        self.name = 'App Conduit'
        self.category = 'App Conduit'
        self.web_icon = Icon.ACTIVITY
        self.report_headers = [
            ('Device ID', 'Device type and version', 'Device extra information'),
            ('Time', 'Device interaction', 'Device ID', 'Log File Name'),
        ]

    @timed
    @Search('**/AppConduit.log.*', file_names_only=True)
    def process(self):
        data_list = []
        device_type_and_info = []

        info = ''
        reg_filter = (
            r'(([A-Za-z]+[\s]+([a-zA-Z]+[\s]+[0-9]+)[\s]+'
            r'([0-9]+\:[0-9]+\:[0-9]+)[\s]+([0-9]{4}))([\s]+'
            r'[\[\d\]]+[\s]+[\<a-z\>]+[\s]+[\(\w\)]+)[\s\-]+'
            r'(((.*)(device+\:([\w]+\-[\w]+\-[\w]+\-[\w]+'
            r'\-[\w]+))(.*)$)))'
        )

        date_filter = re.compile(reg_filter)

        for fp in self.found:
            fp_found = open(fp, 'r', encoding='utf8')
            linecount = 0

            for line in fp_found:
                linecount = linecount + 1
                line_match = re.match(date_filter, line)

                if line_match:
                    date_time = line_match.group(3, 5, 4)
                    conv_time = ' '.join(date_time)
                    dtime_obj = datetime.datetime.strptime(
                        conv_time,
                        '%b %d %Y %H:%M:%S',
                    )
                    values = line_match.group(9)
                    device_id = line_match.group(11)

                    if 'devicesAreNowConnected' in values:
                        device = (
                            device_id,
                            line_match.group(12).split(" ")[4],
                            line_match.group(12).split(" ")[5],
                        )
                        device_type_and_info.append(device)

                        info = 'Connected'
                        data = (dtime_obj, info, device_id, fp.name)
                        data_list.append(data)

                    if 'devicesAreNoLongerConnected' in values:
                        info = 'Disconnected'
                        data = (dtime_obj, info, device_id, fp.name)
                        data_list.append(data)
                    # if 'Resuming because' in values:
                    #     info = 'Resumed'
                    #     data_list.append((dtime_obj,info,device_id,device_type_tmp,file_name))
                    # if 'Suspending because' in values:
                    #     info = 'Suspended'
                    #     data_list.append((dtime_obj,info,device_id,device_type_tmp,file_name))
                    # if 'Starting reunion sync because device ' in values:
                    #     info = 'Reachable again after reunion sync'
                    #     data_list.append((dtime_obj,info,device_id,device_type_tmp,file_name))

        device_type_and_info = list(set(device_type_and_info))

        self.data = {
            'device_type_and_info': device_type_and_info,
            'device_connection_info': data_list,
        }
