// Absolute backend URL for production (Tauri webview relative fetches resolve
// against tauri://localhost, which cannot reach the backend on 127.0.0.1 --
// see mcp-central-docs/standards/TAURI_PRODUCTION_PITFALLS.md #2).
// Vite dev server proxies '' (relative) to the backend, so this must stay empty in dev.
export const API_BASE = import.meta.env.DEV ? '' : 'http://127.0.0.1:10780';
