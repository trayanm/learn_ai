from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import json
import networkx as nx
import plotly.graph_objects as go
import plotly
import re

app = Flask(__name__)

# Configure CORS to allow requests from React development server
CORS(app, origins=["http://localhost:3000"])

# Load spacy model for NER (optional)
try:
    import spacy

    nlp = spacy.load("en_core_web_sm")
    print("SpaCy model loaded successfully")
except (ImportError, OSError):
    print("SpaCy not available. Using fallback pattern matching.")
    nlp = None

# Load knowledge base
try:
    with open("knowledge_base.json", "r") as file:
        knowledge_base = json.load(file)
except FileNotFoundError:
    print("Warning: knowledge_base.json not found. Using empty knowledge base.")
    knowledge_base = {}


def create_knowledge_graph():
    """Create a network graph from the knowledge base"""
    G = nx.Graph()

    # Add nodes and edges from knowledge base
    for key, value in knowledge_base.items():
        # Extract entities from the key (simplified parsing)
        words = key.split()
        if len(words) >= 3:  # e.g., "Bill Gates founded Microsoft"
            person = f"{words[0]} {words[1]}"  # First two words as person name
            company = words[-1]  # Last word as company

            # Add nodes
            G.add_node(person, type="person")
            G.add_node(company, type="company")
            # Add edge
            G.add_edge(person, company, relation="founded")

    return G


def extract_entities_from_text(text):
    """Extract entities from input text using spaCy NER or fallback patterns"""
    entities = {"PERSON": [], "ORG": [], "GPE": [], "PRODUCT": []}

    if nlp is None:
        # Improved fallback pattern matching

        # Single name pattern (for names like "Bellamy", "Octavia")
        single_name_pattern = r"\b[A-Z][a-z]{2,}\b"

        # Full name pattern (for names like "John Smith")
        full_name_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"

        # Find full names first
        full_names = re.findall(full_name_pattern, text)
        entities["PERSON"].extend(
            [name for name in full_names if len(name.split()) <= 3]
        )

        # Find single names that are not part of organizations
        single_names = re.findall(single_name_pattern, text)

        # Filter out common words and organization indicators
        common_words = {
            "The",
            "This",
            "That",
            "Inc",
            "Corp",
            "Ltd",
            "LLC",
            "Company",
            "Technologies",
            "Systems",
            "Group",
            "Industries",
            "Apple",
            "Microsoft",
            "Google",
            "Amazon",
            "Facebook",
            "Tesla",
            "SpaceX",
        }

        # Add single names that are likely person names
        for name in single_names:
            if (
                name not in common_words
                and name not in [n.split()[0] for n in entities["PERSON"]]
                and name not in [n.split()[-1] for n in entities["PERSON"]]
            ):

                # Check if it's in a person context
                name_lower = name.lower()
                person_context_words = [
                    "brother",
                    "sister",
                    "son",
                    "daughter",
                    "father",
                    "mother",
                    "parent",
                    "child",
                    "friend",
                    "colleague",
                ]

                text_around_name = ""
                name_pos = text.lower().find(name_lower)
                if name_pos != -1:
                    start = max(0, name_pos - 50)
                    end = min(len(text), name_pos + len(name) + 50)
                    text_around_name = text[start:end].lower()

                if any(word in text_around_name for word in person_context_words):
                    entities["PERSON"].append(name)

        # Organization patterns
        org_patterns = [
            r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Technologies|Systems|Group|Industries))\b",
            r"\b(?:Apple|Microsoft|Google|Amazon|Facebook|Tesla|SpaceX|Netflix|Twitter|Meta)\b",
        ]

        for pattern in org_patterns:
            orgs = re.findall(pattern, text, re.IGNORECASE)
            entities["ORG"].extend(orgs)

        # Location pattern
        location_pattern = r"\b(?:California|New York|Texas|London|Paris|Tokyo|Berlin|Sydney|Toronto|Singapore|USA|UK|Canada|Australia)\b"
        locations = re.findall(location_pattern, text, re.IGNORECASE)
        entities["GPE"].extend(locations)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    # Use spaCy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))

    return entities


