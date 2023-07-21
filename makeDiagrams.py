from bs4 import BeautifulSoup
from unidecode import unidecode
import pandas as pd
import subprocess
import requests
import graphviz
import json
import re


def getServiceToken():
    with open("./inputFiles/headers.json", "r+") as headersfile:
        headers = json.load(headersfile)
    board_url = 'https://vectorcb.storiesonboard.com/m/contratos-vector-to-be'
    board_response = requests.get(board_url, headers=headers)
    soup = BeautifulSoup(board_response.text, 'html.parser')
    token = ''
    # Find csrf token from board
    for script in soup.findAll('script', type="text/javascript"):
        find_csrf = script.text.find("currentCsrfToken")
        if find_csrf != -1:
            token = script.text[find_csrf+19:find_csrf+55]
            print(token)
            break
    return token


# autopep8: off
# Structure:
    # {
    #     Activities: => User Stories board - Epic
    #     {
            # Tasks:{ => Features
                # TaskReleases: { => Releases (extra)
                    # Subtasks: { => User Stories
                    # }
                # }
            # }
    #     }
    # }
# autopep8: on
def getUserStoriesFromAPI():
    data_url = 'https://vectorcb.storiesonboard.com/api/q/storymapbyslugquery'
    data = {"QueryType": "StorymapBySlugQuery",
            "StoryMapSlug": "contratos-vector-to-be"}
    with open("./inputFiles/headers.json", "r+") as headersfile:
        headers = json.load(headersfile)
    # getServiceToken()
    story_map_response = requests.post(
        url=data_url, json=data, headers=headers)
    web_us_board = json.loads(story_map_response.text)
    annotations = web_us_board["StoryMap"]["Annotations"]
    epics = web_us_board["Activities"]
    features = []
    releases = []
    web_USs = []
    for epic in epics:
        features.extend(epic["Tasks"])
    for f in features:
        releases.extend(f["TaskReleases"])
    for release in releases:
        web_USs.extend(release["Subtasks"])
    # for us in web_USs:
    #     if us['Title'] == 'HU038 - Tipos de contratos para ambos mercados Bursátil y Divisas':
    #         print(json.dumps(us["Title"], indent=" "))
    return {'USs': web_USs, 'releases': releases, 'features': features, 'epics': epics, 'Annotations': annotations}


def searchReleaseById(releases, id):
    for r in releases:
        if r['ReleaseId'] == id:
            # print(f"Release: {r['ReleaseId']}")
            return r
    raise ValueError("We didn't find that release id")
    return []


def searchFeatureById(features, id):
    for f in features:
        if f['Id'] == id:
            # print(f"Feature: {f['Id']} - {f['Title']}")
            return f
    raise ValueError("We didn't find that feature id")
    return []


def searchAnnotationById(annotations, id):
    for a in annotations:
        if a['Id'] == id:
            return a
    raise ValueError("We didn't find that annotation id")
    return []


def getAnnotationNames(annotations, us_ids: list):
    names = []
    for a in annotations:
        for usid in us_ids:
            if a['Id'] == usid['AnnotationId']:
                names.append(a['Name'])
    return names


def writeDependenciesFile(uss, releases, features):
    added_releases = []
    added_features = []
    markdownfileroute = f"./finalFiles/UserStoriesRelationships.md"
    with open(markdownfileroute, "w+") as relationshipfile:
        text = ''
        s = ''
        for us in uss:
            dependencies_index = re.search(
                "# DEPENDENCIAS", us["Description"], re.IGNORECASE)
            if bool(dependencies_index):
                # SI no se han agregado
                r = searchReleaseById(releases, us["ReleaseId"])
                f = searchFeatureById(features, r["TaskId"])
                if not any(ri['ReleaseId'] == r['ReleaseId'] for ri in added_releases):
                    added_releases.append(r)
                    added_features.append(f)
                    text = text + f"\n- {f['Title']}\n"
                s = f"{us['Description'][dependencies_index.start():]}"
                s = s.replace('# DEPENDENCIAS', ' ')
                s = s.replace('\n', '\n\t\t- ')
                text = text + f"\n\t- {us['Title']} {s}"
        # print(text)
        # print(len(features_involved))
        relationshipfile.write(text)

        try:
            result = subprocess.run(
                f"markmap {markdownfileroute}", shell=True, check=True, text=True, capture_output=True)
            if result.stderr:
                print("Command error:")
                print(result.stderr)
            print("Return code:", result.returncode)
        except subprocess.CalledProcessError as e:
            print("Error executing command:", e)


