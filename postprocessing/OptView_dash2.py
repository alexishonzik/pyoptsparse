# This dash version of OptView makes use of the new API 
# to read in the history file, rather than using the 
# OptView baseclass. This should be more maintainab;e
# for adding new features or displaying new information with OptView.

#!/usr/bin/python
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly import subplots
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

# print(conNames)
# print('dvNames', dvNames)
# print(funcNames)
# print(objNames)

dvName = "xvar_1"
index = dvName.split("_")[-1]
varname = dvName[::-1].replace(index + "_", "", 1)[::-1]
# print(varname)

varData = hist.getValues(names='xvars', major=False)
# print(range(len(varData['xvars'])))
# print(numIterations)
# print(values)

varData2 = hist.getValues(names='con', major=False)

y=[data.real[int(0)] for data in varData['xvars']]
# print('ok',y)
y=[data[int(0)] for data in varData['xvars']]
# for data in varData['xvars']:
#     print('here',data)
#     print(type(data[0]))
#     print('data',data[0])
# print(y)

#Need info for each variable 
#PYTHON2vs3 in using range
y=[data.real[int(0)] for data in varData2['con']]
y=[data[int(0)] for data in varData2['con']]


dvInfo = hist.getDVInfo('xvars')
lowerB = dvInfo['lower']
upperB = dvInfo['upper']
print(lowerB)
print('dvInfo', dvInfo)



# -------Defining dash app & layout--------

app = dash.Dash(__name__)
# Override expceptions for when elements are defined without initial input
app.config.suppress_callback_exceptions = True

app.layout = html.Div(
    children = [
        html.H3('OptView'),
        html.Div([
                    dcc.Graph(id="plot"),
                 ],
                  style={"width": "80%", "margin":"0 auto"},
        ),
         html.Div( [
        # html.Div(
        #     [
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
                        style={"marginRight": "2%"},
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
                        style={"marginRight": "2%"},
                ),
        #     ],
        #        style={"display": "flex", "paddingLeft": "3%", "paddingRight": "3%", "width": "80%" },
        # ),
        # html.Div(
        #     [
        #         html.Div(
        #             [
        #                 dcc.Dropdown(
        #                 id='dvar-child',
        #                 # options=[{'label': i, 'value': i} for i in dvNames],
        #                 placeholder="...then select design variable(s)",
        #                 multi=True,
        #                 )
        #             ],
        #             style={"marginRight": "1%", "paddingTop": "1%"},
        #         ),
        #         html.Div(
        #             [
        #                 dcc.Dropdown(id='func-child',
        #                 # options=[{'label': i, 'value': i} for i in conNames],
        #                 placeholder="...then select function variable(s)",
        #                 multi=True,
        #                 )
        #             ],
        #             style={"marginLeft": "1%", "paddingTop": "1%"},
        #         )
        #     ],
        #     style={"display": "flex", "paddingLeft": "3%", "paddingRight": "3%", "width": "80%" },
        # ),
        html.Div(
            [
                html.H5("Graph Type"),
                dcc.RadioItems(
                    id='plot-type',
                    options=[
                        {'label': 'Stacked', 'value': 'stacked'},
                        {'label': 'Shared', 'value': 'shared'},
                    ],
                    value='shared'
                    )
            ],
             style={"width": "30x", "marginRight": "2%"},
        ),
        html.Div(
            [
                html.H5("Data Type"),
                dcc.Checklist(
                    id='data-type',
                    options=[
                        {'label': 'Show Bounds', 'value': 'bounds'},
                        {'label': 'Show Major Iterations', 'value': 'major'},
                        {'label': 'Log Scale', 'value': 'log'},
                        {'label': 'Apply Scaling Factor', 'value': 'scale'},
                    ],
                    )
            ],
             style={"width": "30x"},
        ), 
         ],
          style={"display": "flex", "justify-content": "center", "margin":"50px"},
         ),
    ]
)