def create_graph_from_entities(entities, relationships_text=""):
    """Create a network graph from extracted entities"""
    G = nx.Graph()

    # Add person nodes
    for person in entities["PERSON"]:
        G.add_node(person, type="person")

    # Add organization nodes
    for org in entities["ORG"]:
        G.add_node(org, type="organization")

    # Add location nodes
    for location in entities["GPE"]:
        G.add_node(location, type="location")

    # Add product nodes
    for product in entities["PRODUCT"]:
        G.add_node(product, type="product")

    # Simple relationship detection based on common patterns
    text_lower = relationships_text.lower()
    words = text_lower.split()

    # Look for founding relationships
    founding_words = ["founded", "started", "created", "established", "co-founded"]
    for person in entities["PERSON"]:
        for org in entities["ORG"]:
            person_lower = person.lower()
            org_lower = org.lower()
            if person_lower in text_lower and org_lower in text_lower:
                # Check if they appear in founding context
                for word in founding_words:
                    pattern = f"{re.escape(person_lower)}.*{word}.*{re.escape(org_lower)}|{re.escape(org_lower)}.*{word}.*{re.escape(person_lower)}"
                    if re.search(pattern, text_lower):
                        G.add_edge(person, org, relation="founded")
                        break

    # Look for work relationships
    work_words = ["works at", "ceo of", "president of", "director of", "employed by"]
    for person in entities["PERSON"]:
        for org in entities["ORG"]:
            person_lower = person.lower()
            org_lower = org.lower()
            if person_lower in text_lower and org_lower in text_lower:
                for word in work_words:
                    pattern = (
                        f"{re.escape(person_lower)}.*{word}.*{re.escape(org_lower)}"
                    )
                    if re.search(pattern, text_lower):
                        G.add_edge(person, org, relation="works_at")
                        break

    # Look for family relationships with corrected patterns
    family_patterns = [
        (
            r"(\w+)\s+is\s+(?:the\s+)?(?:brother|sister|son|daughter|father|mother|parent|child)\s+of\s+(\w+)",
            "family",
        ),
        (
            r"(\w+)\s+and\s+(\w+)\s+are\s+(?:siblings|brothers|sisters|related)",
            "family",
        ),
        (
            r"(\w+)(?:'s|s)\s+(?:brother|sister|son|daughter|father|mother|parent|child)\s+is\s+(\w+)",
            "family",
        ),
        (r"(\w+)\s+(?:brother|sister)\s+(\w+)", "family"),
    ]

    for pattern, relation_type in family_patterns:
        try:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                entity1, entity2 = match.groups()
                # Find the actual entity names that match
                matched_persons = []

                for person in entities["PERSON"]:
                    person_lower = person.lower()
                    # Check if the matched groups are part of person names
                    if (
                        entity1 in person_lower
                        or person_lower in entity1
                        or any(part in person_lower for part in entity1.split())
                    ):
                        matched_persons.append(person)
                    if (
                        entity2 in person_lower
                        or person_lower in entity2
                        or any(part in person_lower for part in entity2.split())
                    ):
                        if person not in matched_persons:
                            matched_persons.append(person)

                # Create edges between matched persons
                if len(matched_persons) >= 2:
                    for i, person1 in enumerate(matched_persons):
                        for person2 in matched_persons[i + 1 :]:
                            if not G.has_edge(person1, person2):
                                G.add_edge(person1, person2, relation=relation_type)
        except re.error as e:
            print(f"Regex error in pattern {pattern}: {e}")
            continue

    # Enhanced relationship detection using sentence-level analysis
    sentences = re.split(r"[.!?]+", relationships_text)

    for sentence in sentences:
        sentence = sentence.strip().lower()
        if not sentence:
            continue

        # Find all entities in this sentence
        entities_in_sentence = []
        for entity_type in ["PERSON", "ORG", "GPE", "PRODUCT"]:
            for entity in entities[entity_type]:
                if entity.lower() in sentence:
                    entities_in_sentence.append(entity)

        # If we have multiple entities in the same sentence, create relationships
        if len(entities_in_sentence) >= 2:
            # Look for specific relationship words in the sentence
            relationship_words = {
                "founded": "founded",
                "created": "created",
                "established": "established",
                "works": "works_at",
                "employed": "works_at",
                "brother": "family",
                "sister": "family",
                "son": "family",
                "daughter": "family",
                "father": "family",
                "mother": "mother",
                "parent": "family",
                "child": "family",
                "sibling": "family",
                "married": "married",
                "friend": "friend",
                "partner": "partner",
                "colleague": "colleague",
                "owns": "owns",
                "leads": "leads",
                "manages": "manages",
            }

            detected_relation = "related"  # default
            for word, relation in relationship_words.items():
                if word in sentence:
                    detected_relation = relation
                    break

            # Create edges between entities in the same sentence
            for i, entity1 in enumerate(entities_in_sentence):
                for entity2 in entities_in_sentence[i + 1 :]:
                    if not G.has_edge(entity1, entity2):
                        G.add_edge(entity1, entity2, relation=detected_relation)

    # Fallback: Connect entities that appear close together (within 5 words)
    all_entities = (
        entities["PERSON"] + entities["ORG"] + entities["GPE"] + entities["PRODUCT"]
    )

    for i, entity1 in enumerate(all_entities):
        for entity2 in all_entities[i + 1 :]:
            if not G.has_edge(entity1, entity2):
                # Check if entities appear within 5 words of each other
                entity1_lower = entity1.lower()
                entity2_lower = entity2.lower()

                # Simple proximity check
                try:
                    # Find positions in the original text
                    text_words = relationships_text.lower().split()
                    entity1_positions = [
                        i
                        for i, word in enumerate(text_words)
                        if entity1_lower in word
                        or any(part in word for part in entity1_lower.split())
                    ]
                    entity2_positions = [
                        i
                        for i, word in enumerate(text_words)
                        if entity2_lower in word
                        or any(part in word for part in entity2_lower.split())
                    ]

                    # Check if any positions are close to each other
                    for pos1 in entity1_positions:
                        for pos2 in entity2_positions:
                            if abs(pos1 - pos2) <= 5:  # Within 5 words
                                G.add_edge(entity1, entity2, relation="related")
                                break
                        if G.has_edge(entity1, entity2):
                            break
                except Exception as e:
                    print(f"Error in proximity check: {e}")
                    continue

    return G


