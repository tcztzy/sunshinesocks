import sys

from setuptools import setup

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 5)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write("""
==========================
Unsupported Python version
==========================
SunshineSocks requires Python {}.{}, but you're trying to
install it on Python {}.{}.
This may be because you are using a version of pip that doesn't
understand the python_requires classifier. Make sure you
have pip >= 9.0 and setuptools >= 24.2:
    $ python -m pip install --upgrade pip setuptools
""".format(*(REQUIRED_PYTHON + CURRENT_PYTHON)))
    sys.exit(1)

version = __import__('sunshinesocks').__version__

with open('README.rst', encoding='utf-8') as fp:
    readme = fp.read()

setup(
    name="sunshinesocks",
    version=version,
    python_requires='>={}.{}'.format(*REQUIRED_PYTHON),
    license='https://www.gnu.org/licenses/gpl-3.0.en.html',
    description="A fast and modern tunnel proxy that help you.",
    author='tcztzy',
    author_email='tcztzy@gmail.com',
    url='https://github.com/tcztzy/sunshinesocks',
    packages=['sunshinesocks'],
    package_data={
        'sunshinesocks': ['README.rst', 'LICENSE']
    },
    install_requires=[
        'uvloop; implementation_name == "cpython" and platform_system != "Windows"'
    ],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Framework :: AsyncIO',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: Proxy Servers',
    ],
    long_description=readme,
)
