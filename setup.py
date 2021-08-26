from setuptools import setup, find_packages

# https://click.palletsprojects.com/en/7.x/setuptools/#scripts-in-packages

setup(
    name='clairttn',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'click',
        'paho-mqtt',
        'jsonapi_requests',
        'python-dateutil',
        'requests',
        'pyqrcode',
        'pypng'
    ],
    entry_points='''
    [console_scripts]
    clair-ttn=clairttn.scripts.clairttn:main
    clair-generate-fixtures-from-storage=clairttn.scripts.generate_fixtures:generate_fixtures
    clair-register-device-in-ttn=clairttn.scripts.register_device:register_device_in_ttn
    clair-register-device-in-managair=clairttn.scripts.register_device:register_device_in_managair
    clair-generate-nfc-config=clairttn.scripts.nfc_config:generate_nfc_config
    ''',
)
