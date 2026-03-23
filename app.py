import streamlit as st
import networkx as nx
import pandas as pd
import json
import os
from groq import Groq

# =========================
# 🔑 LOAD API KEY (LOCAL + STREAMLIT)
# =========================
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

# =========================
# LOAD FUNCTION
# =========================
def load_jsonl(folder_path):
    data = []
    for file in os.listdir(folder_path):
        if file.endswith(".jsonl"):
            with open(os.path.join(folder_path, file)) as f:
                for line in f:
                    data.append(json.loads(line))
    return pd.DataFrame(data)

# =========================
# LOAD DATA
# =========================
base_path = "sap-o2c-data"

sales_orders = load_jsonl(f"{base_path}/sales_order_headers")
deliveries = load_jsonl(f"{base_path}/outbound_delivery_headers")
invoices = load_jsonl(f"{base_path}/billing_document_headers")

delivery_items = load_jsonl(f"{base_path}/outbound_delivery_items")
invoice_items = load_jsonl(f"{base_path}/billing_document_items")

# =========================
# BUILD GRAPH
# =========================
G = nx.DiGraph()

for _, row in sales_orders.iterrows():
    if row.get('salesOrder'):
        G.add_node(f"ORDER_{row['salesOrder']}")

for _, row in deliveries.iterrows():
    if row.get('deliveryDocument'):
        G.add_node(f"DELIVERY_{row['deliveryDocument']}")

for _, row in invoices.iterrows():
    if row.get('billingDocument'):
        G.add_node(f"INVOICE_{row['billingDocument']}")

# Edges
for _, row in delivery_items.iterrows():
    if row.get('referenceSdDocument') and row.get('deliveryDocument'):
        G.add_edge(
            f"ORDER_{row['referenceSdDocument']}",
            f"DELIVERY_{row['deliveryDocument']}"
        )

for _, row in invoice_items.iterrows():
    if row.get('referenceSdDocument') and row.get('billingDocument'):
        G.add_edge(
            f"DELIVERY_{row['referenceSdDocument']}",
            f"INVOICE_{row['billingDocument']}"
        )

# =========================
# QUERY FUNCTIONS
# =========================

def trace_flow(order_id):
    node = f"ORDER_{order_id}"
    result = []

    if node not in G:
        return ["❌ Order not found in dataset"]

    while True:
        neighbors = list(G.successors(node))
        if not neighbors:
            break
        next_node = neighbors[0]
        result.append(f"{node} → {next_node}")
        node = next_node

    return result


def broken_orders():
    result = []
    for node in G.nodes:
        if node.startswith("ORDER"):
            if len(list(G.successors(node))) == 0:
                result.append(node)
    return result[:10]


def top_orders():
    result = {}
    for node in G.nodes:
        if node.startswith("ORDER"):
            result[node] = len(list(G.successors(node)))

    return sorted(result.items(), key=lambda x: x[1], reverse=True)[:5]


# =========================
# LLM FUNCTIONS
# =========================

def interpret_query_with_llm(user_query):
    prompt = f"""
    You are a system that converts user queries into actions.

    Available actions:
    - TRACE_ORDER
    - FIND_BROKEN_ORDERS
    - TOP_ORDERS

    Extract:
    - action
    - order_id (if present)

    User Query: {user_query}

    Output format:
    action: <ACTION>
    order_id: <ID or NONE>
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def parse_llm_output(output):
    action = ""
    order_id = None

    for line in output.split("\n"):
        if "action" in line.lower():
            action = line.split(":")[-1].strip().upper().replace(" ", "_")
        if "order_id" in line.lower():
            order_id = line.split(":")[-1].strip()

    return action, order_id


# =========================
# UI
# =========================

st.info("This system explores SAP Order-to-Cash data using a graph + LLM interface.")

st.title("📊 Order-to-Cash Graph Explorer")

st.markdown("### 💬 Try queries like:")
st.code("trace order 740506")
st.code("show broken orders")
st.code("top orders")

query = st.text_input("Ask a question:")

if query:
    try:
        with st.spinner("Processing query..."):
            llm_output = interpret_query_with_llm(query)
            action, order_id = parse_llm_output(llm_output)

        query_lower = query.lower()

        # 🔥 PRIMARY (LLM)
        if action and "TRACE" in action and order_id and order_id != "NONE":
            flow = trace_flow(order_id)
            st.success("📦 Order Flow:\n\n" + "\n➡️ ".join(flow))

        elif action and "BROKEN" in action:
            st.error("❌ Broken Orders:")
            st.write(broken_orders())

        elif action and "TOP" in action:
            st.info("📊 Top Orders:")
            st.write(top_orders())

        # 🔥 FALLBACK (RULE-BASED — VERY IMPORTANT)
        elif "trace" in query_lower:
            order_id = ''.join(filter(str.isdigit, query))
            flow = trace_flow(order_id)
            st.success("📦 Order Flow:\n\n" + "\n➡️ ".join(flow))

        elif "broken" in query_lower:
            st.error("❌ Broken Orders:")
            st.write(broken_orders())

        elif "top" in query_lower:
            st.info("📊 Top Orders:")
            st.write(top_orders())

        else:
            st.warning("⚠️ This system only supports dataset-related queries.")

    except Exception as e:
        st.error(f"Error: {str(e)}")