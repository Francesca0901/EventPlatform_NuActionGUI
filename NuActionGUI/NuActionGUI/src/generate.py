#!/usr/bin/env python3

import os
import shutil
import textwrap
import argparse

from dtm.compiler import compile as dcompile
from stm.compiler import compile as scompile
from ptm.compiler import compile as pcompile
from transformation import transform

def print_header():
    header = textwrap.dedent("""
        ###############################################################
        #                                                             #
        #                       NuActionGUI Tool                      #
        #                                                             #
        ###############################################################
        # Organization: InfSec Group, D-INFK, ETH Zurich              #
        # Authors:      Srdan Krstic, Hoang Nguyen                    #
        # License:      MIT License                                   #
        #                                                             #
        # Description:                                                #
        # Simple Py generator for privacy enhanced web applications   #
        #                                                             #
        ###############################################################
    """)
    print(header)

"""
Simple Python generator for privacy enhanced web applications
"""
BASE_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

"""
Directory navigation
"""
def clean_dir(*path):
    dir = os.path.join(BASE_DIRECTORY, *path)
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)

def set_working_directory(*path):
    dir = os.path.join(BASE_DIRECTORY, *path)
    os.chdir(dir)

if __name__ == "__main__":
    print_header()
    
    transformer = argparse.ArgumentParser()
    transformer.add_argument('-p', '--projectname', help='project name', required=True)
    transformer.add_argument('-dm', '--dtm_file', help='data model file name', default='project.dtm')
    transformer.add_argument('-sm', '--stm_file', help='security model file name', default='project.stm')
    transformer.add_argument('-pm', '--ptm_file', help='privacy model file name', default='project.ptm')
    transformer.add_argument('-re', '--regeneration', action='store_true', help='Regenerate part of the artifacts')
    transformer.add_argument('-o', '--output_folder', help='output folder', default='output')
    args = transformer.parse_args()

    dm_file_path = os.path.abspath(os.path.join(BASE_DIRECTORY, "models", args.projectname, args.dtm_file))
    sm_file_path = os.path.abspath(os.path.join(BASE_DIRECTORY, "models", args.projectname, args.stm_file))
    pm_file_path = os.path.abspath(os.path.join(BASE_DIRECTORY, "models", args.projectname, args.ptm_file))

    with open(dm_file_path, "r") as dm_file:
        dm = dcompile(dm_file.read())
    with open(sm_file_path, "r") as sm_file:
        sm = scompile(dm, sm_file.read())
    with open(pm_file_path, "r") as pm_file:
        pm = pcompile(dm, sm, pm_file.read())

    transform(args.projectname, dm, sm, pm, args.regeneration, args.output_folder)