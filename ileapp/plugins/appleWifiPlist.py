import logging
import plistlib
from dataclasses import dataclass

from ileapp.abstract import AbstractArtifact
from ileapp.helpers.decorators import Search, timed
from ileapp.report.webicons import Icon

logger = logging.getLogger(__name__)


@dataclass
class KnownNetwork:
    ssid: str = ''
    bssid: str = ''
    net_usage: str = ''
    country_code: str = ''
    device_name: str = ''
    manufacturer: str = ''
    serial_number: str = ''
    model_name: str = ''
    last_joined: str = ''
    last_updated: str = ''
    last_auto_joined: str = ''
    enabled: str = ''
    wnpmd: str = ''
    file: str = ''


@dataclass
class ScannedNetwork:
    ssid: str = ''
    bssid: str = ''
    added_at = ''
    last_joined: str = ''
    last_updated: str = ''
    private_mac_in_use = ''
    private_mac_value = ''
    private_mac_valid = ''
    in_known_networks = ''
    last_auto_joined: str = ''
    file: str = ''


def hexify_byte(byte_to_convert):
    to_return = hex(byte_to_convert).replace('0x', '')
    if len(to_return) < 2:
        to_return = "0" + to_return

    return to_return


def _bytes_to_mac_address(encoded_bytes):
    to_return = ''
    to_return = (
        hexify_byte(encoded_bytes[0]) + ":" + hexify_byte(encoded_bytes[1]) + ":"
    )
    to_return = (
        to_return
        + hexify_byte(encoded_bytes[2])
        + ":"
        + hexify_byte(encoded_bytes[3])
        + ":"
    )
    to_return = (
        to_return + hexify_byte(encoded_bytes[4]) + ":" + hexify_byte(encoded_bytes[5])
    )
    return to_return


