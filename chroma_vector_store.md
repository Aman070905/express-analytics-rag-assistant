# Chroma Vector Store

Chroma is an open-source vector database that can store embeddings and associated documents and metadata.

## Adding documents

A document usually contains page content and metadata. A vector store can embed document content and store the resulting vectors with metadata. Stable document IDs can be supplied when adding documents to avoid unnecessary duplicate records.

## Similarity search

Similarity search retrieves documents whose embeddings are close to the query embedding. A top-k parameter controls how many candidate documents are returned.

## Metadata

Metadata can store source names, URLs, document types, page numbers, and other provenance information. Keeping source metadata allows applications to show citations alongside generated answers.

## Persistence

A persistent local directory allows a Chroma collection to be reused across application restarts. The embedding model used for queries should be compatible with the model used to index documents.
