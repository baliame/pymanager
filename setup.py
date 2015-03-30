#from setuptools import setup, find_packages
from setuptools import *
from pymanager import version

description='A process manager in Python.'
long_description = open('README.rst').read()

setup(
    name='pymanager',
    version=version,
    description=description,
    long_description=long_description,
    url='https://github.com/baliame/pymanager',
    author='Baliame',
    author_email='akos.toth@cheppers.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='process manager management',
    py_modules=["pymanager"],
    packages=find_packages(),
    install_requires = [
    	'bottle', 'requests'
    ],
    entry_points= {
    	'console_scripts': [
    		'pymanager = pymanager:main'
    	]
    },
)
