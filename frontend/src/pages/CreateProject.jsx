import React, { useEffect, useMemo, useState } from 'react';
import { FaArrowLeft, FaArrowRight, FaSpinner, FaShieldAlt, FaVial, FaTools, FaUserCheck } from 'react-icons/fa';
import { createGeneration, listTemplates } from '../services/generation';
import { fetchInstalledModels } from '../services/models';

const PENDING_PROMPT_KEY = 'aiforge_pending_prompt';

const EXAMPLES = [
  {
    label: 'Task tracker',
    name: 'Task Tracker',
    text: 'Build a task tracker. Users can create projects, add tasks with a title, due date and priority, mark tasks done, and filter by status.',
  },
  {
    label: 'Recipe box',
    name: 'Recipe Box',
    text: 'Build a recipe box. Users can add recipes with ingredients and steps, search by ingredient, and delete recipes.',
  },
  {
    label: 'Expense tracker',
    name: 'Expense Tracker',
    text: 'Build an expense tracker. Users record expenses with an amount, category and date, and see monthly totals per category.',
  },
];

const FEATURES = [
  { key: 'authentication', label: 'User accounts', hint: 'Sign-up, login and protected routes' },
  { key: 'docker', label: 'Docker setup', hint: 'Dockerfile and docker-compose' },
  { key: 'documentation', label: 'README & API docs', hint: 'Setup and endpoint reference' },
];

const ALWAYS_ON = [
  { Icon: FaUserCheck, text: 'You approve the architecture before code is written' },
  { Icon: FaShieldAlt, text: 'Code review and a security scan on every file' },
  { Icon: FaVial, text: 'Generated tests are run against the code' },
  { Icon: FaTools, text: 'Failing tests trigger debug → patch → re-test' },
];

/** A readable project name from the first words of the description. */
function suggestName(text) {
  const filler = new Set(['a', 'an', 'the', 'build', 'create', 'make', 'me', 'simple', 'my', 'new']);
  // "Build a recipe box where users can..." -> "Recipe Box": stop at the first clause break.
  const head = text.split(/[.,;:]|\s(?:where|with|that|which|for|to|so|using|in)\s/i)[0] || '';
  const words = (head.match(/[A-Za-z0-9]+/g) || []).filter((w) => !filler.has(w.toLowerCase()));
  return words.slice(0, 3).map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
}

function Switch({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full transition cursor-pointer ${checked ? 'bg-accent-violet' : 'bg-surface-hover'}`}
    >
      <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${checked ? 'left-[18px]' : 'left-0.5'}`} />
    </button>
  );
}

