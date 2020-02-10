# -*- coding: utf-8 -*-

# this is a setup script to create an executable of this project.
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('app.py', base='Console')
]

setup(name='jama-test-progress',
      version='0.2',
      description='Create charts to indicate test progress',
      executables=executables
      )