from setuptools import setup

with open('README.rst', encoding='utf-8') as fp:
    readme = fp.read()

setup(
    name="sunshinesocks",
    version="0.1.0",
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
