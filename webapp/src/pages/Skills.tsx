import { useEffect, useState } from 'react';

interface Skill {
  name: string;
  description?: string;
  content?: string;
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/skills')
      .then((r) => r.json())
      .then((d) => {
        setSkills(Array.isArray(d.skills) ? d.skills : []);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load skills'));
  }, []);

  const active = skills?.find((s) => s.name === selected);

  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-100 mb-4">Skills</h1>
      {error && <p className="text-sm text-red-400 mb-4">Failed to load skills: {error}</p>}
      {!error && skills === null && <p className="text-zinc-400 text-sm">Loading...</p>}
      {!error && skills !== null && skills.length === 0 && (
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-6">
          <p className="text-zinc-300 text-sm">No skills are currently registered by this server.</p>
          <p className="text-zinc-400 text-sm mt-2">
            Skills surface bundled workflows as markdown so agents know how to use the server. This server ships its
            tool guidance in llms-full.txt instead.
          </p>
        </div>
      )}
      {skills !== null && skills.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            {skills.map((s) => (
              <button
                key={s.name}
                type="button"
                onClick={() => setSelected(s.name)}
                className={`w-full text-left px-3 py-2 rounded-lg border text-sm transition-colors ${selected === s.name ? 'bg-amber/20 border-amber/40 text-amber' : 'bg-zinc-800/50 border-zinc-700/50 text-zinc-300 hover:bg-zinc-800'}`}
              >
                {s.name}
              </button>
            ))}
          </div>
          <div className="md:col-span-2 bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4 whitespace-pre-wrap text-sm text-zinc-300">
            {active ? (
              active.content || active.description || '(no content)'
            ) : (
              <span className="text-zinc-400">Select a skill to view its content.</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
