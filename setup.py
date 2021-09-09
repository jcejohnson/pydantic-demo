
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='aktorz',

    version='0.1.2-rc1',

    description='Learning pydantic with a simple actors json file.',

    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/jcejohnson/aktorz',

    author='James Johnson',
    author_email='jcejohnson@users.noreply.github.com',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        # "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],

    keywords='json, jsonref',

    package_dir={'': 'src'},
    packages=find_packages(where='src'),  # Required

    install_requires=(here / 'requirements.txt').read_text(encoding='utf-8').split('\n'),

    entry_points={  # Optional
        'console_scripts': [
            'aktorz=aktorz.cli:main'
        ],
    },
)
