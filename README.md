# VaultShare

> A production-oriented file upload and sharing platform built with Django and Django REST Framework.

## Why this project exists

VaultShare was built to explore what a file sharing system designed with production concerns in mind looks like beyond basic CRUD.

The goal was not to build a full SaaS product, but to design a system with clear security boundaries, explicit lifecycle management, and environment-aware behavior — the kinds of concerns that arise in real backend systems.

The project is intentionally scoped to remain inspectable. It can be tested through a minimal UI or directly via a documented API, and is meant to be read as much as it is to be used.

## Overview

VaultShare is a full-stack file upload and sharing platform that supports authenticated file management, time-limited share links with controlled anonymous access, per-user storage limits, and S3-compatible object storage.

The application is deployed with production-style settings and defaults, while remaining easy to run locally without cloud credentials.

## Features

- **Authenticated file management**
  Users can upload, list, and delete files through authenticated endpoints, with server-side validation and per-user constraints.

- **Time-limited share links**
  Files can be shared using expiring links that expose metadata and downloads through controlled anonymous endpoints.

- **Environment-driven lifecycle management**
  Share links always expire, while uploaded files support optional expiration controlled via configuration (e.g. `DEMO_MODE`), with cleanup handled through management commands.

- **Environment-driven upload policy**
  File size limits, type restrictions, and storage behavior are configurable through environment variables.

- **S3-compatible object storage support**
  The system supports local filesystem storage for development and S3-compatible backends (e.g. AWS S3, Cloudflare R2) for deployment.

- **Production-oriented safeguards**
  Request throttling, conservative defaults, and server-side enforcement are applied across the API.

## Architecture & design highlights

- **Explicit lifecycle modeling**
  File uploads and share links model expiration explicitly, with different lifecycle rules applied depending on context. Share links are always time-limited, while uploaded files support optional expiration controlled through configuration. Cleanup is handled via dedicated management commands rather than implicit side effects.

- **Clear access boundaries**
  The system enforces a strict separation between authenticated user operations and anonymous access. All file management actions require authentication, while anonymous access is limited to specific share-link endpoints with constrained behavior.

- **QuerySet- and manager-level domain logic**
  Common domain concerns such as filtering active (non-expired) records are implemented at the QuerySet and manager level, keeping view logic simple and ensuring consistent behavior across the application.

- **Environment-driven behavior**
  Core aspects of the system — including upload limits, storage backend selection, and optional expiration behavior — are controlled through environment variables. This allows the same codebase to support local development, demo deployments, and production-style configurations.

- **Storage abstraction**
  File storage is abstracted behind Django’s storage interface, enabling seamless switching between local filesystem storage and S3-compatible object storage without application-level changes.

- **API-first documentation**
  The API is fully documented using OpenAPI via drf-spectacular, ensuring endpoints, parameters, and responses are explicit and discoverable for both reviewers and consumers.

## Authentication & access model

VaultShare separates access concerns between the web interface and the API.

The web UI uses session-based authentication for user registration, login, and dashboard interactions.
The API uses JWT-based authentication for all user-scoped operations, including file management and share link creation.

Anonymous access is intentionally restricted. Only specific share-link endpoints allow unauthenticated access, and only when the link is valid and unexpired. All other operations require authentication and are subject to server-side enforcement.

## API documentation

VaultShare exposes a RESTful API documented using OpenAPI via drf-spectacular.

The interactive API documentation (Swagger UI) describes available endpoints, request/response schemas, authentication requirements, and error responses. Access to Swagger UI is gated behind authentication through the web interface.

The API is intended to be human-readable and testable, allowing reviewers to explore the system without relying on the UI.

## Local development

VaultShare is designed to run locally with minimal setup and without requiring cloud credentials by default.

### 1. Clone the repository

```bash
git clone https://github.com/Jead100/vaultshare.git
cd vaultshare
````

### 2. Create and activate a virtual environment

> ⚠️ Note: On macOS and Linux, you may need to use `python3` instead of `python`.


```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and adjust values as needed:

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

For local development, the default values in `.env.example` are sufficient.
By default, the application uses local filesystem storage and disables automatic expiration for uploaded files.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver
```

The application will be available at:

```
http://127.0.0.1:8000/
```

Optional features such as S3-compatible storage and demo-mode expirations can be enabled through environment variables.

## Environment configuration

VaultShare is configured primarily through environment variables, allowing the same codebase to support local development, demo deployments, and production-style environments.

Configuration values are grouped by concern and loaded from an `.env` file during local development.

### Core settings
- `DEBUG` – Enable or disable debug mode.
- `SECRET_KEY` – Application secret key.
- `DATABASE_URL` – Database connection string.

### Upload policy
- `MAX_UPLOAD_SIZE` – Maximum allowed file size.
- `ALLOW_ANY_FILE_TYPE` – Toggle file type restrictions.
- `DEFAULT_FILE_TTL_SECONDS` – Default expiration time for uploaded files (set to `0` for no expiration).

### Demo mode
- `DEMO_MODE` – Enables demo-oriented behavior such as automatic file expiration and cleanup.
  When disabled, uploaded files do not expire by default.

### Storage
- `USE_S3` – Enable S3-compatible object storage.
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`

When `USE_S3=False`, VaultShare uses local filesystem storage, allowing the project to run locally without cloud credentials.

## Deployment notes

VaultShare is deployed in a production-style environment and configured to reflect real-world usage patterns.

- The application is hosted on Render.
- A managed PostgreSQL database is used in production.
- File storage is backed by S3-compatible object storage.
- `DEMO_MODE` is enabled in the live deployment to allow automatic expiration and cleanup of uploaded files.

Behavior differences between local development and deployment are controlled through environment variables rather than code changes.

## Scope & limitations

VaultShare is not intended to be a full SaaS file storage product.

The project focuses on backend architecture, API design, and lifecycle management rather than feature completeness or large-scale operational concerns. As such, certain capabilities commonly found in commercial file-sharing platforms are intentionally out of scope.

Notably, VaultShare does not currently include background job processing, virus scanning, or fine-grained access controls beyond its share-link model. These tradeoffs were made to keep the system focused, inspectable, and well-suited for portfolio evaluation.

## Contact

If you’d like to get in touch, feel free to reach me at
ascanoa.jordan@gmail.com or connect with me on LinkedIn.

## Contributing

This project is open source but primarily serves as a personal portfolio project.
If you spot an issue or have a suggestion, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
