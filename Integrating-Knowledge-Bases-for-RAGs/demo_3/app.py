# Step 1: Load libraries and create Flask application
from flask import Flask, request, render_template, jsonify
import spacy
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF
import numpy as np
from sklearn.decomposition import PCA
import json

app = Flask(__name__)


# Step 2: Entity Linking Using SpaCy
def entity_linking(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities


# Step 3: Load Knowledge Base from JSON and Create Knowledge Graph
def load_knowledge_base():
    with open("knowledge_base.json", "r") as kb_file:
        knowledge_base = json.load(kb_file)
    return knowledge_base


# Step 4: Create an RDF Knowledge Graph
def create_knowledge_graph(knowledge_base):
    g = Graph()
    EX = Namespace("http://example.org/")

    # Iterate over the knowledge base and add triples to the graph
    for key, value in knowledge_base.items():
        # Simple parsing to extract subject, predicate, and object from key
        subject_name, predicate_object = key.split(" founded ")
        subject = URIRef(f"http://example.org/{subject_name.replace(' ', '')}")
        predicate = URIRef(f"http://example.org/founded")
        obj = URIRef(f"http://example.org/{predicate_object.replace(' ', '')}")

        g.add((subject, RDF.type, FOAF.Person))
        g.add((subject, FOAF.name, Literal(subject_name)))
        g.add((subject, predicate, obj))
        g.add((obj, RDF.type, URIRef(f"http://example.org/Company")))
        g.add((obj, FOAF.name, Literal(predicate_object)))

    nodes = list(g.all_nodes())
    node_embeddings = np.random.rand(len(nodes), 10)
    pca = PCA(n_components=2)
    reduced_embeddings = pca.fit_transform(node_embeddings)

    return g, reduced_embeddings


# Step 5: Knowledge-Guided Retrieval
def knowledge_guided_retrieval(query, knowledge_base):
    if "founded" in query.lower():
        for key in knowledge_base:
            if "founded" in key and key.split(" ")[-1] in query:
                query = key
                break

    response = knowledge_base.get(query, "No relevant information found.")
    return response


# Step 6: Flask Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    text = request.form["inputText"]
    entities = entity_linking(text)
    knowledge_base = load_knowledge_base()
    graph, embeddings = create_knowledge_graph(knowledge_base)
    response = knowledge_guided_retrieval(text, knowledge_base)
    return jsonify(
        {"entities": entities, "response": response, "graph_size": len(graph)}
    )


if __name__ == "__main__":
    app.run(debug=True)