def generate_dynamic_graph_visualization(G):
    """Generate Plotly graph visualization from a NetworkX graph"""
    if len(G.nodes()) == 0:
        return "<div style='color: white; text-align: center; padding: 20px;'>No entities found to visualize</div>"

    # Get node positions with better spacing
    pos = nx.spring_layout(G, k=4, iterations=100, seed=42)

    # Create visible edge traces (lines only)
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=4, color="#888"),
        hoverinfo="none",
        mode="lines",
        name="Relationships",
        showlegend=False,
    )

    # Create invisible hover traces for edges (points at edge midpoints)
    edge_hover_x = []
    edge_hover_y = []
    edge_hover_text = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        # Calculate midpoint
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2

        edge_hover_x.append(mid_x)
        edge_hover_y.append(mid_y)

        # Add edge info for hover
        relation = G.edges[edge].get("relation", "related")
        hover_text = f"<b>{edge[0]} ←→ {edge[1]}</b><br>Relationship: <i>{relation}</i>"
        edge_hover_text.append(hover_text)

    # Create invisible markers at edge midpoints for hovering
    edge_hover_trace = go.Scatter(
        x=edge_hover_x,
        y=edge_hover_y,
        mode="markers",
        marker=dict(
            size=15,
            color="rgba(0,0,0,0)",
            line=dict(width=0),
        ),
        hoverinfo="text",
        hovertext=edge_hover_text,
        name="Edge Info",
        showlegend=False,
        customdata=[f"{edge[0]}|{edge[1]}" for edge in G.edges()],
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_info = []
    node_customdata = []

    # Color map that matches the HTML template
    color_map = {
        "PERSON": "#FF6B6B",
        "ORG": "#4ECDC4",
        "GPE": "#45B7D1",
        "PRODUCT": "#96CEB4",
        "person": "#FF6B6B",
        "organization": "#4ECDC4",
        "location": "#45B7D1",
        "product": "#96CEB4",
        "company": "#4ECDC4",
    }

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        node_type = G.nodes[node].get("type", "unknown")
        node_colors.append(color_map.get(node_type, "#CCCCCC"))

        # Add connection info
        connections = list(G.neighbors(node))
        connection_info = (
            f"Connections: {', '.join(connections[:3])}"
            if connections
            else "No connections"
        )
        if len(connections) > 3:
            connection_info += f" and {len(connections) - 3} more..."

        node_info.append(
            f"<b>{node}</b><br>Type: <i>{node_type}</i><br>{connection_info}"
        )
        node_customdata.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="middle center",
        textfont=dict(color="white", size=12, family="Arial Black"),
        hoverinfo="text",
        hovertext=node_info,
        marker=dict(size=50, color=node_colors, line=dict(width=3, color="white")),
        name="Entities",
        showlegend=False,
        customdata=node_customdata,
    )

    # Create the figure with all traces
    fig = go.Figure(
        data=[edge_trace, edge_hover_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text="Extracted Entities Graph", font=dict(size=20, color="white")
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=40, l=40, r=40, t=60),
            height=550,
            annotations=[
                dict(
                    text="Red: People • Teal: Organizations • Blue: Locations • Green: Products<br><i>Click on nodes or edges to highlight connections • Use controls to show/hide nodes</i>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=-0.12,
                    xanchor="center",
                    yanchor="bottom",
                    font=dict(color="white", size=11),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        ),
    )

    # Convert to HTML with toolbar enabled
    config = {"displayModeBar": True}
    plot_html = plotly.offline.plot(
        fig, output_type="div", include_plotlyjs=True, config=config
    )

    return plot_html


def generate_graph_visualization():
    """Generate Plotly graph visualization"""
    G = create_knowledge_graph()

    if len(G.nodes()) == 0:
        return "<div style='color: white; text-align: center; padding: 20px;'>No knowledge base data found</div>"

    # Get node positions
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

    # Create visible edge traces (lines only)
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=3, color="#888"),
        hoverinfo="none",
        mode="lines",
        name="Relationships",
        showlegend=False,
    )

    # Create invisible hover traces for edges
    edge_hover_x = []
    edge_hover_y = []
    edge_hover_text = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        # Calculate midpoint
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2

        edge_hover_x.append(mid_x)
        edge_hover_y.append(mid_y)

        # Add edge info for hover
        relation = G.edges[edge].get("relation", "founded")
        hover_text = f"<b>{edge[0]} ←→ {edge[1]}</b><br>Relationship: <i>{relation}</i>"
        edge_hover_text.append(hover_text)

    edge_hover_trace = go.Scatter(
        x=edge_hover_x,
        y=edge_hover_y,
        mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)", line=dict(width=0)),
        hoverinfo="text",
        hovertext=edge_hover_text,
        name="Edge Info",
        showlegend=False,
        customdata=[f"{edge[0]}|{edge[1]}" for edge in G.edges()],
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_info = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        # Color nodes by type
        node_type = G.nodes[node].get("type", "unknown")
        if node_type == "person":
            node_colors.append("#FF6B6B")
        else:
            node_colors.append("#4ECDC4")

        # Add node hover info
        connections = list(G.neighbors(node))
        connection_info = (
            f"Connections: {', '.join(connections)}"
            if connections
            else "No connections"
        )
        node_info.append(
            f"<b>{node}</b><br>Type: <i>{node_type}</i><br>{connection_info}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="middle center",
        textfont=dict(color="white", size=12),
        hoverinfo="text",
        hovertext=node_info,
        marker=dict(size=35, color=node_colors, line=dict(width=2, color="white")),
        customdata=list(G.nodes()),
    )

    # Create the figure
    fig = go.Figure(
        data=[edge_trace, edge_hover_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text="Knowledge Base Graph Visualization",
                font=dict(size=16, color="white"),
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Red nodes: People, Teal nodes: Companies<br><i>Click on nodes to highlight connections</i>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.05,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="white", size=11),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        ),
    )

    # Convert to HTML with toolbar enabled
    config = {"displayModeBar": True}
    plot_html = plotly.offline.plot(
        fig, output_type="div", include_plotlyjs=True, config=config
    )

    return plot_html


