# Step 1: Load libraries and create Flask application
from flask import Flask, request, render_template, jsonify
import spacy
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF
import numpy as np
from sklearn.decomposition import PCA
import json
from transformers import BartTokenizer, BartForConditionalGeneration
import torch

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


# Step 5: Load BART Model for Text Generation
def load_bart_model():
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    return tokenizer, model


# Step 6: Generate Response Using BART
def generate_response_with_bart(query, context, tokenizer, model):
    inputs = tokenizer(
        query, context, return_tensors="pt", max_length=1024, truncation=True
    )
    summary_ids = model.generate(
        inputs["input_ids"], num_beams=4, max_length=100, early_stopping=True
    )
    bart_response = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return bart_response


# Step 7: Knowledge-Guided Retrieval with BART Integration
def knowledge_guided_retrieval(query, knowledge_base, tokenizer, model):
    # Try to find the most relevant context in the knowledge base based on the query
    relevant_contexts = []
    for key, value in knowledge_base.items():
        if any(term.lower() in query.lower() for term in key.split()):
            relevant_contexts.append(value)

    # If relevant context is found, use it; otherwise, fall back to the entire knowledge base
    if relevant_contexts:
        context = " ".join(relevant_contexts)
    else:
        context = " ".join(knowledge_base.values())

    bart_response = generate_response_with_bart(query, context, tokenizer, model)

    return bart_response


# Step 8: Flask Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    text = request.form["inputText"]
    entities = entity_linking(text)
    knowledge_base = load_knowledge_base()
    graph, embeddings = create_knowledge_graph(knowledge_base)

    tokenizer, model = load_bart_model()
    response = knowledge_guided_retrieval(text, knowledge_base, tokenizer, model)

    return jsonify(
        {"entities": entities, "response": response, "graph_size": len(graph)}
    )


if __name__ == "__main__":
    app.run(debug=True)
