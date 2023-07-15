import re
import io
import graphviz

if __name__ == '__main__':
    print(f"[I] Making graphviz code...")
    dot = graphviz.Digraph(comment='US Process model relationships')
    dot.node('A', 'King Arthur')  # doctest: +NO_EXE
    dot.node('B', 'Sir Bedevere the Wise')
    dot.node('L', 'Sir Lancelot the Brave')
    dot.edges(['AB', 'AL'])
    dot.edge('B', 'L', constraint='false')
    with open("./diagram.dot", "w+") as diagram_file:
        diagram_file.write(dot.source)
    print(f"Done!")
