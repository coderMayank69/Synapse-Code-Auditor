"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface AuditResult {
  review: string;
  model?: string;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  error?: string;
}

const SAMPLES: Record<string, { label: string; lang: string; code: string }> = {
  sql: {
    label: "SQL Injection",
    lang: "python",
    code: `def authenticate_user(username, password, db_cursor):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    db_cursor.execute(query)
    return db_cursor.fetchone()`,
  },
  race: {
    label: "Race Condition",
    lang: "python",
    code: `import asyncio

async def update_balance(user_id, amount, db_client):
    balance = await db_client.get_balance(user_id)
    new_balance = balance + amount
    await asyncio.sleep(0.05)  # Simulate latency
    await db_client.set_balance(user_id, new_balance)`,
  },
  webhook: {
    label: "FastAPI Bug",
    lang: "python",
    code: `from fastapi import FastAPI
import requests, json

app = FastAPI()

@app.post('/webhook')
def handle_webhook(payload: dict):
    if not payload.get('user_id'): return {'error': 'missing id'}
    res = requests.post('http://internal-log.local/audit', json=payload)
    with open('audit.log', 'a') as f:
        f.write(json.dumps(res.json()) + '\\n')
    return {'status': 'processed'}`,
  },
};

function md(text: string): string {
  return text
    .replace(/```[\w]*\n([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/^---$/gm, "<hr>")
    .replace(/\n\n/g, "<br><br>");
}

export default function CodeAuditor() {
  const [code, setCode]       = useState("");
  const [lang, setLang]       = useState("python");
  const [result, setResult]   = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(false);
  const areaRef = useRef<HTMLTextAreaElement>(null);

  const run = useCallback(async () => {
    if (!code.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res  = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language: lang }),
      });
      setResult(await res.json());
    } catch {
      setResult({ review: "", error: "Network error — please try again." });
    } finally {
      setLoading(false);
    }
  }, [code, lang, loading]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") run(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [run]);

  const loadSample = (key: string) => {
    const s = SAMPLES[key];
    setCode(s.code);
    setLang(s.lang);
    setResult(null);
    areaRef.current?.focus();
  };

  return (
    <div className="demo-grid">
      {/* ── LEFT: Input ── */}
      <div className="demo-pane">
        <div className="demo-bar">
          <div className="demo-circles">
            <span className="demo-circle dc-r" />
            <span className="demo-circle dc-y" />
            <span className="demo-circle dc-g" />
          </div>
          <span className="demo-bar-label">Input</span>
          <select
            id="lang-select"
            className="lang-select"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
          >
            {["python","javascript","typescript","go","rust","java","cpp","sql"].map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>

        <div className="demo-chips">
          {Object.entries(SAMPLES).map(([k, s]) => (
            <button key={k} id={`sample-${k}`} className="demo-chip" onClick={() => loadSample(k)}>
              {s.label}
            </button>
          ))}
        </div>

        <textarea
          ref={areaRef}
          id="code-input"
          className="code-area"
          placeholder={`# Paste ${lang} code here…\n# Ctrl+Enter to audit`}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          aria-label="Code input"
        />

        <div className="demo-footer">
          <button
            id="audit-btn"
            className="audit-btn"
            onClick={run}
            disabled={loading || !code.trim()}
          >
            {loading ? <><span className="spinner" /> Analyzing…</> : "⚡ Audit Code"}
          </button>
          <button
            id="clear-btn"
            className="clear-btn"
            onClick={() => { setCode(""); setResult(null); }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* ── RIGHT: Output ── */}
      <div className="demo-pane">
        <div className="demo-bar">
          <div className="demo-circles">
            <span className="demo-circle dc-r" />
            <span className="demo-circle dc-y" />
            <span className="demo-circle dc-g" />
          </div>
          <span className="demo-bar-label">Synapse Review</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--gray-2)" }}>
            LLaMA 3.3 · 70B
          </span>
        </div>

        {result?.usage && (
          <div className="review-meta-bar">
            <span><span>{result.usage.prompt_tokens}</span> prompt</span>
            <span><span>{result.usage.completion_tokens}</span> output</span>
            <span><span>{result.usage.total_tokens}</span> total tokens</span>
          </div>
        )}

        {result?.error && <div className="err-bar">⚠ {result.error}</div>}

        <div className="review-out" id="review-output" aria-live="polite">
          {loading && (
            <div className="review-empty">
              <div className="review-empty-icon">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor"
                  strokeWidth="1.5" style={{ color: "var(--gray-3)", animation: "spin 1s linear infinite" }}>
                  <circle cx="18" cy="18" r="15" strokeDasharray="60 30" />
                </svg>
              </div>
              <div className="review-empty-text">Analyzing your code…<br />Usually takes 3–8 seconds.</div>
            </div>
          )}
          {!loading && !result && (
            <div className="review-empty">
              <div className="review-empty-icon">SYNAPSE</div>
              <div className="review-empty-text">
                Review will appear here.<br />Select a sample or paste your own code.
              </div>
            </div>
          )}
          {!loading && result?.review && (
            <div className="review-content" dangerouslySetInnerHTML={{ __html: md(result.review) }} />
          )}
        </div>
      </div>
    </div>
  );
}
