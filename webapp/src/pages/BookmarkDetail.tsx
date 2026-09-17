import { AlertTriangle, CheckCircle2, ExternalLink, Loader2, Trash2, X, XCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { callTool } from '../lib/mcp';

interface Bookmark {
  id?: string;
  title?: string;
  name?: string;
  url?: string;
  parent?: string;
  date_added?: number;
  tags?: string[];
}

interface LinkCheck {
  exists?: boolean;
  status?: number;
  error?: string;
}

function ageLabel(epoch: number): string {
  if (!epoch) return 'unknown';
  const ageSec = Date.now() / 1000 - epoch;
  if (ageSec < 0) return 'future date';
  const days = Math.floor(ageSec / 86400);
  if (days < 1) return 'added today';
  if (days < 30) return `added ${days}d ago`;
  if (days < 365) return `added ${Math.floor(days / 30)}mo ago`;
  const years = Math.floor(days / 365);
  const rem = Math.floor((days % 365) / 30);
  return `added ${years}yr${rem ? ` ${rem}mo` : ''} ago`;
}

const inputCls =
  'bg-zinc-800 border border-zinc-600 text-zinc-100 px-2 py-1.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber placeholder-zinc-500';

export default function BookmarkDetail({
  bookmark,
  browser,
  onClose,
  onChanged,
}: {
  bookmark: Bookmark;
  browser: string;
  onClose: () => void;
  onChanged: () => void;
}) {
  const url = bookmark.url || '';
  const [link, setLink] = useState<LinkCheck | null>(null);
  const [checking, setChecking] = useState(false);
  const [tags, setTags] = useState<string[]>(bookmark.tags || []);
  const [tagInput, setTagInput] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  const checkLink = useCallback(async () => {
    setChecking(true);
    setLink(null);
    try {
      const data = await callTool('browser_bookmarks', { operation: 'check_link', browser, url });
      setLink({ exists: data.exists, status: data.status, error: data.error });
    } catch {
      setLink({ exists: false, error: 'check failed' });
    } finally {
      setChecking(false);
    }
  }, [browser, url]);

  useEffect(() => {
    if (url) checkLink();
  }, [url, checkLink]);

  const addTag = async () => {
    const t = tagInput.trim().toLowerCase();
    if (!t || tags.includes(t)) return;
    const next = [...tags, t].sort();
    setTags(next);
    setTagInput('');
    setBusy(true);
    try {
      await callTool('browser_bookmarks', { operation: 'set_tags', browser, url, tags: next });
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const removeTag = async (t: string) => {
    const next = tags.filter((x) => x !== t);
    setTags(next);
    setBusy(true);
    try {
      await callTool('browser_bookmarks', { operation: 'set_tags', browser, url, tags: next });
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const removeBookmark = async () => {
    setBusy(true);
    try {
      await callTool('browser_bookmarks', { operation: 'delete_bookmark', browser, url });
      onChanged();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Bookmark details"
        className="bg-zinc-900 border border-zinc-600 rounded-lg shadow-xl max-w-lg w-full max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
        data-testid="bookmark-detail"
      >
        <div className="flex items-center justify-between p-4 border-b border-zinc-600">
          <h3 className="text-lg font-semibold text-amber truncate">{bookmark.title || bookmark.name || url}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-white"
            data-testid="bookmark-detail-close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-4 overflow-auto space-y-4 text-sm">
          <div>
            <p className="text-zinc-500 text-xs mb-1">URL</p>
            <a href={url} target="_blank" rel="noopener noreferrer" className="text-amber hover:underline break-all">
              {url}
            </a>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-zinc-500 text-xs mb-1">Folder</p>
              <p className="text-zinc-200">{bookmark.parent || '(root)'}</p>
            </div>
            <div>
              <p className="text-zinc-500 text-xs mb-1">Age</p>
              <p className="text-zinc-200" data-testid="bookmark-detail-age">
                {ageLabel(bookmark.date_added || 0)}
              </p>
              {bookmark.date_added ? (
                <p className="text-zinc-500 text-xs mt-0.5">
                  {new Date(bookmark.date_added * 1000).toLocaleDateString()}
                </p>
              ) : null}
            </div>
          </div>

          <div>
            <p className="text-zinc-500 text-xs mb-1">Link status</p>
            <div data-testid="bookmark-detail-link">
              {checking ? (
                <span className="inline-flex items-center gap-2 text-zinc-400">
                  <Loader2 size={14} className="animate-spin" /> Checking...
                </span>
              ) : link === null ? (
                <span className="text-zinc-400">Not checked</span>
              ) : link.exists ? (
                <span className="inline-flex items-center gap-2 text-green-400">
                  <CheckCircle2 size={14} /> Reachable (HTTP {link.status})
                </span>
              ) : (
                <span className="inline-flex items-center gap-2 text-red-400">
                  {link.status ? <XCircle size={14} /> : <AlertTriangle size={14} />}
                  {link.status ? `Unreachable (HTTP ${link.status})` : link.error || 'Unreachable'}
                </span>
              )}
            </div>
          </div>

          <div>
            <p className="text-zinc-500 text-xs mb-1">Tags</p>
            <div className="flex flex-wrap gap-1.5 mb-2" data-testid="bookmark-detail-tags">
              {tags.length === 0 && <span className="text-zinc-500 text-sm">No tags</span>}
              {tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 bg-zinc-700 text-zinc-200 text-xs px-2 py-0.5 rounded-full"
                >
                  {t}
                  <button
                    type="button"
                    onClick={() => removeTag(t)}
                    disabled={busy}
                    className="text-zinc-400 hover:text-red-400"
                    aria-label={`Remove tag ${t}`}
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag()}
                placeholder="Add tag..."
                className={`${inputCls} flex-1`}
                data-testid="bookmark-detail-tag-input"
              />
              <button
                type="button"
                onClick={addTag}
                disabled={busy || !tagInput.trim()}
                className="bg-amber text-zinc-900 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-amber/90 disabled:opacity-50"
                data-testid="bookmark-detail-tag-add"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 p-4 border-t border-zinc-600">
          <div>
            {confirmDelete ? (
              <div className="flex items-center gap-2">
                <span className="text-red-400 text-xs">Delete?</span>
                <button
                  type="button"
                  onClick={removeBookmark}
                  disabled={busy}
                  className="bg-red-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-red-500"
                  data-testid="bookmark-detail-delete-confirm"
                >
                  Confirm
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmDelete(false)}
                  className="text-zinc-400 hover:text-zinc-200 text-sm"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmDelete(true)}
                className="inline-flex items-center gap-1 text-zinc-400 hover:text-red-400 text-sm"
                data-testid="bookmark-detail-delete"
              >
                <Trash2 size={14} /> Delete
              </button>
            )}
          </div>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-amber text-zinc-900 px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber/90"
          >
            <ExternalLink size={14} /> Open
          </a>
        </div>
      </div>
    </div>
  );
}
