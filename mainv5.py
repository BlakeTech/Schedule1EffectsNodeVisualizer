import json
import math
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import colorsys


# === Configuration ===
class AppState:
    data_file = "schedule1-params.json"
    ingredients = []
    effect_names = {}
    effect_id_map = {}
    edges = []
    node_positions = {}
    node_colors = {}
    highlight_color = "#FF5733"
    faded_opacity = 0.5
    radius = 600


# === Load Data ===
def load_data():
    with open(AppState.data_file, "r") as f:
        data = json.load(f)
    AppState.ingredients = data["ingredientsList"]
    AppState.effect_names = data["effectlist"]
    AppState.effect_id_map = {int(k): v for k, v in AppState.effect_names.items()}

    # Assign unique colors per effect (skip black)
    palette = generate_rainbow_hex_colours(34)

    for i, effect_id in enumerate(AppState.effect_id_map):
        AppState.node_colors[effect_id] = palette[i % len(palette)]

    # Build edges from ingredients
    AppState.edges = []
    for ing in AppState.ingredients:
        for src, tgt in ing.get("effects", [])[1:]:
            AppState.edges.append((src, tgt))


# Colours generator
def generate_rainbow_hex_colours(n: int) -> list[str]:
    hex_colors = []
    for i in range(n):
        hue = i / n  # Hue from 0.0 to 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)  # Full saturation and brightness
        hex_color = "#{:02X}{:02X}{:02X}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        hex_colors.append(hex_color)
    return hex_colors


# === Prepare Graph ===
def prepare_graph(selected_ingredient):
    graph = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#000000",
        font_color="white",
    )
    num_nodes = len(AppState.effect_id_map)
    center_x = 0
    center_y = 0

    relevant_nodes = set()
    relevant_edges = set()
    outgoing_from = set()

    if selected_ingredient != "None":
        for ing in AppState.ingredients:
            if ing["name"] == selected_ingredient:
                for src, tgt in ing["effects"][1:]:
                    relevant_edges.add((src, tgt))
                    outgoing_from.add(src)
                    relevant_nodes.add(src)
                    relevant_nodes.add(tgt)
                break

    for idx, (effect_id, label) in enumerate(AppState.effect_id_map.items()):
        angle = 2 * math.pi * idx / num_nodes
        x = center_x + AppState.radius * math.cos(angle)
        y = center_y + AppState.radius * math.sin(angle)
        AppState.node_positions[effect_id] = (x, y)

        opacity = (
            1.0
            if (not relevant_nodes or effect_id in relevant_nodes)
            else AppState.faded_opacity
        )
        color = AppState.node_colors.get(effect_id, "#3498db")
        graph.add_node(
            n_id=effect_id,
            label=label,
            x=x,
            y=y,
            color=color,
            fixed=True,
            physics=False,
            opacity=opacity,
        )

    for src, tgt in AppState.edges:
        color = AppState.node_colors.get(src, "#aaaaaa")
        # highlight only arrows going FROM selected node, not TO it
        if selected_ingredient != "None" and (
            src in relevant_nodes and src in outgoing_from
        ):
            highlight = (src, tgt) in relevant_edges
        else:
            highlight = False
        opacity = (
            1.0 if highlight else AppState.faded_opacity if relevant_nodes else 1.0
        )
        if not highlight:
            # match arrow opacity to source node
            source_opacity = (
                AppState.faded_opacity if src not in relevant_nodes else 1.0
            )
            opacity = source_opacity

        graph.add_edge(
            source=src,
            to=tgt,
            color=color,
            arrows="to",
            smooth={"type": "cubicBezier", "roundness": 0.5},
            physics=False,
            opacity=opacity,
        )

    return graph


# === Draw Graph with PyVis ===
def draw_graph(selected_ingredient, graph_html_path="graph.html"):
    graph = prepare_graph(selected_ingredient)
    graph.write_html(graph_html_path, notebook=False, open_browser=False)
    with open(graph_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=900, scrolling=True)


# === Sidebar Ingredient Selector ===
def sidebar_ingredient_selector():
    st.sidebar.title("Ingredients")
    ingredient_names = [item["name"] for item in AppState.ingredients]
    selected = st.sidebar.selectbox(
        "Select an ingredient:", ["None"] + ingredient_names
    )
    return selected


# === Streamlit App Entry ===
def main():
    st.set_page_config(page_title="Effect Transformation Graph", layout="wide")
    st.title("Effect Transformation Network Viewer")

    load_data()
    selected_ingredient = sidebar_ingredient_selector()
    draw_graph(selected_ingredient)


if __name__ == "__main__":
    main()
