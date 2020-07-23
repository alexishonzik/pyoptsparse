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


# Saving names for drop down menu
dvNames = hist.getDVNames()
conNames = hist.getConNames()
objNames = hist.getObjNames()
funcNames = conNames + objNames 

# -------Defining dash app & layout--------

app = dash.Dash(__name__)
# Override expceptions for when elements are defined without initial input
app.config.suppress_callback_exceptions = True

external_css = [
    # # Normalize the CSS
    # "https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
    # # Fonts
    # "https://fonts.googleapis.com/css?family=Open+Sans|Roboto",
    # "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
    "https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css"
]

for css in external_css:
    app.css.append_css({"external_url": css})

app.layout = html.Div(
    children = [
        html.Nav(
            children=[
                html.Img(src=app.get_asset_url("/MDOLogo.png"), style={"height":"100px", "width":"200px"}),
                html.H1(["OptView"], style={"margin-top": "20px"}),
            ],
            style={"display":"flex"}
        ),
        html.Div([
                    dcc.Graph(id="plot", style={'width': '80%'},
                    config={"scrollZoom": True, "showTips": True}),
                 ],
        ),
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
                        style={"marginRight": "2%"},
                ),
                html.Div(
                        [
                            html.H5("Function Groups"),
                            dcc.Dropdown(
                                id='funcGroup',
                                options=[{'label': i, 'value': i} for i in funcNames],
                                placeholder="Select function group(s)...",
                                multi=True,
                            )
                        ],
                        style={"marginRight": "2%"},
                ),

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
                                    {'label': 'Show Min/Max', 'value': 'minMax'},
                                    {'label': 'Show Absolute Delta', 'value': 'delta'},
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
    ],
)
def update_plot(dvarGroup, funcGroup, plotType, dataType):
    trace = []
    numV = 0
    # dvData = []
    fig = {}
    fig["layout"] = {}

    # Create subplots if stacked plot type is chosen 
    if plotType == "stacked":
        # Determine # of plots
        numRows = 0;
        if not dvarGroup and not funcGroup:
            numRows = 1;
        if funcGroup:
            numRows += len(funcGroup)
        if dvarGroup:
            numRows += len(dvarGroup)
        # Determine all variable names for axis
        varsNames = []
        if dvarGroup and funcGroup:
            varsNames = dvarGroup + funcGroup
        elif dvarGroup:
                varsNames = dvarGroup
        elif funcGroup:
            varsNames = funcGroup
        fig = subplots.make_subplots(rows=numRows, subplot_titles=varsNames)
        for i in fig['layout']['annotations']:
            i['font'] = dict(size=12)
        fig.update_yaxes(type=('log' if (dataType and ('log' in dataType)) else 'linear'))

    # Add traces for each DV selected 
    if dvarGroup:
        for var in dvarGroup:
            numV += 1
            dvData = []
            # Get values for var, based on input selection 
            if dataType:
                if (('major' in dataType) and ('scale' in dataType)):
                    dvData = hist.getValues(names=var, major=True, scale=True)
                elif ('major' in dataType):
                    dvData = hist.getValues(names=var, major=True) 
                elif ('scale' in dataType): 
                    dvData = hist.getValues(names=var, major=False, scale=True) 
                else:
                    dvData = hist.getValues(names=var, major=False)
            else :
                 dvData = hist.getValues(names=var, major=False)
            # Change values if Abs Delta selected
            if dataType and 'delta' in dataType:
                tempDV = dvData[var].copy()
                for i in list(range(len(dvData[var]))):
                    for j in list(range(len(dvData[var][i]))):
                        if (i!=0):
                            dvData[var][i][j] = abs(dvData[var][i][j] - tempDV[i-1][j])
                        else:
                            dvData[var][i][j] = 0;
            # If minMax selected, append only minMax traces0
            if(dataType and 'minMax' in dataType):
                trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(dvData[var]))),
                            y=[max(data.real) for data in dvData[var]],
                            name=var+"_max",
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 1 }       
                        )
                    )
                trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(dvData[var]))),
                            y=[min(data.real) for data in dvData[var]],
                            name=var+"_min",
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 3 }       
                        )
                    )
                # Add min & max traces to this var's subplot
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)
            # If minMax not selected, add all traces 
            else:
                for i in range(len(dvData[var][0])):
                    trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(dvData[var]))),
                            y=[data.real[int(i)] for data in dvData[var]],
                            name=var+"_"+str(i),
                            # marker_color='blue',
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 3}       
                        )
                    )
                    # Add trace to this var's subplot
                    if plotType == "stacked":
                        fig.append_trace(trace[len(trace)-1], numV, 1)
            # Add upper & lower bounds traces 
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
                        line = { "dash":"dash", "width": 3}
                    )
                )
                trace.append(
                    go.Scatter(
#PYTHON2vs3 in using range
                        x=list(range(len(dvData[var]))),
                        y=upperB,
                        name=var+"_upperBound",
                        # marker_color='blue',
                        line = { "dash":"dash", "width": 3}
                    )
                )
                # Add upper & lower bound traces to this var's subplot
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)

     # Add traces for each function selected 
    funcData=[]
    if funcGroup:
        for var in funcGroup:
            numV += 1
            # Get values for var, based on input selection 
            funcData = []
            if dataType:
                if (('major' in dataType) and ('scale' in dataType)):
                    funcData = hist.getValues(names=var, major=True, scale=True)
                elif ('major' in dataType):
                    funcData = hist.getValues(names=var, major=True) 
                elif ('scale' in dataType): 
                    funcData = hist.getValues(names=var, major=False, scale=True) 
                else: 
                    funcData = hist.getValues(names=var, major=False)
            else :
                 funcData = hist.getValues(names=var, major=False)
            # Change values if Abs Delta selected
            if dataType and 'delta' in dataType:
                tempDV = funcData[var].copy()
                for i in list(range(len(funcData[var]))):
                    for j in list(range(len(funcData[var][i]))):
                        if (i!=0):
                            funcData[var][i][j] = abs(funcData[var][i][j] - tempDV[i-1][j])
                        else:
                            funcData[var][i][j] = 0;
            # If minMax selected, append only minMax traces
            if(dataType and 'minMax' in dataType):
                trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(funcData[var]))),
                            y=[max(data.real) for data in funcData[var]],
                            name=var+"_max",
                            # marker_color='blue',
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 3}       
                        )
                    )
                trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(funcData[var]))),
                            y=[min(data.real) for data in funcData[var]],
                            name=var+"_min",
                            # marker_color='blue',
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 3}       
                        )
                    )
                # Add min & max traces to this var's subplot
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)
            # If minMax not selected, add all traces 
            else:
                for i in range(len(funcData[var][0])):
                    trace.append(
                        go.Scatter(
    #PYTHON2vs3 in using range
                            x=list(range(len(funcData[var]))),
                            y=[data.real[int(i)] for data in funcData[var]],
                            name=var+"_"+str(i),
                            # marker_color=i,
                            mode="lines+markers",
                            marker = { "size": 5},
                            # line = { "width": 3}       
                        )
                    )
                    # Add trace to this var's subplot
                    if plotType == "stacked":
                        fig.append_trace(trace[len(trace)-1], numV, 1)
                
            # Add upper & lower bounds traces 
            if dataType and 'bounds' in dataType:
                if (var == 'obj'):
                    funcInfo = hist.getConInfo(var)
                    lowerB = funcInfo['lower']
                    upperB = funcInfo['upper']
                else:
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
                        line = { "dash":"dash", "width": 3}
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
                        line = { "dash":"dash", "width": 3}
                    )
                )
                 # Add upper & lower bound traces to this var's subplot
                if plotType == "stacked":
                    fig.append_trace(trace[len(trace)-1], numV, 1)
                    fig.append_trace(trace[len(trace)-2], numV, 1)
           
    if plotType == "shared":
        fig["data"] = trace

    fig["layout"].update(
        autosize = True,
        # title = {
        #     "font" : {"size" : 25}
        # },
        # xaxis= {
        #     "title": {
        #         "text": "Iterations" if (plotType == "shared"),
        #         "font": {"family": "Arial, Helvetica, sans-serif", "size": 24},
        #     },
        # },
        yaxis={
            "type": 'log' if (dataType and ('log' in dataType)) else 'linear'
        },
        height= 600,
        showlegend=True,
        legend = {
            "orientation" : "h"
        },
        font = {"size" : 12}
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