def generate_graph_visualization():
    """Generate Plotly graph visualization"""
    G = create_knowledge_graph()

    if len(G.nodes()) == 0:
        return "<div style='color: white; text-align: center; padding: 20px;'>No knowledge base data found</div>"

    # Get node positions
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

    # Create visible edge traces (lines only)
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=3, color="#888"),
        hoverinfo="none",
        mode="lines",
        name="Relationships",
        showlegend=False,
    )

    # Create invisible hover traces for edges
    edge_hover_x = []
    edge_hover_y = []
    edge_hover_text = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        # Calculate midpoint
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2

        edge_hover_x.append(mid_x)
        edge_hover_y.append(mid_y)

        # Add edge info for hover
        relation = G.edges[edge].get("relation", "founded")
        hover_text = f"<b>{edge[0]} ←→ {edge[1]}</b><br>Relationship: <i>{relation}</i>"
        edge_hover_text.append(hover_text)

    edge_hover_trace = go.Scatter(
        x=edge_hover_x,
        y=edge_hover_y,
        mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)", line=dict(width=0)),
        hoverinfo="text",
        hovertext=edge_hover_text,
        name="Edge Info",
        showlegend=False,
        customdata=[f"{edge[0]}|{edge[1]}" for edge in G.edges()],
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_info = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        # Color nodes by type
        node_type = G.nodes[node].get("type", "unknown")
        if node_type == "person":
            node_colors.append("#FF6B6B")
        else:
            node_colors.append("#4ECDC4")

        # Add node hover info
        connections = list(G.neighbors(node))
        connection_info = (
            f"Connections: {', '.join(connections)}"
            if connections
            else "No connections"
        )
        node_info.append(
            f"<b>{node}</b><br>Type: <i>{node_type}</i><br>{connection_info}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="middle center",
        textfont=dict(color="white", size=12),
        hoverinfo="text",
        hovertext=node_info,
        marker=dict(size=35, color=node_colors, line=dict(width=2, color="white")),
        customdata=list(G.nodes()),
    )

    # Create the figure
    fig = go.Figure(
        data=[edge_trace, edge_hover_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text="Knowledge Base Graph Visualization",
                font=dict(size=16, color="white"),
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Red nodes: People, Teal nodes: Companies<br><i>Click on nodes to highlight connections</i>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.05,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="white", size=11),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        ),
    )

    # Convert to HTML with custom JavaScript
    config = {"displayModeBar": True}  # Enable toolbar
    plot_html = plotly.offline.plot(
        fig, output_type="div", include_plotlyjs=True, config=config
    )

    # Add custom JavaScript for click handling
    adjacency = {node: list(G.neighbors(node)) for node in G.nodes()}
    original_colors = [
        ("#FF6B6B" if G.nodes[node].get("type") == "person" else "#4ECDC4")
        for node in G.nodes()
    ]

    # Use regular string formatting to avoid f-string issues with JavaScript
    custom_js = (
        """
    <script>
        setTimeout(function() {
            const plotElement = document.querySelector('.plotly-graph-div');
            if (!plotElement) return;
            
            const adjacency = """
        + str(adjacency)
        + """;
            const originalColors = """
        + str(original_colors)
        + """;
            const nodes = """
        + str(list(G.nodes()))
        + """;
            let isHighlighted = false;
            
            plotElement.on('plotly_click', function(data) {
                if (!data.points || data.points.length === 0) return;
                
                const point = data.points[0];
                if (point.data.name !== 'Entities') return;
                
                const clickedNode = point.customdata;
                
                if (isHighlighted) {
                    // Reset highlight
                    Plotly.restyle(plotElement, {'marker.color': [originalColors]}, [2]);
                    isHighlighted = false;
                } else {
                    // Highlight connected nodes
                    const connectedNodes = adjacency[clickedNode] || [];
                    const nodeColors = originalColors.map((color) => {
                        const r = parseInt(color.slice(1, 3), 16);
                        const g = parseInt(color.slice(3, 5), 16);
                        const b = parseInt(color.slice(5, 7), 16);
                        return `rgba(${r},${g},${b},0.3)`;
                    });
                    
                    // Highlight clicked node
                    const clickedIndex = nodes.indexOf(clickedNode);
                    if (clickedIndex !== -1) {
                        nodeColors[clickedIndex] = originalColors[clickedIndex];
                    }
                    
                    // Highlight connected nodes
                    connectedNodes.forEach(node => {
                        const index = nodes.indexOf(node);
                        if (index !== -1) {
                            nodeColors[index] = originalColors[index];
                        }
                    });
                    
                    Plotly.restyle(plotElement, {'marker.color': [nodeColors]}, [2]);
                    isHighlighted = true;
                }
            });
        }, 1000);
    </script>
    """
    )

    return plot_html + custom_js