export default function CreateProject({ setView, onGenerateSuccess }) {
  // Read the prompt handed over from the dashboard without consuming it here: React runs state
  // initializers twice in development, so removing it in the initializer would lose it.
  const [description, setDescription] = useState(() => sessionStorage.getItem(PENDING_PROMPT_KEY) || '');
  useEffect(() => { sessionStorage.removeItem(PENDING_PROMPT_KEY); }, []);

  const [projectName, setProjectName] = useState('');
  const [templates, setTemplates] = useState([]);
  const [templatesError, setTemplatesError] = useState('');
  const [template, setTemplate] = useState('fastapi-react');
  const selected = templates.find((t) => t.id === template);
  const [features, setFeatures] = useState({ authentication: false, docker: true, documentation: true });
  const [engine, setEngine] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetchInstalledModels().then((res) => !cancelled && setEngine(res));
    return () => { cancelled = true; };
  }, []);

  const suggestedName = useMemo(() => suggestName(description), [description]);
  const effectiveName = projectName.trim() || suggestedName;
  const canSubmit = description.trim().length >= 15 && !submitting;

  useEffect(() => {
    listTemplates()
      .then((res) => {
        setTemplates(res.templates || []);
        if (res.default) setTemplate((t) => t || res.default);
      })
      .catch((e) => setTemplatesError(`Could not load templates: ${e.message}`));
  }, []);

  const handleBack = () => (setView ? setView('dashboard') : (window.location.href = '/'));

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setErrorMessage('');
    if (description.trim().length < 15) {
      setErrorMessage('Describe the app in a sentence or two so the planner has something to work with.');
      return;
    }
    setSubmitting(true);

    const included = FEATURES.filter((f) => features[f.key]).map((f) => f.label.toLowerCase());
    const prompt = [
      effectiveName ? `Project name: ${effectiveName}.` : '',
      selected ? `Tech stack: ${Object.values(selected.stack).join(', ')}.` : '',
      included.length ? `Include: ${included.join(', ')}.` : '',
      `Requirements: ${description.trim()}`,
    ].filter(Boolean).join(' ');
    const projectId = effectiveName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'project';

    try {
      const res = await createGeneration(projectId, prompt, template);
      setSubmitting(false);
      if (onGenerateSuccess) onGenerateSuccess(res.generation_id, effectiveName);
      else if (setView) setView('build');
    } catch (err) {
      setSubmitting(false);
      setErrorMessage(`Could not start the run: ${err.message}. Check that the backend is running.`);
    }
  };

  return (
    <div className="min-h-full bg-bg-base p-4 font-sans text-text-primary sm:p-6 lg:p-8">
      <div className="mx-auto max-w-6xl">
        <button
          onClick={handleBack}
          className="mb-6 inline-flex items-center gap-2 rounded-lg px-2 py-1 text-xs text-text-secondary transition hover:bg-surface-elevated hover:text-text-primary cursor-pointer"
        >
          <FaArrowLeft size={10} /> Dashboard
        </button>

        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">New project</h1>
          <p className="mt-1.5 max-w-2xl text-sm text-text-secondary">
            Describe the app you want. The more concrete the features and data, the better the generated code.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-6">
            {/* Description */}
            <section className="rounded-2xl border border-border-dark bg-surface-card p-5">
              <label htmlFor="project-description" className="text-sm font-medium">What should it do?</label>
              <textarea
                id="project-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={7}
                placeholder="e.g. A reading list app. Users add books with title, author and status (to read, reading, finished), rate finished books and see what they read this year."
                className="mt-3 block w-full resize-y rounded-xl border border-border-dark bg-bg-base px-4 py-3 text-sm leading-relaxed text-text-primary placeholder:text-text-muted outline-none transition focus:border-accent-violet/70 focus:ring-4 focus:ring-accent-violet/10"
              />
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-xs text-text-muted">Start from an example:</span>
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.label}
                    type="button"
                    onClick={() => { setDescription(ex.text); setProjectName(ex.name); }}
                    className="rounded-full border border-border-dark bg-surface-elevated px-3 py-1 text-xs text-text-secondary transition hover:border-accent-violet/50 hover:text-text-primary cursor-pointer"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            </section>

            {/* Name + stack */}
            <section className="grid gap-5 rounded-2xl border border-border-dark bg-surface-card p-5 md:grid-cols-2">
              <div className="md:col-span-2">
                <label htmlFor="project-name" className="text-sm font-medium">Project name <span className="font-normal text-text-muted">(optional)</span></label>
                <input
                  id="project-name"
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder={suggestedName || 'Named from your description'}
                  className="mt-2 block w-full rounded-xl border border-border-dark bg-bg-base px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted outline-none transition focus:border-accent-violet/70 focus:ring-4 focus:ring-accent-violet/10"
                />
              </div>
              <div>
                <span className="text-sm font-medium">Project template</span>
                <div className="mt-2 grid gap-2 sm:grid-cols-3" role="radiogroup" aria-label="Project template">
                  {templates.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      role="radio"
                      aria-checked={template === t.id}
                      onClick={() => setTemplate(t.id)}
                      className={`rounded-xl border p-3 text-left transition cursor-pointer ${
                        template === t.id
                          ? 'border-accent-violet/60 bg-accent-violet/15'
                          : 'border-border-dark bg-bg-base hover:border-accent-violet/30'
                      }`}
                    >
                      <span className="block text-sm font-semibold text-text-primary">{t.label}</span>
                      <span className="mt-1 block text-[11px] leading-snug text-text-secondary">{t.description}</span>
                    </button>
                  ))}
                  {!templates.length && (
                    <p className="text-xs text-text-muted sm:col-span-3">{templatesError || 'Loading templates…'}</p>
                  )}
                </div>
              </div>
            </section>

            {/* Features */}
            <section className="rounded-2xl border border-border-dark bg-surface-card p-5">
              <span className="text-sm font-medium">Also include</span>
              <ul className="mt-3 divide-y divide-border-subtle">
                {FEATURES.map((f) => (
                  <li key={f.key} className="flex items-center justify-between gap-4 py-3">
                    <div>
                      <p className="text-sm text-text-primary">{f.label}</p>
                      <p className="text-xs text-text-muted">{f.hint}</p>
                    </div>
                    <Switch label={f.label} checked={features[f.key]} onChange={(v) => setFeatures({ ...features, [f.key]: v })} />
                  </li>
                ))}
              </ul>
            </section>
          </div>

          {/* Summary */}
          <aside className="space-y-4 xl:sticky xl:top-6 xl:self-start">
            <div className="rounded-2xl border border-border-dark bg-surface-card p-5">
              <p className="text-xs uppercase tracking-wider text-text-muted">You're building</p>
              <p className="mt-1 truncate text-lg font-semibold">{effectiveName || 'Untitled project'}</p>
              <p className="mt-1 text-xs text-text-secondary">{selected ? Object.values(selected.stack).join(' · ') : template}</p>

              <button
                type="submit"
                disabled={!canSubmit}
                className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent-violet px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent-violet/25 transition hover:bg-[#7c4ee4] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none cursor-pointer"
              >
                {submitting ? <><FaSpinner className="animate-spin" size={12} /> Starting…</> : <>Start generation <FaArrowRight size={11} /></>}
              </button>
              {errorMessage && <p className="mt-3 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{errorMessage}</p>}

              <p className="mt-4 text-[11px] leading-relaxed text-text-muted">
                {engine === null
                  ? 'Checking local models…'
                  : engine.ollama_online
                    ? <>Runs locally: <span className="font-mono text-text-secondary">{engine.planning_model}</span> plans, <span className="font-mono text-text-secondary">{engine.coding_model}</span> writes code. Expect several minutes per stage on CPU.</>
                    : <span className="text-rose-300">Ollama is not reachable, so the run will fail. Start Ollama first.</span>}
              </p>
            </div>

            <div className="rounded-2xl border border-border-dark bg-surface-card p-5">
              <p className="text-xs uppercase tracking-wider text-text-muted">Every run includes</p>
              <ul className="mt-3 space-y-3">
                {ALWAYS_ON.map(({ Icon, text }) => (
                  <li key={text} className="flex gap-3 text-xs text-text-secondary">
                    <Icon size={12} className="mt-0.5 shrink-0 text-violet-300" />
                    {text}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </form>
      </div>
    </div>
  );
}
