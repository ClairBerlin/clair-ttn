from setuptools import setup, find_packages

# https://click.palletsprojects.com/en/7.x/setuptools/#scripts-in-packages

setup(
    name='clairttnesr',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'ttn'
    ],
    entry_points='''
    [console_scripts]
    clairttnesr=clairttnesr.scripts.clairttnesr:main
    ''',
)
