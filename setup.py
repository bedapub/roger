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
        "gseapy",
        "rpy2",
        "numpy",
        # "cmapPy", TODO no support for python 3 for now
        "flask_sqlalchemy",
        "Flask-Caching"
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    entry_points={
        'console_scripts': [
            'roger=roger.main:entry_point'
        ],
    },
)
