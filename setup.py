#!/usr/bin/env python

"""
    NURBS-Python (geomdl) Setup Script
    NURBS-Python is released under the MIT License. Copyright (c) Onur Rauf Bingol.

    The setup script directly depends on "setuptools" package and it does not fallback to "distutils" which might
    cause issues on some Python distributions, especially on the embedded distributions.

    To solve this issue, you may want to start with installing "pip" using the "get_pip.py" script
    from the following link if it doesn't exist on your distribution:

    https://pip.pypa.io/en/stable/installing/

    Then, you may install "setuptools" package using the following command:

        pip install setuptools

    "setuptools" is a collection of enhancements to the Python's "distutils" package. You may check its documentation
    from the following link:

    http://setuptools.readthedocs.io/en/latest/setuptools.html#command-reference

    It also comes installed by default with the official Python.org distribution and in all "conda" environments.
    On the other hand, it might require an update. You may update your "setuptools" package using the following command:

        pip install setuptools --upgrade

    or

        conda update setuptools

    depending on the package manager that you are using.

    After installing "pip", you may also consider installing NURBS-Python (geomdl) via "pip install geomdl" or
    alternatively, you may use "conda" package on https://anaconda.org/orbingol/geomdl
"""

from setuptools import setup
from setuptools import Extension
from setuptools.command.install import install as install_command
from setuptools.command.test import test as test_command
from distutils.command.clean import clean as clean_command
import sys
import os
import re
import shutil

# Global variables to control generation of optional Cython-compiled library core module
BUILD_FROM_CYTHON = False
BUILD_FROM_SOURCE = False


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


# Implemented from http://stackoverflow.com/a/41110107
def get_property(prop, project):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    return result.group(1)


class InstallCommand(install_command):
    """ Overrides pip install command to control generation of optional Cython-compiled library core module """
    user_options = install_command.user_options + [
        ('use-cython', None, 'Cythonize and compile geomdl.core'),
        ('use-source', None, 'Compile geomdl.core from the source files'),
    ]

    def initialize_options(self):
        install_command.initialize_options(self)
        self.use_cython = 0
        self.use_source = 0

    def finalize_options(self):
        install_command.finalize_options(self)

    def run(self):
        global BUILD_FROM_CYTHON, BUILD_FROM_SOURCE
        BUILD_FROM_CYTHON = True if self.use_cython > 0 else False
        BUILD_FROM_SOURCE = True if self.use_source > 0 else False
        install_command.run(self)


# Reference: https://docs.pytest.org/en/latest/goodpractices.html
class PyTest(test_command):
    """ Allows test command to call py.test """
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        test_command.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


class SetuptoolsClean(clean_command):
    """ Cleans Cython-generated source files and setuptools-generated directories """
    def run(self):
        # Call parent method
        clean_command.run(self)

        # Clean setuptools-generated directories
        st_dirs = ['dist', 'build', 'geomdl.egg-info']

        print("Removing setuptools-generated directories")
        for d in st_dirs:
            d_path = os.path.join(os.path.dirname(__file__), d)
            shutil.rmtree(d_path, ignore_errors=True)

        # Find list of files with .c extension
        flist, flist_path = read_files("geomdl", ".c")

        # Clean files with .c extensions
        if flist_path:
            print("Removing Cython-generated source files")
            for f in flist_path:
                f_path = os.path.join(os.path.dirname(__file__), f)
                os.unlink(f_path)


def read_files(project, ext):
    """ Reads files inside the input project directory. """
    project_path = os.path.join(os.path.dirname(__file__), project)
    file_list = os.listdir(project_path)
    flist = []
    flist_path = []
    for f in file_list:
        f_path = os.path.join(project_path, f)
        if os.path.isfile(f_path) and f.endswith(ext) and f != "__init__.py":
            flist.append(f.split('.')[0])
            flist_path.append(f_path)
    return flist, flist_path


def copy_files(src, ext, dst):
    """  Copies files with extensions "ext" from "src" to "dst" directory. """
    src_path = os.path.join(os.path.dirname(__file__), src)
    dst_path = os.path.join(os.path.dirname(__file__), dst)
    file_list = os.listdir(src_path)
    for f in file_list:
        if f == '__init__.py':
            continue
        f_path = os.path.join(src_path, f)
        if os.path.isfile(f_path) and f.endswith(ext):
            shutil.copy(f_path, dst_path)


