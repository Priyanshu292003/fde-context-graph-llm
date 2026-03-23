import pandas as pd
import json
import os
import networkx as nx

# =========================
# 🔹 LOAD FUNCTION
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
# 🔹 LOAD DATA
# =========================
base_path = "sap-o2c-data"

sales_orders = load_jsonl(f"{base_path}/sales_order_headers")
deliveries = load_jsonl(f"{base_path}/outbound_delivery_headers")
invoices = load_jsonl(f"{base_path}/billing_document_headers")

delivery_items = load_jsonl(f"{base_path}/outbound_delivery_items")
invoice_items = load_jsonl(f"{base_path}/billing_document_items")

# =========================
# 🔹 CREATE GRAPH
# =========================
G = nx.DiGraph()

# 🟢 Orders
for _, row in sales_orders.iterrows():
    order_id = row.get('salesOrder')
    if order_id:
        G.add_node(f"ORDER_{order_id}", type="order")

# 🟢 Deliveries
for _, row in deliveries.iterrows():
    delivery_id = row.get('deliveryDocument')
    if delivery_id:
        G.add_node(f"DELIVERY_{delivery_id}", type="delivery")

# 🟢 Invoices
for _, row in invoices.iterrows():
    invoice_id = row.get('billingDocument')
    if invoice_id:
        G.add_node(f"INVOICE_{invoice_id}", type="invoice")

# =========================
# 🔗 ADD EDGES
# =========================

# Order → Delivery
for _, row in delivery_items.iterrows():
    order_id = row.get('referenceSdDocument')
    delivery_id = row.get('deliveryDocument')

    if order_id and delivery_id:
        G.add_edge(
            f"ORDER_{order_id}",
            f"DELIVERY_{delivery_id}",
            relation="delivered"
        )

# Delivery → Invoice
for _, row in invoice_items.iterrows():
    delivery_id = row.get('referenceSdDocument')
    invoice_id = row.get('billingDocument')

    if delivery_id and invoice_id:
        G.add_edge(
            f"DELIVERY_{delivery_id}",
            f"INVOICE_{invoice_id}",
            relation="billed"
        )

# =========================
# 📊 GRAPH INFO
# =========================
print("\n✅ Graph Created Successfully!")
print("Total Nodes:", len(G.nodes))
print("Total Edges:", len(G.edges))

# =========================
# 🔍 QUERY FUNCTIONS
# =========================

# 🔹 1. Trace full flow
def trace_full_flow(graph, start_node):
    if start_node not in graph:
        return "Node not found"

    visited = set()
    result = []

    def dfs(node):
        for neighbor in graph.successors(node):
            edge = (node, neighbor)
            if edge not in visited:
                visited.add(edge)
                result.append(edge)
                dfs(neighbor)

    dfs(start_node)
    return result


# 🔹 2. Find broken orders
def find_broken_orders(graph):
    broken = []

    for node in graph.nodes:
        if node.startswith("ORDER"):
            if len(list(graph.successors(node))) == 0:
                broken.append(node)

    return broken


# 🔹 3. Top orders by deliveries
def top_orders_by_deliveries(graph):
    result = {}

    for node in graph.nodes:
        if node.startswith("ORDER"):
            deliveries = list(graph.successors(node))
            result[node] = len(deliveries)

    return sorted(result.items(), key=lambda x: x[1], reverse=True)[:5]


# =========================
# 🧪 TEST OUTPUTS
# =========================

print("\n🔍 Trace Example:")
print(trace_full_flow(G, "ORDER_740506"))

print("\n❌ Broken Orders (first 10):")
print(find_broken_orders(G)[:10])

print("\n📊 Top Orders by Deliveries:")
print(top_orders_by_deliveries(G))