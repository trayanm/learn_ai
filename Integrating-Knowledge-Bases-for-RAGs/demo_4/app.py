from flask import Flask, request, render_template
import json
import networkx as nx
import plotly.graph_objects as go
import plotly

app = Flask(__name__)

# Load knowledge base
with open("knowledge_base.json", "r") as file:
    knowledge_base = json.load(file)


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


def generate_graph_visualization():
    """Generate Plotly graph visualization"""
    G = create_knowledge_graph()

    # Get node positions
    pos = nx.spring_layout(G, k=3, iterations=50)

    # Create edge traces
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
        line=dict(width=2, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        # Color nodes by type
        if G.nodes[node].get("type") == "person":
            node_colors.append("#FF6B6B")  # Red for persons
        else:
            node_colors.append("#4ECDC4")  # Teal for companies

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="middle center",
        hoverinfo="text",
        marker=dict(size=30, color=node_colors, line=dict(width=2, color="white")),
    )

    # Create the figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Knowledge Base Graph Visualization",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Red nodes: People, Teal nodes: Companies",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="white", size=12),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        ),
    )

    return plotly.offline.plot(fig, output_type="div", include_plotlyjs=True)


def find_answer(query):
    """Find answer from knowledge base"""
    query_lower = query.lower()
    for key, value in knowledge_base.items():
        if any(word in key.lower() for word in query_lower.split()):
            return value
    return "I don't have information about that in my knowledge base."


@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    response = ""
    graph_div = generate_graph_visualization()

    if request.method == "POST":
        query = request.form["query"]
        response = find_answer(query)

    return render_template(
        "index.html", query=query, response=response, graph_div=graph_div
    )


if __name__ == "__main__":
    app.run(debug=True)
