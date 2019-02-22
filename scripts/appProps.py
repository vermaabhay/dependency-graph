#!/usr/bin/python
import yaml
import glob
import json
import os

def convertYamlTojson(compName,convert=False):
    yaml_file = glob.glob("services/components/%s.yml" %compName)[0]
    path = yaml_file.split('.')[0]
    name = path+".json"
    if (os.path.isfile(name) and not convert):
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


def appType(vis_label):

    compName = vis_label.split(':')[0]
    subCompName = vis_label.split(':')[1]

    doc = convertYamlTojson(compName)
    subcomps = doc['subcomponents']

    for subcomp in subcomps:
        if(subcomp['name'] == subCompName):
            subcomp_type = subcomp['type']
            return subcomp_type


def appImage(app_type):
    image_dict = {
'default'       : '/assets/imgs/default.ico',
'nodejs'        : '/assets/imgs/nodejs.png', 
'redis'         : '/assets/imgs/redis.png', 
'cdn'           : '/assets/imgs/cdn.png', 
'zookeeper'     : '/assets/imgs/zookeeper.png', 
'kibana'        : '/assets/imgs/kibana.png', 
'kafka'         : '/assets/imgs/kafka.png', 
'mysql'         : '/assets/imgs/mysql.png', 
'hbase'         : '/assets/imgs/hbase.jpg', 
'mailserver'    : '/assets/imgs/mailserver.png', 
'cassandra'     : '/assets/imgs/cassandra.png', 
'ftp'           : '/assets/imgs/ftp.jpg', 
'php'           : '/assets/imgs/php.svg', 
's3'            : '/assets/imgs/s3.png', 
'solr'          : '/assets/imgs/solr.png', 
'jar'           : '/assets/imgs/jar.png', 
'jetty'         : '/assets/imgs/jetty.png', 
'vertica'       : '/assets/imgs/vertica.jpg', 
'storm'         : '/assets/imgs/storm.png', 
'ldap'          : '/assets/imgs/ldap.svg', 
'ruby'          : '/assets/imgs/ruby.png', 
'graphite'      : '/assets/imgs/graphite.png', 
'riak'          : '/assets/imgs/riak.png', 
'aerospikecache': '/assets/imgs/aerospike.png', 
'hdfs'          : '/assets/imgs/hdfs.png', 
'python'        : '/assets/imgs/python.png', 
'mongodb'       : '/assets/imgs/mongodb.png', 
'lighttpd'      : '/assets/imgs/lighttpd.png', 
'influxdb'      : '/assets/imgs/influxdb.png', 
'nginx'         : '/assets/imgs/nginx.png', 
'apache'        : '/assets/imgs/apache.png', 
'spark'         : '/assets/imgs/spark.png', 
'kong'          : '/assets/imgs/kong.png', 
'activemq'      : '/assets/imgs/activemq.png', 
'salesforce'    : '/assets/imgs/salesforce.png', 
'aerospike'     : '/assets/imgs/aerospike.png', 
'tomcat'        : '/assets/imgs/tomcat.png', 
'rabbitmq'      : '/assets/imgs/rabbitmq.png', 
'elasticsearch' : '/assets/imgs/elasticsearch.png', 
'hadoop'        : '/assets/imgs/hadoop.png', 
'apk'           : '/assets/imgs/apk.png', 
'chefserver'    : '/assets/imgs/chefserver.png', 
'consul'        : '/assets/imgs/consul.png', 
'docker'        : '/assets/imgs/docker.png', 
'ejabberd'      : '/assets/imgs/ejabberd.png', 
'external'      : '/assets/imgs/external.png', 
'gerrit'        : '/assets/imgs/gerrit.png', 
'jenkinsmaster' : '/assets/imgs/jenkins.png', 
'jenkinsslave'  : '/assets/imgs/jenkins.png', 
'jumpserver'    : '/assets/imgs/jumpserver.png', 
'loadbalancer'  : '/assets/imgs/loadbalancer.png', 
'memcache'      : '/assets/imgs/memcache.png', 
'nfs'           : '/assets/imgs/nfs.png', 
'orchestrator'  : '/assets/imgs/orchestrator.png', 
'ror'           : '/assets/imgs/ror.png', 
'saltmaster'    : '/assets/imgs/saltmaster.png', 
'services'      : '/assets/imgs/services.png', 
'staticfiles'   : '/assets/imgs/staticfiles.png', 
'superset'      : '/assets/imgs/superset.png', 
'tdagent'       : '/assets/imgs/tdagent.png', 
'telegraf'      : '/assets/imgs/telegraf.png', 
'vault'         : '/assets/imgs/vault.png'
}
    default = "https://cdn1.iconfinder.com/data/icons/universal-mobile-line-icons-vol-3/48/130-512.png"
    image_url = image_dict.get(app_type, default)
    return image_url



