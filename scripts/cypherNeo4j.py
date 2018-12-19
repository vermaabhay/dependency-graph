import glob
import json
import yaml
from py2neo import Graph
import os.path
import datetime
from scripts.appProps import appImage
from scripts.appProps import appType
from scripts.appProps import convertYamlTojson
from pandas import DataFrame


def draw(graph, options, tab, comp, subcomp=None):

    if(subcomp is not None):
        var = comp+":"+subcomp
    else:
        var = comp

    query_7474 = """
    MATCH (n)
    WITH n, rand() AS random
    ORDER BY random
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n AS source_node,
           id(n) AS source_id,
           r,
           m AS target_node,
           id(m) AS target_id
    """

    query_8474_1 = """
    MATCH p=(n)-[r:ConnectsTo]->(m)
    WHERE m.name = {var} AND exists(n.name)
    WITH n, m, r, rand() AS random
    ORDER BY random
    RETURN n AS source_node,
           id(n) AS source_id,
           r,
           m AS target_node,
           id(m) AS target_id
    """
   
    query_8474 = """
    MATCH (m)
    WHERE m.name = {var}
    WITH m, rand() AS random
    ORDER BY random
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n AS source_node,
           id(n) AS source_id,
           r,
           m AS target_node,
           id(m) AS target_id
    """

    if(tab == 'ConnToComp' or tab == 'ConnToSubComp'):
        query = query_8474
    else:
        query = query_7474

    data = graph.run(query,var=var)

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
        print(row)
        print(source_node)
        print(source_id)
        print(rel)
        print(target_node)
        print(target_id)

        source_info = get_vis_info(source_node, source_id)

        if source_info not in nodes:
            nodes.append(source_info)

        if rel is not None:
            target_info = get_vis_info(target_node, target_id)

            if target_info not in nodes:
                nodes.append(target_info)
            
            edge_id = str(source_info["id"])+"-"+str(target_info["id"])
            edges.append({"id": edge_id, "from": source_info["id"], "to": target_info["id"], "label": rel.type()})
            print(rel.type())

    result = {'nodes':nodes,'edges':edges}
    #return result

    if not nodes:
        return None
    else:
        return result


def get_dependency_data(graph,value):

    query_comp = """
    MATCH (comp:Component)-[:ConnectsTo]->(depcomps:Component)
    WITH comp, depcomps ORDER BY depcomps.name
    WITH comp, COLLECT(depcomps.name) AS Dependent_Components, COUNT(depcomps) AS Dep_Count
    WITH comp ORDER BY comp.name, Dependent_Components, Dep_Count
    WITH COLLECT(comp.name) AS Components, Dependent_Components, Dep_Count
    WHERE SIZE(Components) > 1
    RETURN Components, Dependent_Components
    ORDER BY Dep_Count
    """
    query_subcomp = """
    MATCH (subcomp:SubComponent)-[:ConnectsTo]->(depsubcomps:SubComponent)
    WITH subcomp, depsubcomps ORDER BY depsubcomps.name
    WITH subcomp, COLLECT(depsubcomps.name) AS Dependent_SubComponents, COUNT(depsubcomps) AS Dep_Count
    WITH subcomp ORDER BY subcomp.name, Dependent_SubComponents, Dep_Count
    WITH COLLECT(subcomp.name) AS SubComponents, Dependent_SubComponents, Dep_Count
    WHERE SIZE(SubComponents) > 1
    RETURN SubComponents, Dependent_SubComponents
    ORDER BY Dep_Count
    """


    if(value == 'comp'):
        query = query_comp
    else:
        query = query_subcomp

    data =  graph.run(query)
    df = DataFrame(list(map(dict, data)))
    print(df)
    return df


def authenticate(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass):
    
    #authenticate("localhost:7474", "", "")
    #v3
    graph = Graph(bolt=False, host=neo4j_host, http_port=neo4j_http_port, bolt_port=neo4j_bolt_port, user=neo4j_user, password=neo4j_pass)
   
    if(neo4j_http_port == 7474):
        graph.delete_all()

    return graph


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
    MERGE (subcomp:SubComponent:Type {name: document.component+":"+subcomponent.name, type:subcomponent.type})
    MERGE (scd:SubComponent {name: dependency.component+":"+dependency.subcomponent})
    CREATE UNIQUE (subcomp)-[:ConnectsTo]->(scd)
    """

    query_subcomp_graph_fallback = """
    WITH {json} AS document
    UNWIND document.subcomponents AS subcomponent
    WITH document,subcomponent
    WHERE subcomponent.name = {subCompName}
    MERGE (subcomp:SubComponent:Type {name: document.component+":"+subcomponent.name, type:subcomponent.type})
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
    MERGE (subcomp:SubComponent:Type {name: document.component+":"+subcomponent.name, type:subcomponent.type})
    MERGE (scd:SubComponent {name: dependency.component+":"+dependency.subcomponent})
    CREATE UNIQUE (comp)-[:SubComponent]->(subcomp)
    CREATE UNIQUE (subcomp)-[:ConnectsTo]->(scd)
    WITH document,subcomponent,dependency
    WHERE document.component = dependency.component
    MERGE (cd:Component {name: dependency.component})
    MERGE (scd:SubComponent {name: dependency.component+":"+dependency.subcomponent})
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
    if(query != None):
        run = graph.run(query, json=doc, subCompName=subCompName, data=data)

    if(tab == 'SubCompDepGraph' and run.dump() is None):
        query = query_subcomp_graph_fallback
        graph.run(query, json=doc, subCompName=subCompName, data=data)
    ###########

    options = {"Component":"name","SubComponent":"name","ComponentDependency":"name","SubComponentDependency":"name","Type":"type"}
    #options = {"Component":"name","SubComponent":"name","Type":"type"}

    result = draw(graph,options,tab,compName,subCompName)
    return result