# Syntaxis checked in this order Title, Description, Aceptance criteria, Dependencies
def checkSyntaxAndGetCleanList(USs: list):
    title_syntax = r"HU([\d]{3}) *- * [^\*\n]*"
    # title_syntax = r"HU([\d]{3}|XXX) *- * [^\*\n]*"
    description_syntax = r"# Descripci(o|ó)n:? ?\n"
    aceptance_criteria_syntax = r"# Criterios de Aceptaci(o|ó)n:? ?\n"
    dependencies_syntax = r"# Dependencias:\n"
    syntax_title_error = []
    syntax_description_error = []
    syntax_aceptance_criteria_error = []
    syntax_dependencies_error = []
    correct_USs = []
    for i, us in enumerate(USs):
        if not bool(re.match(title_syntax, us['Title'])):
            # print(us['Title'])
            syntax_title_error.append(us)
        # elif not bool(re.match(description_syntax, us['Description'], re.IGNORECASE)):
        #     syntax_description_error.append(us)
        # elif not bool(re.match(aceptance_criteria_syntax, us['Description'], re.IGNORECASE)):
        #     syntax_aceptance_criteria_error.append(us)
        # elif not bool(re.match(dependencies_syntax, us['Description'], re.IGNORECASE)):
            # syntax_dependencies_error.append(us)
        else:
            correct_USs.append(us)
    return {
        'USs': correct_USs,
        'syntaxError': {
            'title': syntax_title_error,
            'description': syntax_description_error,
            'aceptance_criteria': syntax_aceptance_criteria_error,
            'dependencies': syntax_dependencies_error,
        }}


def normString(text: str) -> str:
    if isinstance(text, str):
        return unidecode(text).casefold()
    else:
        return text


def getDiagramStructure(process_names, USs, annotations, proccess_label: str) -> dict:
    result = {}
    not_bind_uss = []
    result[proccess_label] = {}
    for i, process_name in enumerate(process_names):
        result[proccess_label][process_name] = []
        for j, us in enumerate(USs):
            us_annotation_ids = [usa['AnnotationId']
                                 for usa in us['CardAnnotations']]
            for us_a_id in us_annotation_ids:
                annotation_found = searchAnnotationById(annotations, us_a_id)
                if normString(annotation_found['Name']) == normString(process_name):
                    result[proccess_label][process_name].append(
                        {'title': us['Title'], 'id': us['Id'], 'annotations': getAnnotationNames(annotations, us['CardAnnotations'])})
                else:
                    not_bind_uss.append({'title': us['Title'], 'id': us['Id'], 'annotations': getAnnotationNames(
                        annotations, us['CardAnnotations'])})
    return {'structure': result, 'not_bind_uss': not_bind_uss}


