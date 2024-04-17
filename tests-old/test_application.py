from collections import UserDict


def test_device_creation(test_device):
    assert isinstance(test_device, UserDict)
    assert {
        "IOS Version": 14.6,
        "ProductBuildVersion": "18F72",
        "Product": "iPhone OS",
        "Last Known ICCID": "89012803320056608813",
        "Reported Phone Number": "19048075555",
        "IMEI": "356720085253071",
    } == test_device
    assert test_device.table() == [
        ["IOS Version", 14.6],
        ["Product Build Version", "18F72"],
        ["Product", "iPhone OS"],
        ["Last Known ICCID", "89012803320056608813"],
        ["Reported Phone Number", "19048075555"],
        ["IMEI", "356720085253071"],
    ]
