import re
import plotly.graph_objects as go
import streamlit as st

def extract_valid_config(config_text):
    """ Extracts firewall policies while handling nested 'end' statements correctly. """
    valid_config = []
    inside_policy = False
    nested_edit = 0
    
    for line in config_text.splitlines():
        if line.strip().startswith("config firewall policy"):
            inside_policy = True
        
        if inside_policy:
            if line.strip().startswith("edit"):
                nested_edit += 1
            if line.strip() == "end":
                if nested_edit > 1:
                    nested_edit -= 1
                    continue  # Skip nested end
                else:
                    inside_policy = False  # End main policy block
        
        if inside_policy:
            valid_config.append(line)
    
    return "\n".join(valid_config)

def parse_firewall_policy(config_text):
    policies = []
    policy_blocks = config_text.split('next')
    policy_pattern = re.compile(
        r"edit (\d+)\n.*?set name \"(.*?)\".*?set srcintf \"(.*?)\".*?set dstintf \"(.*?)\"(?:.*?set srcaddr \"(.*?)\")?(?:.*?set dstaddr \"(.*?)\")?(?:.*?set service \"(.*?)\")?(?:.*?set logtraffic \"(.*?)\")?", 
        re.DOTALL
    )
    
    policy_map = []
    
    for block in policy_blocks:
        match = policy_pattern.search(block)
        if match:
            policy_id, name, srcintf, dstintf, srcaddr, dstaddr, service, logtraffic = match.groups()
            
            # Handle missing fields
            srcaddr = srcaddr if srcaddr else "N/A"
            dstaddr = dstaddr if dstaddr else "N/A"
            service = service if service else "ALL"
            logtraffic = logtraffic if logtraffic else "N/A"
            
            policy_map.append((policy_id, name, srcintf, dstintf, srcaddr, dstaddr, service, logtraffic))
    
    return policy_map

def generate_sankey(policy_map):
    sources, targets, values, hover_texts = [], [], [], []
    node_labels = {}
    index = 0
    grouped_sources = {}
    grouped_targets = {}
    
    for policy_id, name, src, dst, srcaddr, dstaddr, service, logtraffic in policy_map:
        if src not in grouped_sources:
            grouped_sources[src] = f"{src} (Group)"
        if dst not in grouped_targets:
            grouped_targets[dst] = dst  # Keep destinations as final nodes without grouping
    
    all_nodes = set(grouped_sources.values()).union(set(grouped_targets.values()))
    for node in all_nodes:
        if node not in node_labels:
            node_labels[node] = index
            index += 1
    
    for policy_id, name, src, dst, srcaddr, dstaddr, service, logtraffic in policy_map:
        src_grouped = grouped_sources[src]
        dst_final = grouped_targets[dst]  # Ensure destinations do not become sources
        
        if src_grouped not in node_labels:
            node_labels[src_grouped] = index
            index += 1
        if dst_final not in node_labels:
            node_labels[dst_final] = index
            index += 1
        
        sources.append(node_labels[src_grouped])
        targets.append(node_labels[dst_final])
        values.append(1)
        hover_texts.append(f"Policy ID: {policy_id}<br>Name: {name}<br>Source: {srcaddr}<br>Destination: {dstaddr}<br>Service: {service}<br>Log Traffic: {logtraffic}")
    
    node_names = list(node_labels.keys())
    
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=node_names
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,  # Equal weight for visualization
            customdata=hover_texts,
            hovertemplate='%{customdata}<extra></extra>'
        )
    ))
    
    fig.update_layout(title_text='FortiGate Policy Visualizer', font_size=10, template=theme)
    return fig

st.set_page_config(page_title="FortiGate Policy Visualizer", layout="wide", initial_sidebar_state="collapsed")

# Hide Streamlit menu bar
st.markdown("""
    <style>
        .stAppHeader {display: none;}
    </style>
""", unsafe_allow_html=True)
st.title("FortiGate Policy Visualizer")

# Dark/Light mode toggle
theme = "plotly"

uploaded_file = st.file_uploader("Upload your firewall config file", type=["txt", "conf"])
config_input = st.text_area("Or paste your firewall config here:")

if uploaded_file or config_input:
    if uploaded_file:
        config_text = uploaded_file.getvalue().decode("utf-8")
    else:
        config_text = config_input
    
    valid_config = extract_valid_config(config_text)
    policy_map = parse_firewall_policy(valid_config)
    
    if policy_map:
        fig = generate_sankey(policy_map)
        st.plotly_chart(fig)
    else:
        st.warning("No valid firewall policies found. Ensure your config starts with 'config firewall policy'.")
