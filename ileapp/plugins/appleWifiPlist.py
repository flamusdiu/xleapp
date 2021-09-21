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
    plist: str = ''

    def __init__(self, network: dict) -> None:

        self.ssid = str(network.get('SSID_STR', ''))
        self.bssid = str(network.get('BSSID', ''))
        self.net_usage = str(network.get('networkUsage', ''))
        self.country_code = str(
            network.get('80211D_IE', {}).get('IE_KEY_80211D_COUNTRY_CODE', ''),
        )
        self.last_updated = str(network.get('lastUpdated', ''))
        self.wnpmd = str(
            network.get('WiFiNetworkPasswordModificationDate', ''),
        )
        self.enabled = network.get('enabled', '')

        wps_prob_resp_ie = network.get('WPS_PROB_RESP_IE', '')
        if bool(wps_prob_resp_ie):
            self.device_name = wps_prob_resp_ie.get('IE_KEY_WPS_DEV_NAME', '')
            self.manufacturer = wps_prob_resp_ie.get('IE_KEY_WPS_MANUFACTURER', '')
            self.serial_number = wps_prob_resp_ie.get('IE_KEY_WPS_SERIAL_NUM', '')
            self.model_name = wps_prob_resp_ie.get(
                'IE_KEY_WPS_MODEL_NAME',
                '',
            )

    def attributes(self) -> list[str]:
        return [val for _, val in self.__dict__.items()]


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
    plist: str = ''

    def __init__(self, network: dict) -> None:
        self.ssid = str(network.get('SSID_STR', ''))
        self.bssid = str(network.get('BSSID', ''))
        self.last_updated = str(network.get('lastUpdated', ''))
        self.last_joined = str(network.get('lastJoined', ''))
        self.added_at = str(network.get('addedAt', ''))
        self.in_known_networks = str(
            network.get(
                'PresentInKnownNetworks',
                '',
            ),
        )

        private_mac_address = network.get('PRIVATE_MAC_ADDRESS', '')
        if bool(private_mac_address):
            self.private_mac_in_use = str(
                _bytes_to_mac_address(
                    private_mac_address.get('PRIVATE_MAC_ADDRESS_IN_USE', ''),
                ),
            )
            self.private_mac_value = getattr(
                str(
                    _bytes_to_mac_address(
                        private_mac_address.get('PRIVATE_MAC_ADDRESS_VALUE', ''),
                    ),
                ),
                '',
            )
            self.private_mac_valid = getattr(
                str(
                    private_mac_address.get('PRIVATE_MAC_ADDRESS_VALID', ''),
                ),
                '',
            )

    def attributes(self) -> list[str]:
        return [val for _, val in self.__dict__.items()]


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
                    network = KnownNetwork(known_network)
                    network.plist = fp.name
                    known_networks.append(network.attributes())
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
                    network = ScannedNetwork(scanned_network)
                    network.plist = fp.name
                    scanned_networks.append(network.attributes())
            except KeyError:
                logger.info(
                    'No private networks scanned in plist file.',
                    extra={'flow': 'no_filter'},
                )

        self.data = scanned_networks
