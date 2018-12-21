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
from scripts.getUpdatedYaml import updateYamls, setUpAllYamls
from scripts.redisCache import expireCache
from flask import redirect, request
from scripts.time_tracker import TimeTracker
import logging
from pandas import DataFrame, Series
from scripts.allInfraInNeo4j import dumpAllYamlsNeo4j


logfile = "/var/log/dependency-graph/dependency-graph.log"
logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s  [%(levelname)s]  %(message)s')


time_tracker = TimeTracker()

redis_db = redis.StrictRedis(host="localhost", charset="utf-8", port=6379, db=0, decode_responses=True)

neo4j_host = "localhost"
#neo4j_http_port = 7474
#neo4j_bolt_port = 7687
neo4j_user = ""
neo4j_pass = ""


###########################
# Data Manipulation / Model
###########################


def get_header():
        # Page Header
    header = html.Div([
        html.H4('Snapdeal Infra Dependency Graph',style={'textAlign': 'center'})
    ])
    return header

def get_tabs():
    get_tabs = html.Div([
        dcc.Tabs(id="tabs", value='CompGraph', children=[
                dcc.Tab(label='Comp Graph', value='CompGraph'),
                dcc.Tab(label='Comp Dependency', value='CompDepGraph'),
                dcc.Tab(label='SubComp Dependency', value='SubCompDepGraph'),
                dcc.Tab(label='Comp Comp Dependency', value='CompCompDepGraph'),
                dcc.Tab(label='ConnectsTo Comp', value='ConnToComp'),
                dcc.Tab(label='ConnectsTo SubComp', value='ConnToSubComp'),
                dcc.Tab(label='Graph Data', value='DepTable'),
            ]),
        html.Div(id='tab-output')
        ])
    return get_tabs

def get_comps():
    comps = []
    '''Returns the list of component names'''
    if(os.path.exists('services/components')) is True:
        comps = [os.path.basename(f).split('.')[0] for f in glob.glob("services/components/*.yml")]
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


#@time_tracker.time_track()
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
        if(tab == 'ConnToComp' or tab == 'ConnToSubComp'):
            neo4j_http_port = 8474
            neo4j_bolt_port = 8687
            graph = cypherNeo4j.authenticate(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass)
            document = convertYamlTojson(comp)
        else:
            neo4j_http_port = 7474
            neo4j_bolt_port = 7687
            graph = cypherNeo4j.authenticate(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass)
            document = convertYamlTojson(comp)
            

        result = cypherNeo4j.generate_graph(graph,document,tab,comp,subcomp)
        cache_result = json.dumps(result)

        NoneType = type(None)
            
        if(not isinstance(result, NoneType)):
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


def graph_data():
    display_graph_data = html.Div([
        html.Div(radio_button(),className="row",style={'textAlign': 'center'}),
            html.Div(
                html.Table(id='output-radio-value',style={'margin': '0 auto','width': '100%'}),
                className='twelve columns'),
        ])
    return display_graph_data

def radio_button():
    get_radio_button = html.Div([
         html.Br(),
         dcc.RadioItems(id='radio-value',
         options=[
            {'label': 'Component (Common Dependecy)', 'value': 'commDepcomp'},
            {'label': 'SubComponent (Common Dependency)', 'value': 'commDepsubcomp'},
            {'label': 'Circular Dependency', 'value': 'cirDepsubcomp'},
            {'label': 'StandAlone SubComponents', 'value': 'stndAlonesubcomp'},
         ],
         value='commDepsubcomp',
         labelStyle={'margin': '0px 20px','display': 'inline-block'}
         )
         ])
    return get_radio_button

