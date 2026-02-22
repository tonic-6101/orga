# Contributing to Orga

Thank you for your interest in contributing to Orga! This guide will help you get started.

## Code of Conduct

Be respectful and constructive. We're building something useful together.

## Getting Started

### Prerequisites

- [Frappe Manager](https://github.com/rtCamp/Frappe-Manager) (Docker-based development environment)
- Frappe Framework v15+
- Python 3.10+
- Node.js 18+
- MariaDB 10.6+

### Development Setup

1. **Clone the repository**

   ```bash
   bench get-app orga https://github.com/tonic-6101/orga.git
   bench --site your-site.localhost install-app orga
   ```

2. **Run migrations**

   ```bash
   bench --site your-site.localhost migrate
   ```

3. **Start the frontend dev server**

   All commands must be run **inside the Frappe Manager Docker container**:

   ```bash
   cd apps/orga/frontend
   npm install
   npm run dev
   ```

4. **Access the app** at `https://your-site.localhost/orga`

## How to Contribute

### Reporting Bugs

Open an issue on [GitHub Issues](https://github.com/tonic-6101/orga/issues) with:

- A clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Frappe version and browser info

### Suggesting Features

Open a [GitHub Discussion](https://github.com/tonic-6101/orga/discussions) to propose new features. Please check the existing issues and discussions first to avoid duplicates.

### Submitting Code

1. Fork the repository
2. Create a feature branch from `develop`:
   ```bash
   git checkout -b feature/your-feature develop
   ```
3. Make your changes
4. Test your changes
5. Commit using [conventional commits](#commit-messages)
6. Push and open a Pull Request against `develop`

## Development Guidelines

### Project Structure

| Directory | Purpose |
|-----------|---------|
| `orga/orga/doctype/` | DocType definitions and controllers (Python) |
| `orga/api/` | API endpoints (Python) |
| `frontend/src/pages/` | Vue page components |
| `frontend/src/components/` | Reusable Vue components |
| `frontend/src/composables/` | Vue composition API hooks |
| `frontend/src/types/` | TypeScript type definitions |

### Frontend: TypeScript Only

The frontend uses **TypeScript exclusively**. Do not create `.js` files in `frontend/src/`.

- All Vue components must use `<script setup lang="ts">`
- New files must be `.ts` (not `.js`)
- Avoid `any` types without a justifying comment
- Use existing types from `src/types/orga.ts`

### Backend: Frappe Conventions

- Follow standard Frappe patterns for DocTypes and API endpoints
- Use `@frappe.whitelist()` for API methods
- Validate inputs server-side

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Examples:**
```
feat(tasks): add bulk status update
fix(gantt): correct dependency line rendering
docs(api): document webhook payload format
```

### Running Tests

Inside the Docker container:

```bash
bench run-tests --app orga
```

## Pull Request Process

1. Target the `develop` branch (not `main`)
2. Keep PRs focused — one feature or fix per PR
3. Include a clear description of what changed and why
4. Make sure existing functionality isn't broken
5. Add tests for new backend features when possible

## License

By contributing, you agree that your contributions will be licensed under the [AGPL-3.0 License](LICENSE). All community contributions remain open source — they will never be placed behind a paywall.
