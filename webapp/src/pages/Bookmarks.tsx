import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Folder,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { callTool } from '../lib/mcp';
import BookmarkDetail from './BookmarkDetail';

interface Source {
  available: boolean;
  path?: string | null;
}

interface Bookmark {
  id?: string;
  title?: string;
  name?: string;
  url?: string;
  parent?: string;
  date_added?: number;
  tags?: string[];
}

const BROWSERS = [
  { id: 'chrome', label: 'Chrome' },
  { id: 'edge', label: 'Edge' },
  { id: 'brave', label: 'Brave' },
  { id: 'firefox', label: 'Firefox' },
];

const PAGE_SIZES = [25, 50, 100, 200];
const SORTS = [
  { id: 'title-asc', label: 'Title A-Z' },
  { id: 'title-desc', label: 'Title Z-A' },
  { id: 'date-new', label: 'Newest first' },
  { id: 'date-old', label: 'Oldest first' },
  { id: 'folder', label: 'Folder' },
];

const btn =
  'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50';
const inputCls =
  'bg-zinc-800 border border-zinc-600 text-zinc-100 px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber placeholder-zinc-500';

function sortBookmarks(a: Bookmark, b: Bookmark, id: string): number {
  const titleA = a.title || a.name || a.url || '';
  const titleB = b.title || b.name || b.url || '';
  switch (id) {
    case 'title-desc':
      return titleB.localeCompare(titleA);
    case 'date-new':
      return (b.date_added || 0) - (a.date_added || 0);
    case 'date-old':
      return (a.date_added || 0) - (b.date_added || 0);
    case 'folder':
      return (a.parent || '').localeCompare(b.parent || '');
    default:
      return titleA.localeCompare(titleB);
  }
}

