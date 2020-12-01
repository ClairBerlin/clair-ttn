from setuptools import setup, find_packages

# https://click.palletsprojects.com/en/7.x/setuptools/#scripts-in-packages

setup(
    name='clairttn',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Click',
        'ttn',
        'jsonapi_requests',
        'python-dateutil',
        'requests'
    ],
    entry_points='''
    [console_scripts]
    clairttn=clairttn.scripts.clairttn:main
    fixtures=clairttn.scripts.fixtures:get_fixtures
    ''',
)
