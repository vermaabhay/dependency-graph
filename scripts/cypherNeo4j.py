import glob
import json
import yaml
from py2neo import Graph, authenticate
import os.path
import datetime


def appImage(app_type):
    image_dict = {'nodejs': '/assets/imgs/nodejs.png', 'redis': '/assets/imgs/redis.png', 'cdn': '/assets/imgs/cdn.png', 'zookeeper': '/assets/imgs/zookeeper.png', 'kibana': '/assets/imgs/kibana.png', 'kafka': '/assets/imgs/kafka.png', 'mysql': '/assets/imgs/mysql.png', 'hbase': '/assets/imgs/hbase.jpg', 'mailserver': '/assets/imgs/mailserver.png', 'cassandra': '/assets/imgs/cassandra.png', 'ftp': '/assets/imgs/ftp.jpg', 'php': '/assets/imgs/php.svg', 's3': '/assets/imgs/s3.png', 'solr': '/assets/imgs/solr.png', 'jar': '/assets/imgs/jar.png', 'jetty': '/assets/imgs/jetty.png', 'vertica': '/assets/imgs/vertica.jpg', 'storm': '/assets/imgs/storm.png', 'ldap': '/assets/imgs/ldap.svg', 'ruby': '/assets/imgs/ruby.png', 'graphite': '/assets/imgs/graphite.png', 'riak': '/assets/imgs/riak.png', 'aerospikecache': '/assets/imgs/aerospikecache.png', 'hdfs': '/assets/imgs/hdfs.png', 'python': '/assets/imgs/python.png', 'mongodb': '/assets/imgs/mongodb.png', 'lighttpd': '/assets/imgs/lighttpd.png', 'influxdb': '/assets/imgs/influxdb.png', 'nginx': '/assets/imgs/nginx.png', 'apache': '/assets/imgs/apache.png', 'spark': '/assets/imgs/spark.png', 'kong': '/assets/imgs/kong.png', 'activemq': '/assets/imgs/activemq.png', 'salesforce': '/assets/imgs/salesforce.png', 'aerospike': '/assets/imgs/aerospike.png', 'tomcat': '/assets/imgs/tomcat.png', 'default': '/assets/imgs/default.ico', 'rabbitmq': '/assets/imgs/rabbitmq.png', 'elasticsearch': '/assets/imgs/elasticsearch.png', 'hadoop': '/assets/imgs/hadoop.png', 'apk': '/assets/imgs/apk.png', 'chefserver': '/assets/imgs/chefserver.png', 'consul': '/assets/imgs/consul.png', 'docker': '/assets/imgs/docker.png', 'ejabberd': '/assets/imgs/ejabberd.png', 'external': '/assets/imgs/external.png', 'gerrit': '/assets/imgs/gerrit.png', 'jenkinsmaster': '/assets/imgs/jenkins.png', 'jenkinsslave': '/assets/imgs/jenkins.png', 'jumpserver': '/assets/imgs/jumpserver.png', 'loadbalancer': '/assets/imgs/loadbalancer.png', 'memcache': '/assets/imgs/memcache.png', 'nfs': '/assets/imgs/nfs.png', 'orchestrator': '/assets/imgs/orchestrator.png', 'ror': '/assets/imgs/ror.png', 'saltmaster': '/assets/imgs/saltmaster.png', 'services': '/assets/imgs/services.png', 'staticfiles': '/assets/imgs/staticfiles.png', 'superset': '/assets/imgs/superset.png', 'tdagent': '/assets/imgs/tdagent.png', 'telegraf': '/assets/imgs/telegraf.png', 'vault': '/assets/imgs/vault.png'
}
    default = "https://www.snapdeal.com/img/icons/finalFavicon.ico"
    image_url = image_dict.get(app_type, default)
    return image_url


def get_appType(vis_label):

    compName = vis_label.split(':')[0]
    subCompName = vis_label.split(':')[1]
  
    doc = convertYamlTojson(compName)
    subcomps = doc['subcomponents']
  
    for subcomp in subcomps:
        if(subcomp['name'] == subCompName):
            subcomp_type = subcomp['type']
            return subcomp_type


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
                scdType = get_appType(vis_label)
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
    return result

def convertYamlTojson(compName):
    yaml_file = glob.glob("services/components/%s.yml" %compName)[0]
    path = yaml_file.split('.')[0]
    name = path+".json"
    if os.path.isfile(name):
        json_file = glob.glob("services/components/%s.json" %compName)[0]
    else:
        fjson = open(name, 'w')
        with open(yaml_file) as comp:
            fjson.write(json.dumps(yaml.load(comp), indent=4))
        fjson.close()
        json_file = glob.glob("services/components/%s.json" %compName)[0]
 
    with open(json_file) as data_file:
        doc = json.load(data_file)

    return doc
    

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
    out = graph.run(query, json=doc, subCompName=subCompName)
   
    if(tab == 'SubCompDepGraph' and out.dump() is None):
        query = query_subcomp_graph_fallback
        out = graph.run(query, json=doc, subCompName=subCompName)


    ###########

    options = {"Component":"name","SubComponent":"name","ComponentDependency":"name","SubComponentDependency":"name","Type":"type"}
    #options = {"Component":"name","SubComponent":"name","Type":"type"}

    result = draw(graph,options,compName)
    return result

