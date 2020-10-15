from setuptools import setup, find_packages

# https://click.palletsprojects.com/en/7.x/setuptools/#scripts-in-packages

found_packages = find_packages()
print("packages: {}".format(found_packages))

setup(
    name='clairttn',
    version='0.1',
    packages=found_packages,
    install_requires=[
        'Click',
        'ttn',
        'jsonapi_requests',
        'python-dateutil'
    ],
    entry_points='''
    [console_scripts]
    clairttn=clairttn.scripts.clairttn:main
    ''',
)