def find_answer(query):
    """Find answer from knowledge base"""
    if not knowledge_base:
        return "Knowledge base is empty or not loaded."

    query_lower = query.lower()
    for key, value in knowledge_base.items():
        if any(word in key.lower() for word in query_lower.split()):
            return value
    return "I don't have information about that in my knowledge base."


@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    response = ""

    try:
        graph_div = generate_graph_visualization()
    except Exception as e:
        graph_div = f"<div style='color: red; text-align: center; padding: 20px;'>Error generating graph: {str(e)}</div>"

    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            response = find_answer(query)

    return render_template(
        "index.html", query=query, response=response, graph_div=graph_div
    )


@app.route("/extract", methods=["GET", "POST"])
def extract_entities():
    """Endpoint to extract entities from text and create graph"""
    input_text = ""
    entities = {}
    graph_div = ""
    graph_data = None

    if request.method == "POST":
        input_text = request.form.get("text", "")
        if input_text:
            try:
                # Extract entities
                entities = extract_entities_from_text(input_text)

                # Create graph from entities
                G = create_graph_from_entities(entities, input_text)
                graph_div = generate_dynamic_graph_visualization(G)

                # Prepare graph data for JavaScript (fix JSON serialization)
                if len(G.nodes()) > 0:
                    pos = nx.spring_layout(G, k=4, iterations=100, seed=42)
                    color_map = {
                        "PERSON": "#FF6B6B",
                        "ORG": "#4ECDC4",
                        "GPE": "#45B7D1",
                        "PRODUCT": "#96CEB4",
                        "person": "#FF6B6B",
                        "organization": "#4ECDC4",
                        "location": "#45B7D1",
                        "product": "#96CEB4",
                        "company": "#4ECDC4",
                    }

                    graph_data = {
                        "nodes": list(G.nodes()),
                        "edges": list(G.edges()),
                        "adjacency": {
                            node: list(G.neighbors(node)) for node in G.nodes()
                        },
                        "originalColors": [
                            color_map.get(
                                G.nodes[node].get("type", "unknown"), "#CCCCCC"
                            )
                            for node in G.nodes()
                        ],
                        "positions": {
                            node: [
                                float(pos[node][0]),
                                float(pos[node][1]),
                            ]  # Convert numpy arrays to lists
                            for node in G.nodes()
                        },
                    }
                else:
                    graph_data = {
                        "nodes": [],
                        "edges": [],
                        "adjacency": {},
                        "originalColors": [],
                        "positions": {},
                    }

            except Exception as e:
                print(f"Error processing text: {e}")  # Debug logging
                graph_div = f"<div style='color: red; text-align: center; padding: 20px;'>Error processing text: {str(e)}</div>"
                graph_data = None

    return render_template(
        "extract.html",
        input_text=input_text,
        entities=entities,
        graph_div=graph_div,
        graph_data=graph_data,
    )


