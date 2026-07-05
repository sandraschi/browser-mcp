export default function ApiDocs() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-zinc-100">API Docs</h1>
      <p className="text-sm text-zinc-500">Backend documentation via Swagger UI and ReDoc.</p>
      <div className="flex gap-3">
        <a href="http://127.0.0.1:10776/docs" target="_blank" rel="noopener noreferrer"
          className="px-4 py-2 rounded-lg bg-amber text-zinc-900 font-medium text-sm hover:bg-amber/90">Swagger UI</a>
        <a href="http://127.0.0.1:10776/redoc" target="_blank" rel="noopener noreferrer"
          className="px-4 py-2 rounded-lg bg-zinc-700 text-zinc-200 font-medium text-sm hover:bg-zinc-600">ReDoc</a>
      </div>
    </div>
  );
}
