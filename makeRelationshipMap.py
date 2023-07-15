from bs4 import BeautifulSoup
import pandas as pd
import graphviz
import textwrap
import re
import io
import json


# https://vectorcb.storiesonboard.com/storymapcard/contratos-vector-to-be/<USId>


def searchUSId(trimmendUS):
    buf = io.StringIO(trimmendUS)
    with open("./inputFiles/userStories.html", "r") as ushtml:
        soup = BeautifulSoup(ushtml, 'html.parser')
    us_from_web = []
    # counter = 0
    for x in soup.find_all('li', class_="board-subtask-card card board-card-color-white", id=True):
        for span in x.find_all('span', class_="board-card-title-text"):
            title = span.contents[1]
            # print(f"=> Id: {x['id']} - {title}")
            us_from_web.append({'id': x['id'], 'title': str(title)})
    # print(json.dumps(us_from_web, indent="  ", ensure_ascii=False))
    result = []
    webIdsAdded = []
    valueExists = -1
    for usfw in us_from_web:
        for us in buf:
            if usfw['title'] in us:
                try:
                    valueExists = webIdsAdded.index(usfw['id'])
                except ValueError:
                    result.append(
                        {"webId": usfw['id'], "title": usfw['title'], "description": "", "dependencies": []})
                    webIdsAdded.append(usfw['id'])
        buf.seek(0)
    print(json.dumps(result, indent="  ", ensure_ascii=False))
    return result


def getTrimedUserStories(fileName):
    with open(fileName, "r") as sourceFile:
        preresult = re.sub(r"\n? *\- *DEPENDENCIAS?(\*\*)?:?",
                           '', sourceFile.read())
        preresult = preresult.replace("\nHU", "\n    - HU")
        preresult = re.sub(r"^\n(?!.*(\-)).*$", ' ', preresult)
        buf = io.StringIO(preresult)
        preresult = ''
        for line in buf:
            if (re.search(r" * *\-", buf.readline()[:10])):
                preresult = preresult+line
    buf = io.StringIO(preresult)
    result = ""
    for line in buf:
        if len(line) > 1:
            result = result+line
            # print(f"({len(line)}) {line}", end="")
    return result


def writeFile(fileName, string):
    with open(fileName, "wt+") as resultFile:
        resultFile.write(string)
        searchUSId(string)


if __name__ == '__main__':
    trimmedUserStoriesString = getTrimedUserStories(
        "./transitionFiles/dependencies.txt")
    # print(trimmedUserStoriesString)
    writeFile("./transitionFiles/UserStoriesRelationships.md",
              trimmedUserStoriesString)
    userStories = searchUSId(trimmedUserStoriesString)
    # print(json.dumps(userStories, indent='  ', ensure_ascii=False))
    df = pd.ExcelFile(r"./inputFiles/Contratos_vector_to_be.xlsx")
    sheetX = df.parse(0)
    us_column = sheetX['Subtask']
    us_description_column = sheetX['Subtask description']
    for i, us in enumerate(userStories):
        for j, title in enumerate(us_column):
            try:
                if us['title'] in title:
                    us["description"] = us_description_column[i]
                    break
            except TypeError:
                break
    # print(json.dumps(userStories, indent='  ', ensure_ascii=False))
    print(f"[I] Making graphviz code...")
    dot = graphviz.Digraph('G', comment='US Process model relationships')
    dot.graph_attr['rankdir'] = 'TB'
    for i, us in enumerate(userStories):
        if len(us['title']) > 1:
            title_text = textwrap.indent(f"{us['title']}", '\\n')
            print(title_text)
            dot.node(f"US_{i}", title_text, shape='note')
    # dot.edges(['US_0', 'US_18'])
    print(dot.source)
    with open("./diagram.dot", "w+") as diagram_file:
        diagram_file.write(dot.source)
    print(f"Done!")
