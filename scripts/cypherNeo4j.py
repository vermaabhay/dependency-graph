import glob
import json
import yaml
from py2neo import Graph, authenticate
import os.path
import datetime
from scripts.appProps import appImage
from scripts.appProps import appType
from scripts.appProps import convertYamlTojson


def draw(graph, options, physics=False):
    # The options argument should be a dictionary of node labels and property keys; it determines which property
    # is displayed for the node label. For example, in the movie graph, options = {"Movie": "title", "Person": "name"}.
    # Omitting a node label from the options dict will leave the node unlabeled in the visualization.
    # Setting physics = True makes the nodes bounce around when you touch them!
    query = """
    MATCH (n)
    WITH n, rand() AS random
    ORDER BY random
    LIMIT {limit}
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n AS source_node,
           id(n) AS source_id,
           r,
           m AS target_node,
           id(m) AS target_id
    """

    data = graph.run(query,limit=1000)

    nodes = []
    edges = []


    def get_vis_info(node, id):
        node_labels = list(node.labels())
        if(len(node_labels) > 1):
            for node_label in node_labels:
                if(node_label == "SubComponent"):
                    group = node_label
                    prop_key = options.get(node_label)
                    vis_label = node.properties.get(prop_key, "")
                if(node_label == "Type"):
                    prop_key = options.get(node_label)
                    app_type = node.properties.get(prop_key, "")
                    image_url = appImage(app_type)
            return {"id": id, "label": vis_label, "group": group, "shape":"image", "image":image_url}
        else:
            node_label = list(node.labels())[0]
            prop_key = options.get(node_label)
            vis_label = node.properties.get(prop_key, "")
            if(node_label == "Component" or node_label == "ComponentDependency"):
                image_url = appImage('default')
            else:
                scdType = appType(vis_label)
                image_url = appImage(scdType)
            return {"id": id, "label": vis_label, "group": node_label, "shape":"image", "image":image_url}


    for row in data:
        source_node = row[0]
        source_id = row[1]
        rel = row[2]
        target_node = row[3]
        target_id = row[4]

        source_info = get_vis_info(source_node, source_id)

        if source_info not in nodes:
            nodes.append(source_info)

        if rel is not None:
            target_info = get_vis_info(target_node, target_id)

            if target_info not in nodes:
                nodes.append(target_info)
            
            edge_id = str(source_info["id"])+"-"+str(target_info["id"])
            edges.append({"id": edge_id, "from": source_info["id"], "to": target_info["id"], "label": rel.type()})

    result = {'nodes':nodes,'edges':edges}
    if not nodes:
        return None
    else:
        return result

def authenticate_and_load_json(compName):
    authenticate("localhost:7474", "", "")
    graph = Graph()
    graph.delete_all()

    '''
    yamls = [f for f in glob.glob("services/components/%s.yml" %compName)]
    
    for yml in yamls:
        path = yml.split('.')[0]
        name = path+".json"
        fjson = open(name, 'w')
        with open(yml) as comp:
            fjson.write(json.dumps(yaml.load(comp), indent=4))
        fjson.close()

    jsons = [f for f in glob.glob("services/components/%s.json" %compName)]

    for f in jsons:
        with open(f) as data_file:
            doc = json.load(data_file)
    '''
    doc = convertYamlTojson(compName)
    return graph,doc


def generate_graph(graph,doc,tab,compName,subCompName=None):
    ###########
    #    query_all = """ RETURN {json} """
    #    print graph.cypher.execute(query_all, json = doc)
    ###########
    query_comp = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    RETURN document.component, subcomponent.name
    """
    query_comp_graph = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    MERGE (comp:Component {name: document.component})
    MERGE (subcomp:SubComponent:Type {name: subcomponent.name, type:subcomponent.type})
    CREATE UNIQUE (comp)-[:SubComponent]->(subcomp)
    """

    query_subcomp = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    RETURN document.component, subcomponent.name
    """
    query_subcomp_graph = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    UNWIND subcomponent.dependencies AS dependency
    WITH document,subcomponent,dependency
    WHERE subcomponent.name = {subCompName}
    MERGE (subcomp:SubComponent:Type {name: subcomponent.name, type:subcomponent.type})
    MERGE (scd:SubComponentDependency {name: dependency.component+":"+dependency.subcomponent})
    CREATE UNIQUE (subcomp)-[:ConnectsTo]->(scd)
    """

    query_subcomp_graph_fallback = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    WITH subcomponent
    WHERE subcomponent.name = {subCompName}
    MERGE (subcomp:SubComponent:Type {name: subcomponent.name, type:subcomponent.type})
    """


    #match (comp:Component)
    #return comp
    #match (subcomps:SubComponents)
    #return subcomps
    #match (comp:Component)-[:SubComponent]->(subcomp:SubComponent)
    #return *

    query_comp_subcomp_dependency = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    UNWIND subcomponent.dependencies AS dependency
    RETURN document.component, subcomponent.name, dependency.component, dependency.subcomponent
    """

    query_comp_subcomp_dependency_graph = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    UNWIND subcomponent.dependencies AS dependency
    MERGE (comp:Component {name: document.component})
    MERGE (subcomp:SubComponent:Type {name: subcomponent.name, type:subcomponent.type})
    MERGE (scd:SubComponentDependency {name: dependency.component+":"+dependency.subcomponent})
    CREATE UNIQUE (comp)-[:SubComponent]->(subcomp)
    CREATE UNIQUE (subcomp)-[:ConnectsTo]->(scd)
    WITH document,subcomponent,dependency
    WHERE document.component = dependency.component
    MERGE (cd:Component {name: dependency.component})
    MERGE (scd:SubComponentDependency {name: dependency.component+":"+dependency.subcomponent})
    CREATE UNIQUE (cd)-[:SubComponent]->(scd)
    """

    query_comp_comp_dependency_graph = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    UNWIND subcomponent.dependencies AS dependency
    MERGE (comp:Component {name: document.component})
    MERGE (cd:ComponentDependency {name: dependency.component})
    CREATE UNIQUE (comp)-[:ConnectsTo]->(cd)
    """


    #graph.run(query_comp, json = doc).dump()
    #graph.run(query_comp_dependency, json = doc).dump()


    data = {'component': None, 'subcomponent': None}
   
    graph_query = {'CompGraph':query_comp_graph,
                   'CompDepGraph':query_comp_subcomp_dependency_graph,
                   'SubCompDepGraph':query_subcomp_graph,
                   'CompCompDepGraph':query_comp_comp_dependency_graph
                   }
    query = graph_query.get(tab)
    run = graph.run(query, json=doc, subCompName=subCompName, data=data)

    if(tab == 'SubCompDepGraph' and run.dump() is None):
        query = query_subcomp_graph_fallback
        graph.run(query, json=doc, subCompName=subCompName, data=data)
    ###########

    options = {"Component":"name","SubComponent":"name","ComponentDependency":"name","SubComponentDependency":"name","Type":"type"}
    #options = {"Component":"name","SubComponent":"name","Type":"type"}

    result = draw(graph,options,compName)
    return result

