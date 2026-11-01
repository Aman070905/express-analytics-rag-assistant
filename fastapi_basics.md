# FastAPI Basics

FastAPI is a Python web framework for building APIs using standard Python type hints. It is built on Starlette for web handling and Pydantic for data validation.

## Path operation decorators

A path operation function is associated with an HTTP method and URL path using decorators such as `@app.get("/")`, `@app.post("/")`, `@app.put("/")`, and `@app.delete("/")`. The function's return value is converted to a response.

## Request body validation

Pydantic models can describe JSON request bodies. FastAPI reads the request body, validates it against the model, and returns a validation error when the input does not match the declared schema.

## Automatic API documentation

FastAPI generates an OpenAPI schema and interactive documentation. The Swagger UI is commonly available at `/docs`, and ReDoc is commonly available at `/redoc`.

## File uploads

File uploads are declared with `File` and `UploadFile`. `UploadFile` uses a spooled temporary file and is generally suitable for larger files than reading all bytes immediately. Multipart form handling requires `python-multipart`.

## Dependency injection

Dependencies are declared with `Depends`. They can be used for shared logic such as authentication, database sessions, and reusable request-related services.
