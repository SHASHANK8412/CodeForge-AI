import React, { useCallback, useEffect, useState } from 'react';
import { FaCodeBranch, FaFileContract } from 'react-icons/fa';
import {
  deriveContract, errorsOf, getContract, getContractDiff, listContractVersions, registerContract,
} from '../../services/integrationEngine';

const btn = 'inline-flex items-center gap-1.5 rounded-lg border border-border-dark px-2.5 py-1 text-[11px] text-text-secondary hover:text-white disabled:opacity-40';

/**
 * The project's shared integration contract: its operations and entities, what it leaves unspecified, every version
 * (who registered it and why, breaking or not) and the diff of a version against its parent. A new version is created
 * by deriving it from the generation's architecture or by registering edited JSON with a reason.
 */
export default function ContractPanel({ projectId, onChanged }) {
  const [contract, setContract] = useState(null);
  const [versions, setVersions] = useState([]);
  const [diff, setDiff] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const [c, v] = await Promise.all([getContract(projectId).catch((e) => (e.status === 404 ? null : Promise.reject(e))),
        listContractVersions(projectId)]);
      setContract(c?.contract || null);
      setVersions(v.versions || []);
      setDiff(c?.contract?.parent_version ? await getContractDiff(projectId) : null);
    } catch (e) { setMessage(e?.error || 'Could not load the contract.'); }
    finally { setLoading(false); }
  }, [projectId]);
  useEffect(() => { setContract(null); setDiff(null); setEditing(false); load(); }, [load]);

  const act = async (fn) => {
    setBusy(true); setErrors([]); setMessage('');
    try { await fn(); await load(); onChanged?.(); } catch (e) { setErrors(errorsOf(e)); setMessage(e?.error || 'Request failed.'); }
    finally { setBusy(false); }
  };
  const startEdit = () => {
    const body = contract ? Object.fromEntries(Object.entries(contract).filter(([k]) => !['id', 'project_id', 'version', 'revision',
      'parent_version', 'created_at', 'author', 'reason', 'source'].includes(k))) : { api: { endpoints: [] }, entities: [] };
    setDraft(JSON.stringify(body, null, 2)); setReason(''); setEditing(true);
  };
  const save = () => act(async () => {
    let parsed;
    try { parsed = JSON.parse(draft); } catch (e) { throw Object.assign(new Error('The contract is not valid JSON.'), { error: `The contract is not valid JSON: ${e.message}` }); }
    const r = await registerContract(projectId, parsed, reason);
    setMessage(r.change ? `Registered v${r.contract.version}${r.change.breaking ? ' (breaking change)' : ''}.` : (r.warnings || []).join(' '));
    setEditing(false);
  });

  if (loading && !contract) return <p className="text-xs text-text-muted">Loading the contract…</p>;
  const ops = contract?.api?.endpoints || [];
  const unspec = Object.entries(contract?.unspecified || {}).filter(([, v]) => v?.length);
  return (
    <div className="space-y-3 text-[11px] text-text-secondary">
      <div className="flex flex-wrap items-center gap-2">
        {contract ? <span className="flex items-center gap-1.5 text-text-primary"><FaFileContract className="h-3 w-3" /> v{contract.version}
          <span className="font-mono text-text-muted">{contract.revision}</span> · {contract.source} · {contract.author} · “{contract.reason}”</span>
          : <span className="text-amber-200">No shared contract is registered: compatibility cannot be established without one.</span>}
        <button disabled={busy} className={btn} onClick={() => act(async () => {
          const r = await deriveContract(projectId);
          setMessage(r.change ? `Derived v${r.contract.version} from the architecture.` : (r.warnings || []).join(' '));
        })}>Derive from architecture</button>
        <button disabled={busy} className={btn} onClick={startEdit}>{contract ? 'Edit as new version' : 'Write a contract'}</button>
      </div>
      {message && <p className="text-amber-200">{message}</p>}
      {errors.length > 0 && <ul className="list-disc pl-5 text-rose-200">{errors.map((x) => <li key={x}>{x}</li>)}</ul>}
      {editing && (
        <div className="space-y-2 rounded-lg border border-border-dark p-2">
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} spellCheck={false}
            className="h-72 w-full rounded border border-border-dark bg-bg-base p-2 font-mono text-[11px] text-text-primary outline-none" />
          <div className="flex flex-wrap items-center gap-2">
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for this version (required)"
              className="min-w-[18rem] flex-1 rounded border border-border-dark bg-bg-base px-2 py-1 text-[11px] text-text-primary outline-none" />
            <button disabled={busy || reason.trim().length < 3} className={btn} onClick={save}>Register version</button>
            <button disabled={busy} className={btn} onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>)}
      {contract && (<>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1 pr-3">Operation</th><th className="pr-3">Auth</th>
              <th className="pr-3">Request fields</th><th className="pr-3">Success</th><th>Response fields</th></tr></thead>
            <tbody>{ops.map((e) => {
              const ok = Object.entries(e.responses || {}).find(([k]) => String(k).startsWith('2'));
              const schema = ok?.[1]?.schema;
              const props = schema ? Object.keys((schema.type === 'array' ? schema.items : schema)?.properties || {}) : null;
              return (
                <tr key={`${e.method} ${e.path}`} className="border-t border-border-subtle">
                  <td className="py-1 pr-3 font-mono text-text-primary">{e.method} {e.path}</td><td className="pr-3">{e.auth}</td>
                  <td className="pr-3 font-mono">{Object.keys(e.request_schema?.properties || {}).join(', ') || '—'}</td>
                  <td className="pr-3">{ok?.[0] || '—'}</td>
                  <td className="font-mono">{props ? `${schema.type === 'array' ? '[ ] ' : ''}${props.join(', ') || '{}'}` : 'not specified'}</td>
                </tr>);
            })}</tbody>
          </table>
        </div>
        {contract.entities?.length > 0 && <p><span className="text-text-muted">Entities: </span>{contract.entities.map((x) =>
          `${x.name}(${x.fields.map((f) => `${f.name}${f.primary_key ? '*' : ''}${f.references ? `→${f.references}` : ''}`).join(', ') || 'fields not stated'})`).join(' · ')}</p>}
        {unspec.length > 0 && <p className="text-amber-200/80"><span className="text-text-muted">Not specified (not checked): </span>
          {unspec.map(([k, v]) => `${k}: ${v.join(', ')}`).join(' · ')}</p>}
      </>)}
      {versions.length > 0 && (
        <div><p className="mb-1 flex items-center gap-1 text-[10px] uppercase text-text-muted"><FaCodeBranch className="h-2.5 w-2.5" /> Versions</p>
          <ul className="space-y-0.5">{versions.map((v) => (
            <li key={v.version}>v{v.version} · {new Date(v.created_at).toLocaleString()} · {v.author} · “{v.reason}” · {v.changes} change(s)
              {v.breaking && <span className="ml-1 text-rose-300">breaking</span>}</li>))}</ul></div>)}
      {diff?.items?.length > 0 && (
        <div><p className="mb-1 text-[10px] uppercase text-text-muted">v{diff.from_version} → v{diff.to_version}</p>
          <ul className="space-y-0.5">{diff.items.map((i, k) => (
            <li key={k}><span className={i.breaking ? 'text-rose-300' : 'text-emerald-300'}>{i.breaking ? 'breaking' : 'compatible'}</span>{' '}
              <span className="font-mono">{i.kind}</span> {i.target} — {i.why}{i.affected_components?.length ? ` (affects ${i.affected_components.join(', ')})` : ''}
              {i.affected_code?.length > 0 && <span className="font-mono text-text-muted"> {i.affected_code.join(', ')}</span>}</li>))}</ul></div>)}
    </div>
  );
}
