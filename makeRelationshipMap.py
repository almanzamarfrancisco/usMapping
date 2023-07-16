from bs4 import BeautifulSoup
import pandas as pd
import graphviz
import textwrap
import re
import io
import json
import requests


# https://vectorcb.storiesonboard.com/storymapcard/contratos-vector-to-be/<USId>


def searchUSIdsFromWebPage(user_stories: list):
    url = 'https://vectorcb.storiesonboard.com/m/contratos-vector-to-be'
    with open("./inputFiles/cookies.json", "r+") as cookiesfile:
        cookies = json.load(cookiesfile)
    response = requests.get(url, cookies=cookies)
    with open("./inputFiles/storiesOnBoard.html", "w+") as html:
        html.write(response.text)
    # buf = io.StringIO(trimmendUS)
    # with open("./inputFiles/userStories.html", "r") as ushtml:
    #     soup = BeautifulSoup(ushtml, 'html.parser')
    # us_from_web = []
    # # counter = 0
    # for x in soup.find_all('li', class_="board-subtask-card card board-card-color-white", id=True):
    #     for span in x.find_all('span', class_="board-card-title-text"):
    #         title = span.contents[1]
    #         # print(f"=> Id: {x['id']} - {title}")
    #         us_from_web.append({'id': x['id'], 'title': str(title)})
    # # print(json.dumps(us_from_web, indent="  ", ensure_ascii=False))
    # result = []
    # webIdsAdded = []
    # valueExists = -1
    # for usfw in us_from_web:
    #     for us in buf:
    #         if usfw['title'] in us:
    #             try:
    #                 valueExists = webIdsAdded.index(usfw['id'])
    #             except ValueError:
    #                 result.append(
    #                     {"webId": usfw['id'], "title": usfw['title'], "description": "", "dependencies": []})
    #                 webIdsAdded.append(usfw['id'])
    #     buf.seek(0)
    # print(json.dumps(result, indent="  ", ensure_ascii=False))
    # return result


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
    searchUSIdsFromWebPage(exel_file_USs)
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
