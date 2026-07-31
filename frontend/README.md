# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  # Expense Tracker - Frontend

  The frontend is a React and TypeScript single-page application built with Vite. It calls the FastAPI backend using `VITE_API_BASE_URL`.

  ## Run locally

  From `frontend/`:

  ```powershell
  npm install
  $env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
  npm run dev
  ```

  Open http://localhost:5173.

  Useful commands:

  ```powershell
  npm run lint
  npm run build
  npm run preview
  ```

  ## Run with Docker

  The root `docker-compose.yml` builds the frontend as static files and serves them with Nginx. From the project root:

  ```powershell
  docker compose up --build
  ```

  Open http://localhost:5173. The frontend container uses `http://localhost:8000` for the backend by default. To use another host-facing backend URL, set `VITE_API_BASE_URL` before building:

  ```powershell
  $env:VITE_API_BASE_URL = "http://localhost:8000"
  docker compose up --build
  ```

  Stop the containers with `Ctrl+C`, or run `docker compose down` from another terminal. The frontend image uses an Nginx SPA fallback so client-side routes continue to work after refresh.
      // Enable lint rules for React
