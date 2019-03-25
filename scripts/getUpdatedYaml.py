import json
import urllib
from urllib.request import Request, urlopen
import base64
import re
import os
import configparser
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from scripts.appProps import convertYamlTojson


confparser = configparser.RawConfigParser()
confparser.read('scripts/config.properties')


api_url = confparser.get('gitlab','api_url')
token = confparser.get('gitlab','token')
project_id = confparser.get('gitlab','project_id')
project = confparser.get('gitlab','project')
project_path = confparser.get('gitlab','project_path')


def get_last_commit_id():
    url = "{0}/projects/{1}/repository/commits".format(api_url,project_id)
    query = Request(url)
    query.add_header('PRIVATE-TOKEN', token)
    result = urlopen(query).read()
    result = json.loads(result)
    last_commit = sorted(result, key=lambda k: k['created_at'],reverse=True)[0]
    last_commit_id = last_commit.get('id')
    return last_commit_id


def get_diff_on_commit_ids():
    comp_dep = "component:"
    subcomp_dep = "subcomponent:"
    name = "name:"

    last_commit_id = get_last_commit_id()
   
    prev_commit_id_file = 'services/components/prev_commit_id.txt'

    if os.path.isfile(prev_commit_id_file):
        file_name = open(prev_commit_id_file,'r')
        prev_commit_id = file_name.read().strip()
        file_name.close()
    else:
        file_name = open(prev_commit_id_file,'w')
        file_name.write(last_commit_id)
        prev_commit_id = last_commit_id
        file_name.close()
        
    if(prev_commit_id != last_commit_id):
        url = "{0}/projects/{1}/repository/compare?from={2}&to={3}".format(api_url,project_id,prev_commit_id,last_commit_id)
        query = Request(url)
        query.add_header('PRIVATE-TOKEN', token)
        result = urlopen(query).read()
        result = json.loads(result)
        files = []
        diffs = result.get('diffs')
        for diff in diffs:
            diff_str_all = diff.get('diff')
            diff_str_match = re.findall('^[+-].*', diff_str_all, re.MULTILINE)
            diff_str = ''.join(diff_str_match)
            if(re.search(r'({0})'.format(comp_dep),diff_str) or re.search(r'({0})'.format(subcomp_dep),diff_str) or re.search(r'({0})'.format(name),diff_str)):
                files.append(diff.get('new_path'))
        for f in files:
            get_updated_file(f)

        file_name = open('services/components/prev_commit_id.txt','w')
        file_name.write(last_commit_id)
        file_name.close()
        return files
    else:
        return None
    

def get_updated_file(file_name):
        file_path = "services/"+file_name
        #url = "{0}/projects/{1}/repository/files?file_path={2}&ref=master".format(api_url,project_id,file_name)
        encoded_file_name = urllib.parse.quote_plus(file_name)
        url = "{0}/projects/{1}/repository/files/{2}?ref=master".format(api_url,project_id,encoded_file_name)
        query = Request(url)
        query.add_header('PRIVATE-TOKEN', token)
        result = urlopen(query).read()
        result = json.loads(result)
        content = result.get('content')
        content_str = base64.b64decode(content).decode('utf-8')
        new_file = open(file_path,'w')
        new_file.write(content_str)
        new_file.close()

def updateYamls():
    
    files = get_diff_on_commit_ids()
    if(files):
        print("Updating following YAMLs:")
        print(files)
        comps = list(map(lambda f:f.split('/')[1].split('.')[0], files))

	###### Partial Function : As Map In ProcessPoolExecutor Takes Single Argument Functions ######
        convertYamlTojsonPartial = partial(convertYamlTojson,convert=True)

        with ProcessPoolExecutor() as executor:
            executor.map(convertYamlTojsonPartial, comps)

        return comps
    else:
        print("No Dependencies Altered In Infra")
        return None


def setUpAllYamls():
    if(os.path.exists('services/components')) is False:
        os.makedirs('services/components')

        all_files = []
        counter = 1

        while(counter != 0):
            page = counter
            per_page = 100
            #url = "{0}/projects/{1}/repository/tree?path={2}&per_page={3}".format(api_url,project_id,project_path,per_page)
            url = "{0}/projects/{1}/repository/tree?path={2}&page={3}&per_page={4}".format(api_url,project_id,project_path,counter,per_page)
            query = Request(url)
            query.add_header('PRIVATE-TOKEN', token)
            result = urlopen(query).read()
            result = json.loads(result)
            files = ["components/"+comp.get('name') for comp in result]

            all_files.extend(files)
            
            if(len(files) < 100):
                counter = 0
            else:
                counter = counter + 1


        ###### Multi Threading ####### -> API Calls
        with ThreadPoolExecutor() as executor:
            executor.map(get_updated_file, all_files)

        ###### Multi Processing ###### -> CPU Intensive & I/O Bound
        all_comps = list(map(lambda f:f.split('/')[1].split('.')[0], all_files))
        with ProcessPoolExecutor() as executor:
            executor.map(convertYamlTojson, all_comps)


        get_diff_on_commit_ids()

        return True
    else:
        return None
