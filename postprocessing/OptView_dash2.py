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

from pyoptsparse import History

# Read in the history files given by user 
major_python_version = sys.version_info[0]
parser = argparse.ArgumentParser()
parser.add_argument(
    "histFile", nargs="*", type=str, default="opt_hist.hst", help="Specify the history file to be plotted"
)

args = parser.parse_args()
histList = args.histFile


# -------Retrieving History file data --------
# Currently supports display for one history file
hist = History(histList[0])


# Save needed info from history file to variables 

#These will be used for the dropdowns
conNames = hist.getConNames()
dvNames = hist.getDVNames()
funcNames = conNames + dvNames
numIterations = hist.getCallCounters()
objNames = hist.getObjNames()

print(conNames)
print('dvNames', dvNames)
print(funcNames)
print(objNames)

dvName = "xvar_1"
index = dvName.split("_")[-1]
varname = dvName[::-1].replace(index + "_", "", 1)[::-1]
# print(varname)

varData = hist.getValues(names='xvars', major=False)
print(range(len(varData['xvars'])))
print(numIterations)
# print(values)

#Need info for each variable 



# -------Defining dash app & layout--------

app = dash.Dash(__name__)
# Override expceptions for when elements are defined without initial input
app.config.suppress_callback_exceptions = True

app.layout = html.Div(
    children = [
        html.H1('OptView'),
        html.Div(
            [
                html.Div(
                        [
                            html.H5("Design Groups"),
                            dcc.Dropdown(
                                id='dvarGroup',
                                options=[{'label': i, 'value': i} for i in dvNames],
                                placeholder="Select design group(s)...",
                                multi=True,
                            )
                        ],
                        style={"width": "50%",  "marginRight": "1%"},
                ),
                html.Div(
                        [
                            html.H5("Function Groups"),
                            dcc.Dropdown(
                                id='funcGroup',
                                options=[{'label': i, 'value': i} for i in conNames],
                                placeholder="Select function group(s)...",
                                multi=True,
                            )
                        ],
                        style={"width": "50%",  "marginLeft": "1%"},
                )
            ],
                style={"display": "flex", "paddingLeft": "3%", "paddingRight": "3%" },
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                        id='dvar-child',
                        # options=[{'label': i, 'value': i} for i in dvNames],
                        placeholder="...then select design variable(s)",
                        multi=True,
                        )
                    ],
                    style={"width": "50%", "marginRight": "1%", "paddingTop": "1%"},
                ),
                html.Div(
                    [
                        dcc.Dropdown(id='func-child',
                        # options=[{'label': i, 'value': i} for i in conNames],
                        placeholder="...then select function variable(s)",
                        multi=True,
                        )
                    ],
                    style={"width": "50%", "marginLeft": "1%", "paddingTop": "1%"},
                )
            ],
            style={"display": "flex", "paddingLeft": "3%", "paddingRight": "3%" },
        ),
        dcc.Graph(id="plot"),
    ]
)


# Generate graph based on variable input 
@app.callback(
    dash.dependencies.Output("plot", "figure"),
    [
        dash.dependencies.Input("dvarGroup", "value"),
        dash.dependencies.Input("funcGroup", "value"),
        # dash.dependencies.Input("dvar-child", "value"),
        # dash.dependencies.Input("func-child", "value"),
        # dash.dependencies.Input("axis_scale", "value"),
        # dash.dependencies.Input("scale_type", "value"),
        # dash.dependencies.Input("hidden-div", "value"),
    ],
)
def update_plot(dvarGroup, funcGroup):
    trace = []
    if dvarGroup:
        # Add all traces for each design variable's data
        for var in dvarGroup:
            # Retrieve values for specific DV 
            varData = hist.getValues(names=var, major=False)
            # Add each trace from the current var
            for i in range(len(varData[var][0])):
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(varData[var]))),
                        y=[data[int(i)] for data in varData[var]],
                        name=var,
                        mode="lines+markers",
                    )
                )
            i += 1
            
    # trace = []
    # i = 0
    # if dvarGroup:
    #     varData = hist.getValues(names=dvarGroup, major=False)
    #     for var in dvar:
    #         index = var.split("_")[-1]
    #         varGroup = var.split("_")[0]
    #         trace.append(
    #             go.Scatter(
    #                 x=range(numIterations),
    #                 y=[data[int(index)] for data in varData[varGroup]],
    #                 name=var,
    #                 mode="lines+markers",
    #             )
    #         )
    #         i += 1

    # if func:
    #     for var in func:
    #         index = var.split("_")[-1]
    #         varname = var[::-1].replace(index + "_", "", 1)[::-1]
    #         trace.append(
    #             go.Scatter(
    #                 x=range(Opt.num_iter),
    #                 y=[data[int(index)] for data in Opt.func_data_all[varname]],
    #                 name=var,
    #                 mode="lines+markers",
    #             )
    #         )
    #         i += 1

    fig = {}
    fig["layout"] = {}
    if dvarGroup or funcGroup:
        # if type == "multi":
        #     fig = tools.make_subplots(rows=i, cols=1)
        #     for k in range(i):
        #         fig.append_trace(trace[k], k + 1, 1)
        # else:
        fig["data"] = trace

    fig["layout"].update(
        xaxis={
            "title": {
                "text": "Iterations",
                "font": {"family": "Courier New, monospace", "size": 24, "color": "#7f7f7f"},
            },
            # "type": axisscale,
        },
        yaxis={
            "title": {"text": "Data", "font": {"family": "Courier New, monospace", "size": 24, "color": "#7f7f7f"}},
            # "type": axisscale,
        },
        height=900,
        showlegend=True,
    )

    return fig




# Populate DV variables dropdown based on DV group input
@app.callback(dash.dependencies.Output("dvar-child", "options"), [dash.dependencies.Input("dvarGroup", "value")])
def update_dvar_child(dvar):
    strlist = []
    if dvar:
        for var in dvar:
            varValues = hist.getValues(names=var, major=False)
            num = len(varValues[var][0])
            strlist += [var + "_" + str(i) for i in range(num)]
    return [{"label": i, "value": i} for i in strlist]

# Populate function variables dropwdown based on function group input
@app.callback(dash.dependencies.Output("func-child", "options"), [dash.dependencies.Input("funcGroup", "value")])
def update_func_child(func):
    strlist = []
    if func:
        for var in func:
            varValues = hist.getValues(names=var, major=False)
            num = len(varValues[var][0])
            strlist += [var + "_" + str(i) for i in range(num)]

    return [{"label": i, "value": i} for i in strlist]



# Run if file is used directly, and not imported 
if __name__ == "__main__":
      app.run_server(debug=True)



