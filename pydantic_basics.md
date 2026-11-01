# Pydantic Basics

Pydantic is a Python library for data validation and settings management using type annotations.

## Models

A model is a class that inherits from `BaseModel`. Fields are declared using type annotations. When data is validated, Pydantic parses input into the declared types or reports validation errors.

## Field constraints

`Field` can provide metadata and constraints such as minimum length, maximum length, and numeric bounds. These constraints are useful for validating API request payloads.

## Optional fields

An optional field can be declared using a union with `None`, such as `str | None`, and can be given a default value of `None`.

## Serialization

In Pydantic v2, `model_dump()` returns a dictionary representation of a model. This is useful when storing validated request data or converting it to JSON-compatible structures.
