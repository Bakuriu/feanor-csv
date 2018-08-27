from setuptools import setup, find_packages
from os import path

from feanor import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='feanor-csv',
    version=__version__,
    description='The ultimate CSV artisan.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Bakuriu/feanor-csv',
    author='Giacomo Alzetta',
    author_email='giacomo.alzetta@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='csv generation schema',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'ply',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest', 'pytest-cov',
    ],
    extras_require={
        'dev': ['check-manifest'],
    },
    entry_points={
        'console_scripts': [
            'feanor=feanor.main:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/Bakuriu/feanor-csv/issues',
        'Source': 'https://github.com/Bakuriu/feanor-csv',
    },
)