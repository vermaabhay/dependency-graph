# standard library
import os
# dash libs
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import datetime
import glob
from pandas.io.json import json_normalize
import json
import yaml
import visdcc
from scripts import cypherNeo4j
from scripts.appProps import convertYamlTojson
import redis
from scripts.getUpdatedYaml import updateYamls
from scripts.redisCache import expireCache
from flask import redirect
from scripts.time_tracker import TimeTracker

time_tracker = TimeTracker()


redis_db = redis.StrictRedis(host="localhost", charset="utf-8", port=6379, db=0, decode_responses=True)


###########################
# Data Manipulation / Model
###########################

'''Returns the list of component names'''
comps = [os.path.basename(f).split('.')[0] for f in glob.glob("services/components/*.yml")]

def get_header():
        # Page Header
    header = html.Div([
        html.H4('Snapdeal Infra Dependency Graph',style={'textAlign': 'center'})
    ])
    return header

def get_tabs():
    get_tabs = html.Div([
        dcc.Tabs(id="tabs", value='CompGraph', children=[
                dcc.Tab(label='Component Graph', value='CompGraph'),
                dcc.Tab(label='Component Dependency Graph', value='CompDepGraph'),
                dcc.Tab(label='SubComponent Dependency Graph', value='SubCompDepGraph'),
                dcc.Tab(label='Component Component Dependency Graph', value='CompCompDepGraph'),
            ]),
        html.Div(id='tab-output')
        ])
    return get_tabs

def get_comps():

    return comps
   

def get_subComps(comp):

    '''Returns the list of sub-component names for a component name from the database'''
    doc = convertYamlTojson(comp)
    subComps = json_normalize(doc['subcomponents']).name.tolist()
    return subComps


def load_comp_names():

    comp = (
        [{'label': comp, 'value': comp}
         for comp in get_comps()]
    )
    return comp
 

def display_comp():
    comp =  html.Div([
            html.Br(),
            html.Div([
            html.Div([
                html.Div([
                    html.Div('Component', className='three columns'),
                    html.Div(dcc.Dropdown(id='component-selector',
                                      options=load_comp_names()),
                             className='nine columns')
                ]),
            ], className='offset-by-three six columns'),
        ], className='row'),
            html.Div([
                html.Div(id='graph-data-comp')
            ]),
        ])
    return comp

def display_comp_subcomp():
    comp_subcomp = html.Div([
              html.Br(),
              html.Div([
              html.Div([
            # Select Component Dropdown
                html.Div([
                    html.Div('Component', className='three columns'),
                    html.Div(dcc.Dropdown(id='component-selector',
                                      options=load_comp_names()),
                             className='nine columns')
                ]),
            # Select SubComponent Dropdown
                html.Div([
                    html.Div('Sub Component', className='three columns'),
                    html.Div(dcc.Dropdown(id='subcomponent-selector'),
                             className='nine columns')
                ]),
            ], className='offset-by-three six columns'),
        ], className='row'),
        html.Div([
                html.Div(id='graph-data-subcomp')
        ]),
        ])
    return comp_subcomp


def get_sample_visdcc():
    sample_visdcc = html.Div(
                    visdcc.Network(id='net'),style={'display': 'none'})
    return sample_visdcc


@time_tracker.time_track()
def get_graph(comp,tab,subcomp=None):

    if(subcomp is not None):
        redis_key = comp+":"+tab+":"+subcomp
    else:
        redis_key = comp+":"+tab
    
    try:
        cache_result = redis_db.get(redis_key)
    except Exception as err:
        print("Can't Read From Redis:",err)
        cache_result = None
    
    if(cache_result is not None):
        result = json.loads(cache_result)
    else:
        graph, document = cypherNeo4j.authenticate_and_load_json(comp)
        result = cypherNeo4j.generate_graph(graph,document,tab,comp,subcomp)
        cache_result = json.dumps(result)
  
        try:
            redis_db.set(redis_key,cache_result)
        except Exception as err:
            print("Can't Write To Redis:",err)

    visual = visdcc.Network(id='net',
             options = dict(height= '600px',
             width= '100%',
             physics={'solver':'forceAtlas2Based','stabilization':{'enabled':True,'fit':True},'adaptiveTimestep':True},
             nodes={'shape':'dot','size':20,'font':{'size': 14}},
             edges={'font':{'size':12,'align':'middle'},
             'color':'gray','arrows':{'to':{'enabled':True,'scaleFactor':0.5}},
             'smooth':{'enabled':True}},
             groups={
'Component':{'color':{'border':"#2e4ba0",'background':"#4169e1",'highlight':{'border':"#1138af",'background':"#1a4adb"}}},
'SubComponent':{'color':{'border':"#299b33",'background':"#34c140",'highlight':{'border':"#0a8715",'background':"#10bc1f"}}},
'ComponentDependency':{'color':{'border':"#692589",'background':"#9a34c9",'highlight':{'border':"#670e91",'background':"#8911c1"}}},
'SubComponentDependency':{'color':{'border':"#34a385",'background':"#42cea9",'highlight':{'border':"#0d9973",'background':"#17c697"}}}
             },
             layout={'improvedLayout':True},
             ),
             data=result
             )
    return visual


#########################
# Dashboard Layout / View
#########################

# Set up Dashboard and create layout

app = dash.Dash(__name__)

server = app.server

app.title = 'Dependency Graph'
app.config['suppress_callback_exceptions']=True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app.layout = html.Div([
     get_header(),
     get_tabs(),
     get_sample_visdcc(),
#    html.Img(src='/assets/neo4j_background3.gif'),
])

#############################################
# Interaction Between Components / Controller
#############################################


@app.callback(Output('tab-output', 'children'), 
              [Input('tabs', 'value')])
def display_content(tab):
    if tab == 'CompGraph':
        return display_comp()
    elif tab == 'CompDepGraph':
        return display_comp()
    elif tab == 'SubCompDepGraph':
        return display_comp_subcomp()
    elif tab == 'CompCompDepGraph':
        return display_comp()
    else:
        return None


@app.callback(
    Output(component_id='subcomponent-selector', component_property='options'),
    [Input(component_id='component-selector', component_property='value')]
)
def populate_subcomponent_selector(comp):
    subcomp = (
        [{'label': subcomp, 'value': subcomp}
         for subcomp in get_subComps(comp)]
    )
    return subcomp


@app.callback(
    Output(component_id='graph-data-subcomp', component_property='children'),
    [Input(component_id='component-selector', component_property='value'),
     Input(component_id='subcomponent-selector', component_property='value')],
    [State('tabs', 'value')]
)
def load_graph_subcomp(comp,subcomp,tab):
    if(comp is not None and subcomp is not None):
        result = get_graph(comp,tab,subcomp)
        return result
        

@app.callback(
    Output(component_id='graph-data-comp', component_property='children'),
    [Input(component_id='component-selector', component_property='value')],
    [State('tabs', 'value')]
)
def load_graph_comp(comp,tab):
    if(comp is not None):
        result = get_graph(comp,tab)
        return result


@server.route('/update')
def update():
    comps = updateYamls()
    if(comps):
        expireCache(redis_db,comps)
        return redirect("http://dependency-graph.ops.snapdeal.io", code=302)
    else:
        return redirect("http://dependency-graph.ops.snapdeal.io", code=302)


# start Flask server
if __name__ == '__main__':
    app.run_server(debug=False)
