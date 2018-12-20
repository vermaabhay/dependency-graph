import json
from urllib.request import Request, urlopen
import base64
import re
import os
from scripts.appProps import convertYamlTojson

base_url = 'http://gitlab.snapdeal.com'
api_url = '%s/api/v3' % base_url
token = ''
project_id = 1346
project_path = 'devtools/services'
path = 'components'
per_page = -1


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
            if(re.search(r'(^{0})'.format(comp_dep),diff_str) or re.search(r'(^{0})'.format(subcomp_dep),diff_str) or re.search(r'(^{0})'.format(name),diff_str)):
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
        url = "{0}/projects/{1}/repository/files?file_path={2}&ref=master".format(api_url,project_id,file_name)
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
        print("Updated following YAMLs:")
        print(files)
        comps = []
        for f in files:
            comp = f.split('/')[1].split('.')[0]
            comps.append(comp)
            convertYamlTojson(comp,convert=True)
        return comps
    else:
        return None


def setUpAllYamls():
    if(os.path.exists('services/components')) is False:
        os.makedirs('services/components')
        url = "{0}/projects/{1}/repository/tree?path={2}&per_page={3}".format(api_url,project_id,path,per_page)
        query = Request(url)
        query.add_header('PRIVATE-TOKEN', token)
        result = urlopen(query).read()
        result = json.loads(result)
        files = ["components/"+comp.get('name') for comp in result]
        for f in files:
            get_updated_file(f)
            comp = f.split('/')[1].split('.')[0]
            convertYamlTojson(comp,convert=True)
        get_diff_on_commit_ids()
        return True
    else:
        return None