@app.route("/api/extract", methods=["POST"])
def api_extract_entities():
    """API endpoint to extract entities from text"""
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data["text"]
        entities = extract_entities_from_text(text)

        # Create graph from entities
        G = create_graph_from_entities(entities, text)

        # Convert graph to JSON format (fix numpy array serialization)
        if len(G.nodes()) > 0:
            pos = nx.spring_layout(G, k=4, iterations=100, seed=42)

            color_map = {
                "PERSON": "#FF6B6B",
                "ORG": "#4ECDC4",
                "GPE": "#45B7D1",
                "PRODUCT": "#96CEB4",
                "person": "#FF6B6B",
                "organization": "#4ECDC4",
                "location": "#45B7D1",
                "product": "#96CEB4",
                "company": "#4ECDC4",
            }

            graph_data = {
                "nodes": list(G.nodes()),  # Just return node names as strings
                "edges": list(G.edges()),  # Return edges as tuples
                "adjacency": {node: list(G.neighbors(node)) for node in G.nodes()},
                "originalColors": [
                    color_map.get(G.nodes[node].get("type", "unknown"), "#CCCCCC")
                    for node in G.nodes()
                ],
                "positions": {
                    node: [float(pos[node][0]), float(pos[node][1])]
                    for node in G.nodes()
                },
                # Add node types separately for React component
                "nodeTypes": {
                    node: G.nodes[node].get("type", "unknown") for node in G.nodes()
                },
            }
        else:
            graph_data = {
                "nodes": [],
                "edges": [],
                "adjacency": {},
                "originalColors": [],
                "positions": {},
                "nodeTypes": {},
            }

        return jsonify({"entities": entities, "graph": graph_data})

    except Exception as e:
        print(f"API error: {e}")  # Debug logging
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