def make_dir(project, gen_init_py=True):
    """ Creates the project directory for compiled modules. """
    project_path = os.path.join(os.path.dirname(__file__), project)
    # Delete the directory and the files inside it
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    # Create the directory
    os.mkdir(project_path)
    # We need a __init__.py file inside the directory
    if gen_init_py:
        with open(os.path.join(project_path, '__init__.py'), 'w') as fp:
            fp.write('__version__ = "' + str(get_property('__author__', 'geomdl')) + '"\n')
            fp.write('__version__ = "' + str(get_property('__version__', 'geomdl')) + '"\n')
            fp.write('__license__ = "MIT"\n')


def in_argv(arg_list):
    """ Checks if any of the elements of the input list is in sys.argv array. """
    for arg in sys.argv:
        for parg in arg_list:
            if parg == arg or arg.startswith(parg):
                return True
    return False


possible_cmds = ['install', 'build', 'bdist']
packages = ['geomdl', 'geomdl.visualization']

# Cython and compiled C module options
# Ref: https://gist.github.com/ctokheim/6c34dc1d672afca0676a
if in_argv(possible_cmds) and '--use-source' in sys.argv:
    BUILD_FROM_SOURCE = True
    sys.argv.remove('--use-source')

if in_argv(possible_cmds) and '--use-cython' in sys.argv:
    # Try to import Cython
    try:
        from Cython.Build import cythonize
    except ImportError:
        raise ImportError("Cython is required for this step. Please install it via 'pip install cython'")

    BUILD_FROM_CYTHON = True
    sys.argv.remove('--use-cython')

# We don't want to include any compiled files with the distribution
ext_modules = []

if BUILD_FROM_CYTHON or BUILD_FROM_SOURCE:
    # Choose the file extension
    file_ext = '.py' if BUILD_FROM_CYTHON else '.c'

    # Create Cython-compiled module directory
    make_dir('geomdl/core')

    # Create extensions
    optional_extensions = []
    fnames, fnames_path = read_files('geomdl', file_ext)
    for fname, fpath in zip(fnames, fnames_path):
        temp = Extension('geomdl.core.' + str(fname), sources=[fpath])
        optional_extensions.append(temp)

    # Call Cython when "python setup.py build_ext --use-cython" is executed
    if BUILD_FROM_CYTHON:
        ext_modules = cythonize(optional_extensions, compiler_directives={'language_level': sys.version_info[0]})

    # Compile from C source when "python setup.py build_ext --use-source" is executed
    if BUILD_FROM_SOURCE:
        ext_modules = optional_extensions

    # Add Cython-compiled module to the packages list
    packages.append('geomdl.core')

# Required packages for older Python versions
required = []

# Add Enum type support for Python versions < 3.4
if sys.version_info[:2] < (3, 4):
    required += ['enum34']

# Add LRU cache support for Python versions < 3.3
if sys.version_info[:2] < (3, 3):
    required += ['backports.functools_lru_cache']

# Add type hints support for Python versions < 3.5
if sys.version_info[:2] < (3, 5):
    required += ['typing']

data = dict(
    name='geomdl',
    version=get_property('__version__', 'geomdl'),
    description='Object-oriented B-Spline and NURBS evaluation library',
    long_description=read('DESCRIPTION.rst'),
    license='MIT',
    author='Onur Rauf Bingol',
    author_email='nurbs-python@googlegroups.com',
    url='https://github.com/orbingol/NURBS-Python',
    keywords='NURBS B-Spline curve surface CAD modeling visualization surface-generator',
    packages=packages,
    install_requires=['six>=1.9.0'] + required,
    tests_require=["pytest>=3.0.0"],
    cmdclass={"install": InstallCommand, "test": PyTest, 'clean': SetuptoolsClean},
    ext_modules=ext_modules,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    project_urls={
        'Documentation': 'http://nurbs-python.readthedocs.io/',
        'Source': 'https://github.com/orbingol/NURBS-Python',
        'Tracker': 'https://github.com/orbingol/NURBS-Python/issues',
    },
)


if __name__ == '__main__':
    setup(**data)
