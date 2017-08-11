#coding=utf-8
from setuptools import setup
import aiossdb
packages = [
    'aiossdb'
]
setup(
    name="aiossdb",
    version=aiossdb.__version__,
    author="Kevin",
    author_email="dgt_x@foxmail.com",
    description="aiossdb is a library for accessing a ssdb database from the asyncio",
    long_description="aiossdb is a library for accessing a ssdb database from the asyncio",
    license="MIT",
    keywords="aiossdb",
    packages=packages,
    package_dir={'aiossdb': 'aiossdb'},
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python 3',
        'Intended Audience :: Developers',
        'License :: Jinchongzi Licence',
        'Operating System :: Mac OS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data=True,
    extras_require={},
)
