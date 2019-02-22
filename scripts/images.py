import requests

data = {
"default" : "https://cdn1.iconfinder.com/data/icons/universal-mobile-line-icons-vol-3/48/130-512.png",
"aerospike" : "https://d1q6f0aelx0por.cloudfront.net/product-logos/c59ad037-0e53-4b0d-bee5-766397f3b40e-949b9260-e34e-4964-ba74-bfbd18607b71-ac72c493-71fb-44fb-89ac-f296cd8cef43-logo-large.png",
"aerospikecache" : "https://d1q6f0aelx0por.cloudfront.net/product-logos/c59ad037-0e53-4b0d-bee5-766397f3b40e-949b9260-e34e-4964-ba74-bfbd18607b71-ac72c493-71fb-44fb-89ac-f296cd8cef43-logo-large.png",
"activemq" : "https://www.signalfx.com/wp-content/uploads/integrations_activemq@4x-500x500.png",
"apache" : "https://www.signalfx.com/wp-content/uploads/integrations_apache@4x-500x500.png",
"cassandra" : "https://www.signalfx.com/wp-content/uploads/integrations_cassandra@4x-500x500.png",
"elasticsearch" : "https://www.signalfx.com/wp-content/uploads/integrations_elasticsearch-500x500.png",
"kafka" : "https://www.signalfx.com/wp-content/uploads/integrations_kafka@4x-500x500.png",
"kong" : "https://www.signalfx.com/wp-content/uploads/2018/09/Webp.net-resizeimage-500x500.png",
"mongodb" : "https://www.signalfx.com/wp-content/uploads/integrations_mongodb@4x-500x500.png",
"mysql" : "https://www.signalfx.com/wp-content/uploads/integrations_mysql@4x-500x500.png",
"nginx" : "https://www.signalfx.com/wp-content/uploads/integrations_nginx@4x-500x500.png",
"nodejs" : "https://www.signalfx.com/wp-content/uploads/2016/03/integrations_nodejs@4x-500x500.png",
"rabbitmq" : "https://www.signalfx.com/wp-content/uploads/integrations_rabbitmq@4x-500x500.png",
"redis" : "https://www.signalfx.com/wp-content/uploads/integrations_redis@4x-500x500.png",
"riak" : "https://www.signalfx.com/wp-content/uploads/2016/03/integrations_riak@4x-500x500.png",
"ruby" : "https://www.signalfx.com/wp-content/uploads/2016/03/integrations_ruby@4x-500x500.png",
"zookeeper" : "https://www.signalfx.com/wp-content/uploads/integrations_zookeeper@4x-500x500.png",
"ftp" : "http://caninechronicle.com/wp-content/uploads/2012/09/FTP-icon.jpg",
"hadoop" : "http://iconinc.in/wp-content/uploads/2017/08/hadoop-history-270x283.png",
"hdfs" : "http://iconinc.in/wp-content/uploads/2017/08/hadoop-history-270x283.png",
"hbase" : "https://i0.wp.com/techmango.org/wp-content/uploads/2017/07/hbase-icon.jpg",
"tomcat" : "https://raw.githubusercontent.com/docker-library/docs/8e31eb93a02d504d0cfe1da435aa31b377fc627d/tomcat/logo.png",
"jetty" : "https://raw.githubusercontent.com/docker-library/docs/c14d620ba7dbd254b6a44f753ee1ba4e700906f0/jetty/logo.png",
"jar" : "https://media-market.edmodo.com/media/public/e0dd66f726194a1feb7350ae91e011d7ec811599.png",
"kibana" : "https://cdn.iconscout.com/icon/free/png-256/elastic-1-283281.png",
"lighttpd" : "https://www.thingy-ma-jig.co.uk/sites/thingy-ma-jig.co.uk/files/styles/medium/public/field_image_files/light_logo_0.png",
"php" : "https://en.wikipedia.org/wiki/PHP#/media/File:PHP-logo.svg",
"python" : "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png",
"s3" : "https://martechforum.com/wp-content/uploads/2015/08/Amazon-S3-300x300.png",
"solr" : "http://lucene.apache.org/solr/assets/identity/Solr_Logo_on_white.png",
"spark" : "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Apache_Spark_logo.svg/2000px-Apache_Spark_logo.svg.png",
"storm" : "https://raw.githubusercontent.com/docker-library/docs/81d5cc2864be8fca7676abc044d974e8481d1d06/storm/logo.png",
"graphite" : "http://labs.criteo.com/wp-content/uploads/2017/01/Graphite.png",
"vertica" : "https://davewentzel.com/sites/default/files/vert.jpg",
"salesforce" : "https://www.salentica.com/wp-content/uploads/2015/07/salesforce-icon.png",
"mailserver" : "https://pbs.twimg.com/profile_images/646830789787697153/NKoHyhZZ.png",
"ldap" : "https://market.enonic.com/vendors/enonic/com.enonic.app.ldapidprovider/_/attachment/inline/f77bfb0b-5af6-4e68-b0e9-1bceff97e0fa:c1808c774597366f4296426039e3b963764a9e27/simpleid-icon-adapt.svg",
"cdn" : "https://botw-pd.s3.amazonaws.com/styles/logo-thumbnail/s3/042013/new_akamai_logo_cmyk_0.png",
"influxdb" : "https://d22e4d61ky6061.cloudfront.net/sites/default/files/Influxdb_logo_1.png"
}

for key in data.iterkeys():
    value = data.get(key)
    ext = value.split('.')[-1:][0]
    file_name = key+"."+ext
    with open(file_name, 'wb') as f:
        resp = requests.get(value, verify=False)
        f.write(resp.content)

