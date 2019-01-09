import glob
import os.path
import time
from py2neo import Graph
from scripts.appProps import convertYamlTojson
from scripts import cypherNeo4j


def dumpAllYamlsNeo4j(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass):

    graph = cypherNeo4j.authenticate(neo4j_host,neo4j_http_port,neo4j_bolt_port,neo4j_user,neo4j_pass)
    graph.delete_all()

    comps = [os.path.basename(f).split('.')[0] for f in glob.glob("services/components/*.yml")]

    error = []
    for comp in comps:
        if(comp != "nonengg"):
            document = convertYamlTojson(comp)

            query_subcomponent = """
            WITH {json} AS document
            UNWIND document.subcomponents AS subcomponent
            MERGE (comp:Component {name: document.component})
            MERGE (subcomp:SubComponent {name: document.component+":"+subcomponent.name})
            """
            #CREATE UNIQUE (comp)-[:SubComponent {name: "SubComponent"}]->(subcomp)

            query_dependency = """
            WITH {json} AS document
            UNWIND document.subcomponents AS subcomponent
            UNWIND subcomponent.dependencies AS dependency
            MERGE (comp:Component {name: document.component})
            MERGE (subcomp:SubComponent {name: document.component+":"+subcomponent.name})
            MERGE (cd:Component {name: dependency.component})
            MERGE (scd:SubComponent {name: dependency.component+":"+dependency.subcomponent})
            CREATE UNIQUE (comp)-[:ConnectsTo {name: "ConnectsTo"}]->(cd)
            CREATE UNIQUE (subcomp)-[:ConnectsTo {name: "ConnectsTo"}]->(scd)
            """
            #print(document)
            try:
                graph.run(query_subcomponent, json=document)
                graph.run(query_dependency, json=document)
            except Exception as err:
                error.append(comp)                
                print(err)
                
            #time.sleep(1)
    if(len(error) > 0):
        print("Following YAMLs Are Not Successfully Processed")
        print(error)        
    else:
        print("All YAMLs Successfully Processed")
