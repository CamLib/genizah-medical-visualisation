from setuptools import setup, find_packages


def get_version(filename):
    '''
    Parse the value of the __version__ var from a Python source file
    without running/importing the file.
    '''
    import re
    version_pattern = r'^ *__version__ *= *[\'"](\d+\.\d+\.\d+)[\'"] *$'
    match = re.search(version_pattern, open(filename).read(), re.MULTILINE)

    assert match, ('No version found in file: {!r} matching pattern: {!r}'
                   .format(filename, version_pattern))

    return match.group(1)


setup(
    name='genizah-data-tools',
    version='0.0.0',  #get_version('src/genizahdata/_version.py'),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    author='Hal Blackburn',
    install_requires=[
        'docopt <1'
    ],
    test_requires=[
        'pytest'
        'pytest-lazy-fixture'
        'pytest-cov'
    ],
    entry_points={
        'console_scripts': [
            'genizah-titles-extract=genizahdata:extract_genizah_titles_cmd'
        ]
    }
)
