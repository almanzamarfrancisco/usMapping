from bs4 import BeautifulSoup
import pandas as pd
import graphviz
import textwrap
import re
# import io
import json
import requests


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
    #     print(json.dumps(us["Title"], indent=" "))
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


def writeDependenciesFile(uss, releases, features):
    added_releases = []
    added_features = []
    with open("./finalFiles/UserStoriesRelationships.md", "w+") as relationshipfile:
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


# Syntaxis checked in this order Title, Description, Aceptance criteria, Dependencies
def checkSyntaxAndGetCleanList(USs: list):
    title_syntax = r"HU([\d]{3}|XXX) *- * [^\*\n]*"
    description_syntax = r"# Descripci(o|ó)n:? ?\n"
    aceptance_criteria_syntax = r"# Criterios de Aceptaci(o|ó)n:\n"
    dependencies_syntax = r"# Dependencias:\n"
    syntax_title_error = []
    syntax_description_error = []
    syntax_aceptance_criteria_error = []
    syntax_dependencies_error = []
    correct_USs = []
    for us in USs:
        if not re.finditer(title_syntax, us['Title']):
            syntax_title_error.append(us)
        elif not re.finditer(description_syntax, us['Description'], re.IGNORECASE):
            syntax_description_error.append(us)
        elif not re.finditer(aceptance_criteria_syntax, us['Description'], re.IGNORECASE):
            syntax_aceptance_criteria_error.append(us)
        elif not re.finditer(dependencies_syntax, us['Description'], re.IGNORECASE):
            syntax_dependencies_error.append(us)
        else:
            correct_USs.append(us)
            # print(us['Description'])
    return {
        'USs': correct_USs,
        'syntaxError': {
            'title': syntax_title_error,
            'description': syntax_description_error,
            'aceptance_criteria': syntax_aceptance_criteria_error,
            'dependencies': syntax_dependencies_error,
        }}


def getDiagramStructure(process_names, USs, annotations, proccess_label: str) -> dict:
    result = {}
    result[proccess_label] = {}
    for i, process_name in enumerate(process_names):
        result[proccess_label][process_name] = []
        for j, us in enumerate(USs):
            us_annotation_ids = [usa['AnnotationId']
                                 for usa in us['CardAnnotations']]
            for us_a_id in us_annotation_ids:
                annotation_found = searchAnnotationById(
                    annotations, us_a_id)
                if annotation_found['Name'] == process_name:
                    result[proccess_label][process_name].append(
                        {'title': us['Title'], 'id': us['Id']})
    return result


def writeProcessDotDiagram(dot, USs, annotations, process_names, process_label: str):
    us_detail_url = "https://vectorcb.storiesonboard.com/storymapcard/contratos-vector-to-be"
    title = graphviz.Graph(name=process_label)
    # Get diagram Structure
    diagram_structure = getDiagramStructure(
        process_names, USs, annotations, process_label)
    with dot.subgraph(name=f"cluster_{process_label}") as title:
        title.attr(label=process_label, style="rounded", rankdir='TB')
        for i, process_name in enumerate(process_names):
            title.node(f"{process_label}_PROC_{i}", process_name, shape='cds')
            for j, us in enumerate(diagram_structure[process_label][process_name]):
                title.node(us['title'][:6], us['title'][:6], shape='note',
                           href=f"{us_detail_url}/{us['id']}")
                if j > 0:
                    title.edge(
                        diagram_structure[process_label][process_name][j-1]['title'][:6], us['title'][:6], constraint='true')
            if len(diagram_structure[process_label][process_name]):
                title.edge(
                    f'{process_label}_PROC_{i}', diagram_structure[process_label][process_name][0]['title'][:6], constraint='true')
            if i > 0:
                title.edge(f'{process_label}_PROC_{i-1}',
                           f'{process_label}_PROC_{i}', constraint='false')


def generateDotDiagram(USs, annotations, proccess_list: list[dict]):
    print(f"[I] Getting diagram structure...")
    print(f"[I] Making graphviz code...")

    dot = graphviz.Digraph('G', comment='US Process model relationships')
    dot.graph_attr['rankdir'] = 'TB'
    for pl in proccess_list:
        writeProcessDotDiagram(dot, USs, annotations,
                               pl['list'], pl['label'])
    dot.view(filename='ProccessDiagram.dot',
             directory='./finalFiles', cleanup=True, quiet=False)
    with open("./finalFiles/ProccessDiagram.dot", "w+") as diagram_file:
        diagram_file.write(dot.source)
    print(f"Done!")


if __name__ == '__main__':
    process1_names = [  # Prospect registration
        "Solicitud de contrato",
        "Creación de prospecto",
        "Selección de tipo de contrato",
        "Registro de segmento de info",
        "Alta documentación ",
        "Registro de información ",
        "Envío a PLD / Contratos",
    ]
    process2_names = [  # Information validation
        "Recepción de prospecto",
        "Validación de prospecto",
        "Aceptación de prospecto",
        "Validación PLD (LN y M)",
        "Prospecto Aceptado",
        "Generación de Contrato",
        "Envío de Contrato para Firma",
    ]
    process3_names = [  # Signature, activation and digitalizace
        "Recepción de Contrato Firmado",
        "Activación de Contrato",
        "Digitalización de Contrato",
    ]
    process4_names = [  # Contract modification
        "Tipo de Modificación",
        "Modificación",
        "Digitalización",
    ]
    print(f"[I] Obtaining StoryMap from API...")
    userStoriesGotten, releases, features, epics, annotations = getUserStoriesFromAPI().values()
    print(f"[I] Done!")
    print(f"[I] Checking syntax...")
    USs, error_USs = checkSyntaxAndGetCleanList(userStoriesGotten).values()
    print(f"[I] Done!")
    writeDependenciesFile(USs, releases, features)
    generateDotDiagram(USs, annotations, [
        {'label': 'Alta de prospecto', 'list': process1_names},
        {'label': 'Validación de información', 'list': process2_names},
        {'label': 'Firma, activación y digitalización', 'list': process3_names},
        {'label': 'Modificación de contrato', 'list': process4_names},
    ])
