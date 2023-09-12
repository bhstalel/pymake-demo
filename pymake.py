from inspect import getsourcefile
import os.path
import sys
import logging
import argparse

logging.basicConfig(level=logging.INFO)

current_path = os.path.abspath(getsourcefile(lambda:0))
current_dir = os.path.dirname(current_path)
parent_dir = current_dir[:current_dir.rfind(os.path.sep)]

sys.path.insert(0, parent_dir)

import pymake.modules.libpymake as lib

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=str, default=None, help="Target to build")
    parser.add_argument("-C", "--directory", type=str, help="Custom PyMakefile")
    args = parser.parse_args()

    cwd = os.getcwd()
    if args.directory:
        os.chdir(args.directory)

    handler = lib.PyMakeHandler("PyMakefile.yml")
    handler.run(args.target)

    os.chdir(cwd)