# Generate graph based on variable input 
@app.callback(
    dash.dependencies.Output("plot", "figure"),
    [
        dash.dependencies.Input("dvarGroup", "value"),
        dash.dependencies.Input("funcGroup", "value"),
        dash.dependencies.Input("plot-type", "value"),
        dash.dependencies.Input("data-type", "value"),
        # dash.dependencies.Input("dvar-child", "value"),
        # dash.dependencies.Input("func-child", "value"),
        # dash.dependencies.Input("axis_scale", "value"),
        # dash.dependencies.Input("scale_type", "value"),
        # dash.dependencies.Input("hidden-div", "value"),
    ],
)
def update_plot(dvarGroup, funcGroup, plotType, dataType):
    trace = []
    numV = 0
    dvData = []
    fig = {}
    fig["layout"] = {}

    numRows = 0;
    if not dvarGroup and not funcGroup:
        numRows = 1;
    if funcGroup:
        numRows += len(funcGroup)
    if dvarGroup:
        numRows += len(dvarGroup)
    
    if plotType == "stacked":
        print('hi', numRows)
        fig = subplots.make_subplots(rows=numRows)

    if dvarGroup:
        # Add all traces for each design variable's data
        for var in dvarGroup:
            # Retrieve values for specific DV 
            numV += 1
            dvData = []
            if (dataType and ('major' in dataType)):
                dvData = hist.getValues(names=var, major=True)
            else :
                 dvData = hist.getValues(names=var, major=False)
            # Add each trace from the current dvar
            for i in range(len(dvData[var][0])):
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(dvData[var]))),
                        y=[data.real[int(i)] for data in dvData[var]],
                        name=var+"_"+str(i),
                        # marker_color='blue',
                        mode="lines+markers",
                    )
                )
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
            # add bounds information for dv variable 
            if dataType and 'bounds' in dataType:
                dvInfo = hist.getDVInfo(var)
                lowerB = dvInfo['lower']
                upperB = dvInfo['upper']
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(dvData[var]))),
                        y=lowerB,
                        name=var+"_lowerBound",
                        # marker_color='blue',
                        line = { "dash":"dash"}
                    )
                )
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(dvData[var]))),
                        y=upperB,
                        name=var+"_upperBound",
                        # marker_color='blue',
                        line = { "dash":"dash"}
                    )
                )
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)

                    
        
    
    funcData=[]
    if funcGroup:
        for var in funcGroup:
            # Retrieve values for specific function 
            numV += 1
            funcData = []
            if (dataType and ('major' in dataType)):
                funcData = hist.getValues(names=var, major=True)
            else :
                 funcData = hist.getValues(names=var, major=False)
            # Add each trace from the current fucntion
            for i in range(len(funcData[var][0])):
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(funcData[var]))),
                        y=[data.real[int(i)] for data in funcData[var]],
                        name=var+"_"+str(i),
                        # marker_color=i,
                        mode="lines+markers",
                    )
                )
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
            
             # add bounds information for dv variable 
            if dataType and 'bounds' in dataType:
                funcInfo = hist.getConInfo(var)
                lowerB = funcInfo['lower']
                upperB = funcInfo['upper']
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(funcData[var]))),
                        y=lowerB,
                        name=var+"_lowerBound",
                        # marker_color='blue',
                        line = { "dash":"dash"}
                    )
                )
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(funcData[var]))),
                        y=upperB,
                        name=var+"_upperBound",
                        # marker_color='blue',
                        # mode="lines",
                        line = { "dash":"dash"}
                    )
                )
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)
           


    # fig = {}
    # fig["layout"] = {}
    # if dvarGroup or funcGroup:
    #     if plotType == "stacked":
    #         fig = subplots.make_subplots(rows=2)
    #         print("hi", len(trace))
        #     for k in range(len(trace)):
        #         fig.append_trace(trace[k], 1, 1)
    if plotType == "shared":
        fig["data"] = trace

    fig["layout"].update(
        title = {
            "text": "OptView"
        },
        xaxis={
            "title": {
                "text": "Iterations",
                "font": {"family": "Courier New, monospace", "size": 24, "color": "#7f7f7f"},
            },
        },
        yaxis={
            "title": {"text": "Data", "font": {"family": "Courier New, monospace", "size": 24, "color": "#7f7f7f"}},
            "type": 'log' if (dataType and ('log' in dataType)) else 'linear'
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



