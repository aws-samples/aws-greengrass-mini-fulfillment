"""
pyutu
-------------

"""
import os
from setuptools import setup
from servode import __version__


def open_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


setup(
    name='servode',
    version=__version__,
    url='https://github.com/brettf/servode',
    license=open("LICENSE").read(),
    author='Brett Francis',
    author_email='brett_francis@me.com',
    description='An ode to Python code that uses Servos.',
    long_description=open_file("README.rst").read(),
    py_modules=['servode'],
    zip_safe=False,
    include_package_data=True,
    packages=["servode"],
    keywords='servo robot robotics',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Robot Framework :: Library'
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ]
)