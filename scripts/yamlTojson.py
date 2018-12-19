import glob
import json
import yaml

def convertYamlTojson():
    yamls = [f for f in glob.glob("services/components/*.yml")]
    print yamls

    for yml in yamls:
        path = yml.split('.')[0]
        name = path+".json"
        print name
        fjson = open(name, 'w')
        with open(yml) as comp:
            fjson.write(json.dumps(yaml.load(comp), indent=4))
        fjson.close()


convertYamlTojson()

