from bs4 import BeautifulSoup
import pandas as pd
import graphviz
import textwrap
import re
# import io
import json
import requests


# https://vectorcb.storiesonboard.com/storymapcard/contratos-vector-to-be/<USId>

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


def writeProcessDotDiagram(USs, annotations):
    process_names = [
        "Solicitud de contrato",
        "Creación de prospecto",
        "Selección de tipo de contrato",
        "Registro de segmento de info",
        "Alta documentación ",
        "Registro de información ",
        "Envío a PLD / Contratos",
        "Alta de prospecto",
        "Alta de persona",
        "anexo de servicios de internet",
        "digitalización de documentos",
        "documentación de alta de prospecto",
        "documentos de alta de contrato",
        "modificación de cliente/contrato",
        "Registro de segmentos",
        "selección de tipo de contrato",
        "Tarjeta de internet",
        "validación de PLD",
        "Validación de prospecto"
    ]
    diagram_structure = {}
    print(f"[I] Making graphviz code...")
    dot = graphviz.Digraph('G', comment='US Process model relationships')
    dot.graph_attr['rankdir'] = 'TB'

    title = graphviz.Graph(name='t1')
    diagram_structure['t1'] = {}
    for i, process_name in enumerate(process_names):
        diagram_structure["t1"][process_name] = []
        print(f"=> Process Name {process_name}")
        for j, us in enumerate(USs):
            if j > 29 and j < 40:
                us_annotation_ids = [usa['AnnotationId']
                                     for usa in us['CardAnnotations']]
                print(
                    f"\tUS annotations {us['Title'][:6]}: {us_annotation_ids}")
                for us_a_id in us_annotation_ids:
                    annotation_found = searchAnnotationById(
                        annotations, us_a_id)
                    print(
                        f"\t\t\tSentence: {annotation_found['Name']} is in {process_name}: {annotation_found['Name'] in process_names}")
                    if annotation_found['Name'] == process_name:
                        print(
                            f"\t\t\t\t=> Annotation found {annotation_found['Id']} - {annotation_found['Name']}")
                        diagram_structure['t1'][process_name].append(
                            us['Title'])
                    else:
                        continue
    with open(f"./diagram_structure.json", "w+") as dsf:
        dsf.write(json.dumps(diagram_structure,
                  indent=" ", ensure_ascii=False))
    # with dot.subgraph(name="cluster t1") as title:
    #     title.attr(label='Title 1', style="rounded")
    #     for i, process_name in enumerate(process_names):
    #         title.node(f"PROC_{i}", process_name, shape='cds')
    #         for j, us in enumerate(diagram_structure['t1'][process_name]):
    #             title.node(us, us, shape='note')
    #             print(f"PROC_{i}\n\tNodo: {us[:6]} created:")
    #             if j > 0:
    #                 title.edge(
    #                     diagram_structure['t1'][process_name][j-1], us, constraint='true')
    #                 print(
    #                     f"\tArrow: {diagram_structure['t1'][process_name][j-1][:5]} -> {us[:5]}")
    #         title.edge(
    #             f'PROC_{i}', diagram_structure['t1'][process_name][0][:5], constraint='true')
    #         print(
    #             f"=> Arrow Proccedure PROC_{i} => {diagram_structure['t1'][process_name][0][:5]}")
        # print(json.dumps(f"{diagram_structure['t1']}",
        #       indent="   ", ensure_ascii=False))
    # print(dot.source)

    with open("./finalFiles/ProccessDiagram.dot", "w+") as diagram_file:
        diagram_file.write(dot.source)
    print(f"Done!")


if __name__ == '__main__':
    userStoriesGotten, releases, features, epics, annotations = getUserStoriesFromAPI().values()
    USs, error_USs = checkSyntaxAndGetCleanList(userStoriesGotten).values()
    # writeDependenciesFile(USs, releases, features)
    # writeProcessDotDiagram()
    writeProcessDotDiagram(USs, annotations)
