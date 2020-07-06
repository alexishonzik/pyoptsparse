
# This dash version of OptView makes use of the new API 
# to read in the history file, rather than using the 
# OptView baseclass. This should be more maintainab;e
# for adding new features or displaying new information with OptView.

#!/usr/bin/python
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly import tools
import numpy as np
import argparse
from sqlitedict import SqliteDict
import shelve

import sys
import os 
# sys.path.append(os.path.abspath('../pyoptsparse'))
# from pyOpt_history import History
from pyoptsparse import History

# Read in the history files given by user 
major_python_version = sys.version_info[0]
parser = argparse.ArgumentParser()
parser.add_argument(
    "histFile", nargs="*", type=str, default="opt_hist.hst", help="Specify the history file to be plotted"
)

args = parser.parse_args()
histList = args.histFile


# Currently supports display for one history file
hist = History(histList[0])


# Save needed info from history file to variables 

#These will be used for the dropdowns
conNames = hist.getConNames()
dvNames = hist.getDVNames()
objNames = hist.getObjNames()

print(conNames)
print(dvNames)
print(objNames)

#Need info for each variable 
