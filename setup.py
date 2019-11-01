import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('bkp9151/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='bkp9151',
    version=version,
    description='BK Precision 9151 Python Library/Driver',
    url='https://github.com/wstanislaus/bkp9151',
    download_url='https://github.com/wstanislaus/bkp9151.git',
    license='MIT',
    author='William Stanislaus',
    author_email='wstanislaus@gmail.com',
    packages=[str('bkp9151')],
    platforms='any',
    install_requires=['pyserial>=2.6']
)
