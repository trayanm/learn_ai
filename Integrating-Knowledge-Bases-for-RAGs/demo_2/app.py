# Step 1 - Import Necessary Libraries

import wikipediaapi
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from flask import Flask, render_template, request

# Step 2 - Initialize the Flask Application

app = Flask(__name__)

# Step 3 - Initialize Wikipedia API

# Initialize Wikipedia API with correct argument names
wiki_wiki = wikipediaapi.Wikipedia(
    language="en", user_agent="RAGDemo/1.0 (bletort@bellsouth.net)"
)

# Step 4 - Simulating a Domain-Specific Database

# Simulated domain-specific database
domain_specific_data = {
    "data center": "A data center is a facility used to house computer systems and associated components, such as telecommunications and storage systems.",
    "AI ethics": "AI ethics is a branch of ethics of technology specific to artificially intelligent systems.",
    "Trajan": "Imperator of Rome. Has big nose. Born in Spain",
}

# Step 5 - Load a Pre-Trained NLP Model and Tokenizer

# Load pre-trained model and tokenizer
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Step 6 - defining the RAG System Function


def rag_system(query):
    # Step 1: Retrieve domain-specific data
    domain_data = None
    for key in domain_specific_data:
        if key.lower() in query.lower():
            print(f"Pair '{key}': {domain_specific_data[key]}")
            domain_data = domain_specific_data[key]
            break

    # Step 2: Fetch data from Wikipedia
    wiki_page = wiki_wiki.page(query)
    wiki_summary = wiki_page.summary if wiki_page.exists() else None

    # Step 3: Combine and process data
    combined_data = ""

    if domain_data:
        print(f"Domain-specific '{query}': {domain_data}")
        combined_data += domain_data + " "

    if wiki_summary:
        print(f"Wikipedia summary '{query}': {wiki_summary[:20]}...")
        combined_data += wiki_summary

    if combined_data:
        inputs = tokenizer(
            combined_data, return_tensors="pt", max_length=1024, truncation=True
        )
        outputs = model.generate(
            inputs["input_ids"], max_length=150, num_beams=5, early_stopping=True
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    else:
        response = "No relevant data found."

    return response


# Step 7 - Handling Web Requests and Displaying Results & Running the Flask Application


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        response = rag_system(query)
        return render_template("index.html", query=query, response=response)
    return render_template("index.html", query=None, response=None)


if __name__ == "__main__":
    app.run(debug=True)