def generate_table(dataframe,value):

    '''Given dataframe, return template generated using Dash components'''
    if(dataframe.size == 0):
        return no_results()
    else:
        num = dataframe.shape[0]
        s_no = list(range(1, num+1))
        dataframe.insert(loc=0, column='S.No.', value=s_no)

        columnsNames = list(dataframe.columns.values)


        if(value == 'commDepcomp'):
            columnsTitles = ['S.No.','Components','Dependent_Components']
            dataframe = dataframe.reindex(columns=columnsTitles)
            dataframe.rename(columns={'S.No.':'S.No.', 'Components':'Components', 'Dependent_Components':'Component Dependency'}, inplace=True)
        elif(value == 'commDepsubcomp'):
            columnsTitles = ['S.No.','SubComponents','Dependent_SubComponents']
            dataframe = dataframe.reindex(columns=columnsTitles)
            dataframe.rename(columns={'S.No.':'S.No.', 'SubComponents':'SubComponents', 'Dependent_SubComponents':'SubComponent Dependency'}, inplace=True)
        elif(value == 'cirDepsubcomp'):
            columnsTitles = ['S.No.','Components','SubComponents']
            dataframe = dataframe.reindex(columns=columnsTitles)
            #dataframe.rename(columns={'S.No.':'S.No.', 'Components':'Components', 'SubComponents':'SubComponents'}, inplace=True)
        elif(value == 'stndAlonesubcomp'):
            columnsTitles = ['S.No.','Components','SubComponents']
            dataframe = dataframe.reindex(columns=columnsTitles)
            #dataframe.rename(columns={'S.No.':'S.No.', 'Components':'Components', 'SubComponents':'SubComponents'}, inplace=True)
        else:
            return None
        '''
        if('SubComponents' in columnsNames):
            columnsTitles = ['S.No.','SubComponents','Dependent_SubComponents']
            dataframe = dataframe.reindex(columns=columnsTitles)
            dataframe.rename(columns={'S.No.':'S.No.', 'SubComponents':'SubComponents', 'Dependent_SubComponents':'SubComponent Dependency'}, inplace=True)
        else:
            columnsTitles = ['S.No.','Components','Dependent_Components']
            dataframe = dataframe.reindex(columns=columnsTitles)
            dataframe.rename(columns={'S.No.':'S.No.', 'Components':'Components', 'Dependent_Components':'Component Dependency'}, inplace=True)
        '''
       
        rows = []
        for i in range(len(dataframe)):
            row = []
            for col in dataframe.columns:
                value = dataframe.iloc[i][col]
                new_value = str(value)
                cell = html.Td(children=new_value)
                row.append(cell)
            rows.append(html.Tr(row))

        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in dataframe.columns])] + rows,className='responstable'
            )

def no_results():
        # Page Header
    result = html.Div([
        html.Br(),
        html.Br(),
        html.H4('No Results Found',style={'textAlign': 'center'})
    ])
    return result


#########################
# Dashboard Layout / View
#########################

# Set up Dashboard and create layout

app = dash.Dash(__name__)

server = app.server

app.title = 'Dependency Graph'
app.config['suppress_callback_exceptions']=True
#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True

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
    elif tab == 'ConnToComp':
        return display_comp()
    elif tab == 'ConnToSubComp':
        return display_comp_subcomp()
    elif tab == 'DepTable':
        return graph_data()
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


#Groupping Common Dependency
@app.callback(
    dash.dependencies.Output('output-radio-value', 'children'),
    [dash.dependencies.Input('radio-value', 'value')])
def comp_subcomp_dep_table(value):
    neo4j_http_port = 8474
    neo4j_bolt_port = 8687
    graph = cypherNeo4j.authenticate(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass)
    result,rvalue = cypherNeo4j.get_graph_data(graph,value)
    return generate_table(result,rvalue)


@server.route('/update')
def update():
    url = request.url
    new_url = url.replace('/update','')
    updated_comps = updateYamls()
    if(updated_comps):
        try:
            updated_comps.extend(['ConnToComp','ConnToSubComp'])
            expireCache(redis_db,updated_comps)
            dumpAllYamlsNeo4j()
            return redirect(new_url, code=302)
        except Exception as err:
            return redirect(new_url, code=302)
    else:
        return redirect(new_url, code=302)


@server.route('/initialsetup')
def setup():
    url = request.url
    new_url = url.replace('/initialsetup','')
    try:
        setUpAllYamls()
        dumpAllYamlsNeo4j()
        return redirect(new_url, code=302)
    except Exception as err:
        return redirect(new_url, code=302)

# start Flask server
if __name__ == '__main__':
    app.run_server(debug=False)