export default function Bookmarks() {
  const [browser, setBrowser] = useState('chrome');
  const [sources, setSources] = useState<Record<string, Source> | null>(null);
  const [all, setAll] = useState<Bookmark[]>([]);
  const [tagsList, setTagsList] = useState<Array<{ tag: string; count: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [folder, setFolder] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [sort, setSort] = useState('title-asc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const [showAdd, setShowAdd] = useState(false);
  const [addUrl, setAddUrl] = useState('');
  const [addTitle, setAddTitle] = useState('');
  const [addFolder, setAddFolder] = useState('');
  const [confirmUrl, setConfirmUrl] = useState<string | null>(null);
  const [editUrl, setEditUrl] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState('');
  const [detail, setDetail] = useState<Bookmark | null>(null);

  useEffect(() => {
    fetch('/api/bookmarks/sources')
      .then((r) => r.json())
      .then((d) => {
        const s = (d.sources || {}) as Record<string, Source>;
        setSources(s);
        const first = BROWSERS.find((b) => s[b.id]?.available);
        if (first) setBrowser(first.id);
      })
      .catch(() => setSources({}));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, tagRes] = await Promise.all([
        fetch(`/api/bookmarks?browser=${encodeURIComponent(browser)}`).then((r) => r.json()),
        fetch('/api/bookmarks/tags').then((r) => r.json()),
      ]);
      const allItems: Bookmark[] = listRes.bookmarks || [];
      const tagMap: Record<string, string[]> = tagRes.tag_map || {};
      setAll(allItems.map((b) => ({ ...b, tags: (b.url && tagMap[b.url]) || [] })));
      setTagsList((tagRes.tags || []).map((t: { tag: string; count: number }) => t));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAll([]);
    } finally {
      setLoading(false);
    }
  }, [browser]);

  useEffect(() => {
    if (sources === null) return;
    if (sources[browser]?.available === false) {
      setAll([]);
      return;
    }
    load();
  }, [sources, browser, load]);

  const selectedUnavailable = sources !== null && sources[browser]?.available === false;
  const availableCount = sources ? Object.values(sources).filter((s) => s.available).length : null;

  const folders = useMemo(() => {
    const set = new Set<string>();
    for (const b of all) if (b.parent) set.add(b.parent);
    return [...set].sort();
  }, [all]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return all.filter((b) => {
      const title = (b.title || b.name || '').toLowerCase();
      const url = (b.url || '').toLowerCase();
      if (q && !title.includes(q) && !url.includes(q)) return false;
      if (folder && (b.parent || '') !== folder) return false;
      if (tagFilter && !(b.tags || []).includes(tagFilter)) return false;
      return true;
    });
  }, [all, query, folder, tagFilter]);

  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => sortBookmarks(a, b, sort));
    return copy;
  }, [filtered, sort]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const paged = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, currentPage, pageSize]);

  const resetFilters = () => {
    setQuery('');
    setFolder('');
    setTagFilter('');
    setSort('title-asc');
    setPage(1);
  };

  const addBookmark = async () => {
    const url = addUrl.trim();
    if (!url) return;
    setBusy(true);
    setError(null);
    try {
      await callTool('browser_bookmarks', {
        operation: 'add_bookmark',
        browser,
        url,
        title: addTitle.trim() || url,
        ...(addFolder.trim() ? { folder: addFolder.trim() } : {}),
      });
      setAddUrl('');
      setAddTitle('');
      setAddFolder('');
      setShowAdd(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const removeBookmark = async (url: string) => {
    setBusy(true);
    setError(null);
    try {
      await callTool('browser_bookmarks', { operation: 'delete_bookmark', browser, url });
      setConfirmUrl(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const saveRename = async () => {
    if (!editUrl) return;
    setBusy(true);
    setError(null);
    try {
      await callTool('browser_bookmarks', {
        operation: 'edit_bookmark',
        browser,
        url: editUrl,
        new_title: draftTitle,
      });
      setEditUrl(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const start = (currentPage - 1) * pageSize + 1;
  const end = Math.min(currentPage * pageSize, sorted.length);

  return (
    <div data-testid="bookmarks-page" className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-zinc-100">Bookmarks</h2>
        {availableCount !== null && (
          <span className="text-sm text-zinc-400" data-testid="bookmarks-source-count">
            {availableCount} of {BROWSERS.length} browsers have a readable bookmark source
          </span>
        )}
      </div>

      {selectedUnavailable && (
        <div
          className="flex items-start gap-2 bg-amber/10 border border-amber/30 text-amber-200 text-sm rounded-lg p-3"
          data-testid="bookmarks-no-source-warning"
        >
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <p>
            No bookmark source detected for <strong>{BROWSERS.find((b) => b.id === browser)?.label}</strong>. Open the
            browser once so it creates its bookmarks file, then retry, or pick another browser below.
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={browser}
          onChange={(e) => setBrowser(e.target.value)}
          data-testid="bookmarks-browser-select"
          className="bg-zinc-800 border border-zinc-600 text-zinc-100 px-3 py-2 rounded-lg text-sm focus:outline-none"
        >
          {BROWSERS.map((b) => {
            const avail = sources?.[b.id]?.available;
            const disabled = sources !== null && avail !== true;
            return (
              <option key={b.id} value={b.id} disabled={disabled}>
                {b.label}
                {disabled ? ' (no source)' : ''}
              </option>
            );
          })}
        </select>

        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search title or URL..."
            data-testid="bookmarks-search"
            className={`${inputCls} w-full pl-8`}
          />
        </div>

        <select
          value={folder}
          onChange={(e) => {
            setFolder(e.target.value);
            setPage(1);
          }}
          data-testid="bookmarks-folder-filter"
          className="bg-zinc-800 border border-zinc-600 text-zinc-100 px-2 py-2 rounded-lg text-sm focus:outline-none"
        >
          <option value="">All folders</option>
          {folders.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>

        <select
          value={tagFilter}
          onChange={(e) => {
            setTagFilter(e.target.value);
            setPage(1);
          }}
          data-testid="bookmarks-tag-filter"
          className="bg-zinc-800 border border-zinc-600 text-zinc-100 px-2 py-2 rounded-lg text-sm focus:outline-none"
        >
          <option value="">All tags</option>
          {tagsList.map((t) => (
            <option key={t.tag} value={t.tag}>
              {t.tag} ({t.count})
            </option>
          ))}
        </select>

        <select
          value={sort}
          onChange={(e) => {
            setSort(e.target.value);
            setPage(1);
          }}
          data-testid="bookmarks-sort"
          className="bg-zinc-800 border border-zinc-600 text-zinc-100 px-2 py-2 rounded-lg text-sm focus:outline-none"
        >
          {SORTS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => setShowAdd((v) => !v)}
          disabled={busy || selectedUnavailable}
          className={`${btn} bg-emerald-600 text-white hover:bg-emerald-500`}
          data-testid="bookmarks-add-toggle"
        >
          <Plus size={14} />
          Add
        </button>
        <button
          type="button"
          onClick={load}
          disabled={loading || busy || selectedUnavailable}
          className={`${btn} bg-amber text-zinc-900 hover:bg-amber/90`}
          data-testid="bookmarks-list-button"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Loading...' : 'Refresh'}
        </button>
        {(query || folder || tagFilter || sort !== 'title-asc') && (
          <button type="button" onClick={resetFilters} className={`${btn} bg-zinc-800 text-zinc-300 hover:bg-zinc-700`}>
            <X size={14} />
            Clear
          </button>
        )}
      </div>

      {showAdd && (
        <div
          className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4 space-y-3"
          data-testid="bookmarks-add-form"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-zinc-200">
              Add bookmark to {BROWSERS.find((b) => b.id === browser)?.label}
            </p>
            <button type="button" onClick={() => setShowAdd(false)} className="text-zinc-400 hover:text-zinc-100">
              <X size={16} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              value={addUrl}
              onChange={(e) => setAddUrl(e.target.value)}
              placeholder="URL (required)"
              data-testid="bookmarks-add-url"
              className={inputCls}
            />
            <input
              value={addTitle}
              onChange={(e) => setAddTitle(e.target.value)}
              placeholder="Title"
              data-testid="bookmarks-add-title"
              className={inputCls}
            />
            <input
              value={addFolder}
              onChange={(e) => setAddFolder(e.target.value)}
              placeholder="Folder (optional)"
              data-testid="bookmarks-add-folder"
              className={inputCls}
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className={`${btn} bg-zinc-800 text-zinc-300 hover:bg-zinc-700`}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={addBookmark}
              disabled={busy || !addUrl.trim()}
              className={`${btn} bg-emerald-600 text-white hover:bg-emerald-500`}
              data-testid="bookmarks-add-submit"
            >
              {busy ? 'Saving...' : 'Add bookmark'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div
          className="bg-red-900/50 border border-red-700/50 text-red-300 text-sm rounded-lg p-3"
          data-testid="bookmarks-error"
        >
          {error}
        </div>
      )}

      {!loading && !error && !selectedUnavailable && (
        <p className="text-sm text-zinc-400">
          {sorted.length === 0
            ? 'No bookmarks match the current filters.'
            : `Showing ${start}-${end} of ${sorted.length}`}
          {tagFilter ? ` (tagged "${tagFilter}")` : ''}
          {folder ? ` in "${folder}"` : ''}
        </p>
      )}

      {!loading && !error && all.length === 0 && !selectedUnavailable && (
        <p className="text-zinc-400">No bookmarks found. Add one with the Add button.</p>
      )}

      {paged.length > 0 && (
        <div
          className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg overflow-hidden"
          data-testid="bookmarks-list"
        >
          <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2 text-xs text-zinc-500 border-b border-zinc-700/50">
            <span className="col-span-5">Title</span>
            <span className="col-span-2">Folder</span>
            <span className="col-span-2">Added</span>
            <span className="col-span-2">Tags</span>
            <span className="col-span-1 text-right">Actions</span>
          </div>
          {paged.map((bm) => {
            const url = bm.url || '';
            const title = bm.title || bm.name || url;
            const age = bm.date_added ? ageLabel(bm.date_added) : '—';
            return (
              <div
                key={url || bm.id || title}
                className="grid grid-cols-1 md:grid-cols-12 gap-2 px-4 py-2.5 border-b border-zinc-800/50 hover:bg-zinc-800/40 items-center"
                data-testid="bookmarks-item"
              >
                <div className="col-span-5 min-w-0">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setDetail(bm)}
                      className="text-amber font-medium truncate hover:underline text-left"
                      data-testid="bookmark-open-detail"
                    >
                      {title}
                    </button>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-zinc-500 hover:text-zinc-300 shrink-0"
                      title="Open"
                    >
                      <ExternalLink size={12} />
                    </a>
                  </div>
                  <p className="text-xs text-zinc-500 truncate">{url}</p>
                </div>
                <div className="col-span-2 flex items-center gap-1 text-sm text-zinc-400 truncate">
                  {bm.parent && <Folder size={12} className="shrink-0" />}
                  <span className="truncate">{bm.parent || '(root)'}</span>
                </div>
                <div className="col-span-2 text-sm text-zinc-400" data-testid="bookmark-age">
                  {age}
                </div>
                <div className="col-span-2 flex flex-wrap gap-1">
                  {(bm.tags || []).slice(0, 3).map((t) => (
                    <span key={t} className="text-xs bg-zinc-700/60 text-zinc-300 px-1.5 py-0.5 rounded-full">
                      {t}
                    </span>
                  ))}
                  {(bm.tags || []).length > 3 && (
                    <span className="text-xs text-zinc-500">+{(bm.tags || []).length - 3}</span>
                  )}
                </div>
                <div className="col-span-1 flex items-center justify-end gap-1">
                  <button
                    type="button"
                    onClick={() => {
                      setEditUrl(url);
                      setDraftTitle(title);
                    }}
                    disabled={busy}
                    className="p-1.5 rounded text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700"
                    title="Rename"
                    data-testid="bookmarks-edit"
                  >
                    <Pencil size={14} />
                  </button>
                  {confirmUrl === url ? (
                    <button
                      type="button"
                      onClick={() => removeBookmark(url)}
                      disabled={busy}
                      className="px-2 py-1 rounded bg-red-600 text-white text-xs hover:bg-red-500"
                      data-testid="bookmarks-delete-confirm"
                    >
                      Confirm
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setConfirmUrl(url)}
                      disabled={busy}
                      className="p-1.5 rounded text-zinc-400 hover:text-red-400 hover:bg-zinc-700"
                      title="Delete"
                      data-testid="bookmarks-delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {editUrl && (
        <div
          className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4 space-y-2"
          data-testid="bookmarks-edit-form"
        >
          <p className="text-sm text-zinc-300">Rename</p>
          <div className="flex gap-2">
            <input
              value={draftTitle}
              onChange={(e) => setDraftTitle(e.target.value)}
              className={`${inputCls} flex-1`}
              data-testid="bookmarks-edit-input"
            />
            <button
              type="button"
              onClick={saveRename}
              disabled={busy}
              className={`${btn} bg-amber text-zinc-900 hover:bg-amber/90`}
              data-testid="bookmarks-edit-save"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => setEditUrl(null)}
              className={`${btn} bg-zinc-800 text-zinc-300 hover:bg-zinc-700`}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {sorted.length > 0 && (
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            Rows per page
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              data-testid="bookmarks-page-size"
              className="bg-zinc-800 border border-zinc-600 text-zinc-100 px-2 py-1 rounded text-sm"
            >
              {PAGE_SIZES.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1.5 rounded text-zinc-400 hover:bg-zinc-800 disabled:opacity-30"
              data-testid="bookmarks-prev"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm text-zinc-400">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="p-1.5 rounded text-zinc-400 hover:bg-zinc-800 disabled:opacity-30"
              data-testid="bookmarks-next"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {detail && (
        <BookmarkDetail bookmark={detail} browser={browser} onClose={() => setDetail(null)} onChanged={() => load()} />
      )}
    </div>
  );
}

function ageLabel(epoch: number): string {
  if (!epoch) return 'unknown';
  const ageSec = Date.now() / 1000 - epoch;
  if (ageSec < 0) return 'future date';
  const days = Math.floor(ageSec / 86400);
  if (days < 1) return 'today';
  if (days < 30) return `${days}d`;
  if (days < 365) return `${Math.floor(days / 30)}mo`;
  const years = Math.floor(days / 365);
  const rem = Math.floor((days % 365) / 30);
  return `${years}y${rem ? ` ${rem}m` : ''}`;
}
