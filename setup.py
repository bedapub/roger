from setuptools import setup

setup(
    name='ROGER',
    packages=['roger'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'werkzeug',
        'click',
        'pandas',
        'biomart',
        'filecache',
        "gseapy",
        "flask_sqlalchemy"
    ],
    entry_points={
        'console_scripts': [
            'roger=roger.cli:cli'
        ],
    },
)