@dataclass
class AppleWifiKnownNetworks(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Wifi Known Networks'
        self.description = (
            'WiFi known networks data. Dates are taken straight from the source plist.'
        )
        self.category = 'Locations'
        self.report_headers = (
            'SSID',
            'BSSID',
            'Network Usage',
            'Country Code',
            'Device Name',
            'Manufacturer',
            'Serial Number',
            'Model Name',
            'Last Joined',
            'Last Auto Joined',
            'Last Updated',
            'Enabled',
            'WiFi Network Password Modification Date',
            'File',
        )
        self.report_title = 'WiFi Known Networks'
        self.web_icon = Icon.WIFI

    @timed
    @Search(
        '**/com.apple.wifi.plist',
        '**/com.apple.wifi-networks.plist.backup',
        '**/com.apple.wifi.known-networks.plist',
        '**/com.apple.wifi-private-mac-networks.plist',
    )
    def process(self):
        if not isinstance(self.found, list):
            self.found = [self.found]

        for fp in self.found:
            deserialized = plistlib.load(fp)

            known_networks = []
            try:
                for known_network in deserialized['List of known networks']:
                    network = KnownNetwork()

                    if 'SSID_STR' in known_network:
                        network.ssid = str(known_network['SSID_STR'])

                    if 'BSSID' in known_network:
                        network.bssid = str(known_network['BSSID'])

                    if 'networkUsage' in known_network:
                        network.net_usage = str(known_network['networkUsage'])

                    if '80211D_IE' in known_network:
                        if 'IE_KEY_80211D_COUNTRY_CODE' in known_network['80211D_IE']:
                            network.country_code = str(
                                known_network['80211D_IE']['IE_KEY_80211D_COUNTRY_CODE']
                            )

                    if 'lastUpdated' in known_network:
                        network.last_updated = str(known_network['lastUpdated'])

                    if 'lastAutoJoined' in known_network:
                        network.last_auto_joined = str(known_network['lastAutoJoined'])

                    if 'lastJoined' in known_network:
                        network.last_joined = str(known_network['lastJoined'])

                    if 'WiFiNetworkPasswordModificationDate' in known_network:
                        network.wnpmd = str(
                            known_network['WiFiNetworkPasswordModificationDate']
                        )

                    if 'enabled' in known_network:
                        network.enabled = str(known_network['enabled'])

                    if 'WPS_PROB_RESP_IE' in known_network:

                        if 'IE_KEY_WPS_DEV_NAME' in known_network['WPS_PROB_RESP_IE']:
                            network.device_name = known_network['WPS_PROB_RESP_IE'][
                                'IE_KEY_WPS_DEV_NAME'
                            ]
                        if (
                            'IE_KEY_WPS_MANUFACTURER'
                            in known_network['WPS_PROB_RESP_IE']
                        ):
                            network.manufacturer = known_network['WPS_PROB_RESP_IE'][
                                'IE_KEY_WPS_MANUFACTURER'
                            ]
                        if 'IE_KEY_WPS_SERIAL_NUM' in known_network['WPS_PROB_RESP_IE']:
                            network.serial_number = known_network['WPS_PROB_RESP_IE'][
                                'IE_KEY_WPS_SERIAL_NUM'
                            ]
                        if 'IE_KEY_WPS_MODEL_NAME' in known_network['WPS_PROB_RESP_IE']:
                            network.model_name = known_network['WPS_PROB_RESP_IE'][
                                'IE_KEY_WPS_MODEL_NAME'
                            ]

                    network.file = fp.name
                    network_attributes = [val for attr, val in network.__dict__.items()]
                    known_networks.append(network_attributes)
            except KeyError:
                logger.info('No networks found in plist.', extra={'flow': 'no_filter'})

        self.data = known_networks


@dataclass
class AppleWifiScannedPrivate(AbstractArtifact):
    def __post_init__(self):
        self.name = 'Wifi Networks Scanned (private)'
        self.description = 'WiFi networks scanned while using fake ("private") MAC address. Dates are taken straight from the source plist.'
        self.category = 'Locations'
        self.report_headers = (
            'SSID',
            'BSSID',
            'Added At',
            'Last Joined',
            'Last Updated',
            'MAC Used For Network',
            'Private MAC Computed For Network',
            'MAC Valid',
            'In Known Networks',
            'File',
        )
        self.report_title = 'Wifi Networks Scanned (private)'
        self.web_icon = Icon.WIFI

    @timed
    @Search(
        '**/com.apple.wifi.plist',
        '**/com.apple.wifi-networks.plist.backup',
        '**/com.apple.wifi.known-networks.plist',
        '**/com.apple.wifi-private-mac-networks.plist',
    )
    def process(self):
        if not isinstance(self.found, list):
            self.found = [self.found]

        for fp in self.found:
            deserialzied = plistlib.load(fp)

            scanned_networks = []
            try:
                for scanned_network in deserialzied[
                    'List of scanned networks with private mac'
                ]:
                    network = ScannedNetwork()

                    if 'SSID_STR' in scanned_network:
                        network.ssid = str(scanned_network['SSID_STR'])

                    if 'BSSID' in scanned_network:
                        network.bssid = str(scanned_network['BSSID'])

                    if 'lastUpdated' in scanned_network:
                        network.last_updated = str(scanned_network['lastUpdated'])

                    if 'lastJoined' in scanned_network:
                        network.last_joined = str(scanned_network['lastJoined'])

                    if 'addedAt' in scanned_network:
                        network.added_at = str(scanned_network['addedAt'])

                    if 'PresentInKnownNetworks' in scanned_network:
                        network.in_known_networks = str(
                            scanned_network['PresentInKnownNetworks']
                        )

                    if 'PRIVATE_MAC_ADDRESS' in scanned_network:
                        if (
                            'PRIVATE_MAC_ADDRESS_IN_USE'
                            in scanned_network['PRIVATE_MAC_ADDRESS']
                        ):
                            network.private_mac_in_use = str(
                                _bytes_to_mac_address(
                                    scanned_network['PRIVATE_MAC_ADDRESS'][
                                        'PRIVATE_MAC_ADDRESS_IN_USE'
                                    ]
                                )
                            )
                        if (
                            'PRIVATE_MAC_ADDRESS_VALUE'
                            in scanned_network['PRIVATE_MAC_ADDRESS']
                        ):
                            network.private_mac_value = str(
                                _bytes_to_mac_address(
                                    scanned_network['PRIVATE_MAC_ADDRESS'][
                                        'PRIVATE_MAC_ADDRESS_VALUE'
                                    ]
                                )
                            )
                        if (
                            'PRIVATE_MAC_ADDRESS_VALID'
                            in scanned_network['PRIVATE_MAC_ADDRESS']
                        ):
                            network.private_mac_valid = str(
                                scanned_network['PRIVATE_MAC_ADDRESS'][
                                    'PRIVATE_MAC_ADDRESS_VALID'
                                ]
                            )

                    network.file = fp.name
                    network_attributes = [val for attr, val in network.__dict__.items()]
                    scanned_networks.append(network_attributes)
            except KeyError:
                logger.info(
                    'No private networks scanned in plist file.',
                    extra={'flow': 'no_filter'},
                )

        self.data = scanned_networks
