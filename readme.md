# Order-to-Cash Graph Explorer

## 🚀 Overview
This project builds a context graph from SAP Order-to-Cash data and enables natural language querying over it.

## 🧠 Problem
Enterprise data is fragmented across multiple tables (orders, deliveries, invoices), making it hard to trace relationships.

## 💡 Solution
We:
- Converted structured data into a graph
- Built a query system on top of it
- Enabled natural language interaction via a chat UI

---

## 🏗️ Architecture

- **Backend:** Python, NetworkX
- **Frontend:** Streamlit
- **Data Source:** SAP O2C dataset

---

## 🔗 Graph Model

Nodes:
- Orders
- Deliveries
- Invoices

Edges:
- Order → Delivery
- Delivery → Invoice

### 🔥 Key Insight:
Relationships were derived from **item-level tables**, not headers.

---

## 🔍 Features

- Trace full order flow
- Identify broken orders
- Top orders by activity
- Chat-based interface

---

## 💬 Example Queries

- `trace order 740506`
- `show broken orders`
- `top orders`

---

## 🛡️ Guardrails

The system restricts responses to dataset-related queries only.

---

## ⚖️ Trade-offs

- Used NetworkX instead of Neo4j for simplicity
- Rule-based query parsing instead of full LLM pipeline (can be extended)

---

## 🚀 Future Improvements

- LLM-based query interpretation
- Graph visualization (Cytoscape)
- Node highlighting
- Advanced analytics

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python -m streamlit run app.py