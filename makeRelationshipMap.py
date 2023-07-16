# from bs4 import BeautifulSoup
import pandas as pd
import graphviz
import textwrap
import re
# import io
import json
import requests


# https://vectorcb.storiesonboard.com/storymapcard/contratos-vector-to-be/<USId>


def searchUSIdsFromWebPage():
    board_url = 'https://vectorcb.storiesonboard.com/m/contratos-vector-to-be'
    data_url = 'https://vectorcb.storiesonboard.com/api/q/storymapbyslugquery'
    data = {"QueryType": "StorymapBySlugQuery",
            "StoryMapSlug": "contratos-vector-to-be"}
    with open("./inputFiles/headers.json", "r+") as headersfile:
        headers = json.load(headersfile)
    # board_response = requests.get(board_url, headers=headers)
    # soup = BeautifulSoup(board_response.text, 'html.parser')
    # token = ''
    # Find csrf token from board
    # for script in soup.findAll('script', type="text/javascript"):
    #     find_csrf = script.text.find("currentCsrfToken")
    #     if find_csrf != -1:
    #         token = script.text[find_csrf+19:find_csrf+55]
    #         print(token)
    #         break
    story_map_response = requests.post(
        url=data_url, json=data, headers=headers)
    # print(json.dumps(story_map_response.text, indent="   "))
    web_us_board = json.loads(story_map_response.text)
    epics = web_us_board["Activities"]
    characteristics = []
    releases = []  # User Stories are separated on releases
    web_USs = []
    for epic in epics:
        characteristics.extend(epic["Tasks"])
    for characteristic in characteristics:
        releases.extend(characteristic["TaskReleases"])
    for release in releases:
        web_USs.extend(release["Subtasks"])
    for us in web_USs:
        print(json.dumps(us["Title"], indent=" "))


def checkSyntaxAndGetList(titles, content, labels_values):
    title_syntax = r"HU([\d]{3}|XXX) *- * [^\*\n]*"
    syntax_title_error = []
    description_found = ''
    aceptance_criteria_found = ''
    dependencies_found = ''
    correct_USs = []
    labels = []

    for i, title in enumerate(titles):
        try:
            # For listing bad syntax USs
            if not re.finditer(title_syntax, title, re.MULTILINE):
                syntax_title_error.append(title)
            else:  # TODO: Verify correctUSs structures, it is not prepared for dependencies and aceptance criteria
                if (content[i].find('CRITERIOS DE ACEPTACIÓN', re.IGNORECASE) != -1):
                    description_ending = content[i].find(
                        'CRITERIOS DE ACEPTACIÓN', re.IGNORECASE)
                    description_found = content[i][:description_ending]
                    aceptance_criteria_ending = content[i].find(
                        "# Dependencias", re.IGNORECASE)
                    if (aceptance_criteria_ending != -1):
                        print(
                            content[i][description_ending:aceptance_criteria_ending])
                        aceptance_criteria_found = content[i][description_ending:aceptance_criteria_ending]
                        dependencies_found = content[aceptance_criteria_ending:]
                    else:
                        aceptance_criteria_found = content[i][description_ending:]
                        dependencies_found = ''
                else:
                    description_found = ''
                if isinstance(labels_values[i], (str,)):
                    labels = labels_values[i].split('\n')
                else:
                    labels = []
                correct_USs.append(
                    {
                        'webid': '',
                        'id': title[:5],
                        'title': title[5:].replace(' - ', ''),
                        'description': description_found.replace('# Descripción', ''),
                        'aceptance_criteria': aceptance_criteria_found,
                        'dependencies': dependencies_found,
                        'labels': labels
                    })
        except TypeError as err:
            # print(f"Title: {title}, {err}")
            pass
        except AttributeError as err:
            # print(f"Title: {title}, {err}")
            pass
    # print(json.dumps(correct_USs, indent="  ", ensure_ascii=False))
    return {'USs': correct_USs, 'SyntaxErrorTitles': syntax_title_error}


def getUserStoriesFromExelFile(fileName: str):
    df = pd.ExcelFile(fileName)
    sheetX = df.parse(0)
    us_file_titles = sheetX['Subtask']
    us_description_file_column = sheetX['Subtask description']
    labels_values = sheetX['ThirdLevelAnnotations']
    USs, SyntaxErrorTitles = checkSyntaxAndGetList(
        us_file_titles, us_description_file_column, labels_values).values()
    # print(json.dumps(USs, indent="  ", ensure_ascii=False))
    # TODO: Do something with syntax Error Titles
    return USs


if __name__ == '__main__':
    exel_file_USs = getUserStoriesFromExelFile(
        "./inputFiles/Contratos_vector_to_be.xlsx")
    # searchUSIdsFromWebPage(exel_file_USs)
    searchUSIdsFromWebPage()
    # trimmedUserStoriesString = getUserStoriesFromExelFile(
    #     "./inputFiles/Contratos_vector_to_be.xlsx")
    # print(trimmedUserStoriesString)
    # writeFile("./transitionFiles/UserStoriesRelationships.md",
    #           trimmedUserStoriesString)
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
