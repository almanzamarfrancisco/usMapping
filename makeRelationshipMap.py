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
    return {'USs': web_USs, 'releases': releases, 'features': features, 'epics': epics}


def searchReleaseById(releases, id):
    for r in releases:
        if r['ReleaseId'] == id:
            # print(f"Release: {r['ReleaseId']}")
            return r
    raise ValueError("We didn't find that release id")


def searchFeatureById(features, id):
    for f in features:
        if f['Id'] == id:
            # print(f"Feature: {f['Id']} - {f['Title']}")
            return f
    raise ValueError("We didn't find that feature id")


def writeDependenciesFile(uss, releases, features):
    releases_involved = []
    features_involved = []
    with open("./transitionFiles/UserStoriesRelationships.md", "w+") as relationshipfile:
        text = ''
        correct_us = []
        for us in uss:
            dependencies_index = re.search(
                "# DEPENDENCIAS", us["Description"], re.IGNORECASE)
            if bool(dependencies_index):
                # If there is not any release with that id, we add it
                if not any(ri['ReleaseId'] == us['ReleaseId'] for ri in releases_involved):
                    releases_involved.append(
                        searchReleaseById(releases, us['ReleaseId']))
                correct_us.append(us)
        for ri in releases_involved:
            # If there is not any release with that id, we add it
            if not any(fi['Id'] == ri['ReleaseId'] for fi in features_involved):
                features_involved.append(
                    searchFeatureById(features, ri['TaskId']))
            for us in correct_us:
                dependencies_index = re.search(
                    "# DEPENDENCIAS", us["Description"], re.IGNORECASE)
                if bool(dependencies_index):
                    s = f"{us['Description'][dependencies_index.start():]}"
                    s = s.replace('# DEPENDENCIAS', ' ')
                    s = s.replace('\n', '\n\t\t\t- ')
                    text = text + f"\n\t\t- {us['Title']} {s}"
        print(text)
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


if __name__ == '__main__':
    userStoriesGotten, releases, features, epics = getUserStoriesFromAPI().values()
    USs, error_USs = checkSyntaxAndGetCleanList(userStoriesGotten).values()
    writeDependenciesFile(USs, releases, features)
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