def writeProcessDotDiagram(dot, USs, annotations, process_names, process_label: str):
    title = graphviz.Graph(name=process_label)
    # Get diagram Structure
    diagram_structure, rest_uss = getDiagramStructure(
        process_names, USs, annotations, process_label).values()
    with dot.subgraph(name=f"cluster_{process_label}") as title:
        title.attr(label=process_label, style="rounded", rankdir='TB')
        process_names.reverse()
        for i, process_name in enumerate(process_names):
            # title.node(f"{process_label}_PROC_{i}", process_name, shape='cds')
            approved_counter = 0
            not_approved_counter = 0
            for j, us in enumerate(diagram_structure[process_label][process_name]):
                if 'Aprobada por Cliente' in us['annotations']:
                    fillcolor = "#5cb85c"
                    approved_counter = approved_counter + 1
                else:
                    fillcolor = "#ff7063"
                    not_approved_counter = not_approved_counter + 1
                title.node(us['title'][:6], us['title'][:6],
                           shape='note', href=f"{us_detail_url}/{us['id']}", style="filled", color=fillcolor)
                if j > 0:
                    title.edge(diagram_structure[process_label][process_name]
                               [j-1]['title'][:6], us['title'][:6], constraint='true')
            title.node(
                f"{process_label}_PROC_{i}", f"{process_name} (√{approved_counter}|X{not_approved_counter})", shape='cds')
            if len(diagram_structure[process_label][process_name]):
                title.edge(f'{process_label}_PROC_{i}',
                           diagram_structure[process_label][process_name][0]['title'][:6], constraint='true')
            # if i > 0:
            #     title.edge(f'{process_label}_PROC_{i}',
            #                f'{process_label}_PROC_{i-1}', constraint='false')
    return rest_uss


def generateDotDiagram(USs, annotations, proccess_list: list[dict]):
    rest_uss = []
    print(f"[I] Getting diagram structure...")
    print(f"[I] Making graphviz code...")

    dot = graphviz.Digraph('G', comment='US Process model relationships')
    dot.graph_attr['rankdir'] = 'TB'
    for i, pl in enumerate(proccess_list):
        rus = writeProcessDotDiagram(
            dot, USs, annotations, pl['list'], pl['label'])
        for ru in rus:
            if not ru in rest_uss:
                rest_uss.append(ru)
    proccess_list.reverse()
    for i, pl in enumerate(proccess_list):
        if i < len(proccess_list)-1:
            # print(f"{pl['label']}_PROC_{len(pl['list'])-1} -> {proccess_list[i+1]['label']}_PROC_0")
            dot.edge(f"{proccess_list[i+1]['label']}_PROC_0",
                     f"{pl['label']}_PROC_{len(pl['list'])-1}", style='invis')

    dot.view(filename='ProccessDiagram.dot',
             directory='./finalFiles', cleanup=True, quiet=False)
    with open("./finalFiles/ProccessDiagram.dot", "w+") as diagram_file:
        diagram_file.write(dot.source)

    second_dot = graphviz.Digraph('H', comment='User Stories without process')
    with second_dot.subgraph(name=f"cluster_rest", graph_attr=dict(rankdir='LR', rank="max")) as rest:
        green = []
        red = []
        rest.attr(label='User Stories without process', style="rounded")
        rest.edge_attr['style'] = 'invis'
        for i, ru in enumerate(rest_uss):
            if 'Aprobada por Cliente' in ru['annotations']:
                fillcolor = "#5cb85c"
                green.append(ru)
            else:
                fillcolor = "#ff7063"
                red.append(ru)
            rest.node(ru['title'][:6], ru['title'][:6], shape='note',
                      href=f"{us_detail_url}/{ru['id']}", style="filled", color=fillcolor)
        for j, r in enumerate(red):
            if j < len(red)-1:
                rest.edge(red[j+1]['title'][:6], r['title'][:6])
        for k, g in enumerate(green):
            if k < len(green)-1:
                rest.edge(green[k+1]['title'][:6], g['title'][:6])
    second_dot.view(filename='USsWithoutProcess.dot',
                    directory='./finalFiles', cleanup=True, quiet=False)

    print(f"Done!")


us_detail_url = "https://vectorcb.storiesonboard.com/m/contratos-vector-to-be/!card"


def render(predefined_processes):
    print(f"[I] Obtaining StoryMap from API...")
    userStoriesGotten, releases, features, epics, annotations = getUserStoriesFromAPI().values()
    print(f"[I] Done!")
    print(f"[I] Checking syntax...")
    USs, error_USs = checkSyntaxAndGetCleanList(userStoriesGotten).values()
    print(f"[I] Done!")
    # writeDependenciesFile(USs, releases, features)
    generateDotDiagram(USs, annotations, predefined_processes)
