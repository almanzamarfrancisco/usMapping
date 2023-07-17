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
    epics = web_us_board["Activities"]
    characteristics = []
    releases = []  # User Stories are separated on releases inside of characteristics
    web_USs = []
    for epic in epics:
        characteristics.extend(epic["Tasks"])
    for characteristic in characteristics:
        releases.extend(characteristic["TaskReleases"])
    for release in releases:
        web_USs.extend(release["Subtasks"])
    # for us in web_USs:
    #     print(json.dumps(us["Title"], indent=" "))
    return web_USs


def writeDependenciesFile(uss):
    with open("./transitionFiles/UserStoriesRelationships.md", "w+") as relationshipfile:
        text = ''
        for us in uss:
            i = re.search("# DEPENDENCIAS", us["Description"], re.IGNORECASE)
            if bool(i):
                s = f"{us['Description'][i.start():]}"
                s = s.replace('# DEPENDENCIAS', ' ')
                s = s.replace('\n', '\n\t- ')
                text = text + f"\n- {us['Title']} {s}"
        print(text)
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


if __name__ == '__main__':
    userStoriesGotten = getUserStoriesFromAPI()
    USs, error_USs = checkSyntaxAndGetCleanList(userStoriesGotten).values()
    writeDependenciesFile(USs)
    # userStories = searchUSIdsFromWebPage(trimmedUserStoriesString)
    # # print(json.dumps(userStories, indent='  ', ensure_ascii=False))

    # print(f"[I] Making graphviz code...")
    # dot = graphviz.Digraph('G', comment='US Process model relationships')
    # dot.graph_attr['rankdir'] = 'TB'
    # for i, us in enumerate(userStories):
    #     if len(us['title']) > 1:
    #         title_text = textwrap.indent(f"{us['title']}", '\\n')
    #         print(title_text)
    #         dot.node(f"US_{i}", title_text, shape='note')
    # # dot.edges(['US_0', 'US_18'])
    # print(dot.source)
    # with open("./diagram.dot", "w+") as diagram_file:
    #     diagram_file.write(dot.source)
    # print(f"Done!")
