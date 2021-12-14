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
        'pypng',
        # Pin transitive dependency of the jsonapi_requests library until fixed;
        # See https://github.com/socialwifi/jsonapi-requests/issues/53
        'tenacity==7.0' 
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points='''
    [console_scripts]
    clair-ttn=clairttn.scripts.clairttn:main
    clair-get-device-id=clairttn.scripts.get_clair_id:get_device_id
    clair-generate-fixtures-from-storage=clairttn.scripts.generate_fixtures:generate_fixtures
    clair-register-device-in-managair=clairttn.scripts.register_device:register_device_in_managair
    clair-generate-nfc-config=clairttn.scripts.nfc_config:generate_nfc_config
    ''',
)
