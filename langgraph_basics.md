# LangGraph Basics

LangGraph is a library for building stateful, multi-step agent workflows as graphs. A graph consists of state, nodes, and edges.

## StateGraph

`StateGraph` defines the state schema shared by workflow nodes. The state can be represented using a TypedDict. Nodes receive the current state and return updates to it.

## Nodes and edges

A node is a Python function that performs one step and returns a dictionary of state updates. Normal edges define fixed transitions between nodes. Conditional edges choose the next node based on the current state.

## Compiling and invoking

After adding nodes, edges, and an entry point, compile the graph. The compiled graph can be invoked with an initial state. The final state contains the updates produced during execution.

## Retry and routing patterns

A workflow can store a retry counter in its state. A conditional routing function can inspect that counter and route to a rewrite/retrieval path while the retry limit has not been reached. A bounded retry limit prevents infinite loops.

## Human-readable workflow design

Keep each node focused on one responsibility, make state fields explicit, and ensure that failure and fallback paths are represented in the graph rather than hidden inside one large function.
