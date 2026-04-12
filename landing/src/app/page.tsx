"use client";

import { useEffect, useRef, useState } from "react";
import CodeAuditor from "./components/CodeAuditor";

const MARQUEE_ITEMS = [
  "SQL Injection Detection",
  "Race Condition Analysis",
  "Architecture Review",
  "Security Audit",
  "Performance Issues",
  "AI Code Verification",
  "Concurrency Bugs",
  "Error Handling",
  "Blocking I/O",
  "Input Validation",
];

export default function Home() {
  const revealRef = useRef<IntersectionObserver | null>(null);
  const cursorRef = useRef<HTMLDivElement>(null);
  const cursorRingRef = useRef<HTMLDivElement>(null);
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [ringPos,   setRingPos]   = useState({ x: -100, y: -100 });

  // Custom cursor
  useEffect(() => {
    let raf: number;
    let rx = -100, ry = -100;
    let tx = -100, ty = -100;

    const onMove = (e: MouseEvent) => { tx = e.clientX; ty = e.clientY; };
    window.addEventListener("mousemove", onMove);

    const loop = () => {
      rx += (tx - rx) * 0.12;
      ry += (ty - ry) * 0.12;
      setCursorPos({ x: tx, y: ty });
      setRingPos({ x: rx, y: ry });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => { window.removeEventListener("mousemove", onMove); cancelAnimationFrame(raf); };
  }, []);

  // Scroll reveal
  useEffect(() => {
    revealRef.current = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("in"); }),
      { threshold: 0.08 }
    );
    document.querySelectorAll(".reveal").forEach((el) => revealRef.current?.observe(el));
    return () => revealRef.current?.disconnect();
  }, []);

  const doubled = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS];

  return (
    <>
      {/* Custom cursor */}
      <div
        ref={cursorRef}
        className="cursor"
        style={{ left: cursorPos.x, top: cursorPos.y }}
        aria-hidden="true"
      />
      <div
        ref={cursorRingRef}
        className="cursor-ring"
        style={{ left: ringPos.x, top: ringPos.y }}
        aria-hidden="true"
      />

      {/* ── NAV ── */}
      <nav className="nav" role="navigation" aria-label="Main navigation">
        <div className="wrap nav-inner">
          <a href="#" className="nav-brand" aria-label="Synapse Code Auditor">
            <span>SYNAPSE</span> CODE AUDITOR
          </a>
          <ul className="nav-links" role="list">
            <li><a href="#features" className="nav-link">Features</a></li>
            <li><a href="#demo"     className="nav-link">Demo</a></li>
            <li><a href="#ide"      className="nav-link">IDE</a></li>
          </ul>
          <a
            href="https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-btn"
            id="nav-hf"
          >
            HuggingFace ↗
          </a>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="hero" aria-labelledby="hero-h1">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-glow"  aria-hidden="true" />

        <div className="wrap hero-content">
          <div className="hero-eyebrow">AI-Powered Code Audit</div>

          <h1 className="hero-title" id="hero-h1">
            CODE<br />
            THAT<br />
            <em>WORKS</em>
          </h1>

          <div className="hero-bottom">
            <p className="hero-desc">
              <strong>Synapse</strong> detects bugs, security vulnerabilities, and performance
              issues in AI-generated code — instantly. The code AI writes looks right.
              Synapse knows when it isn&apos;t.
            </p>
            <div className="hero-actions">
              <a href="#demo" className="btn-accent" id="hero-demo">
                Audit Code →
              </a>
              <a
                href="https://github.com/coderMayank69/Synapse-Code-Auditor"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost"
                id="hero-gh"
              >
                GitHub ↗
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ── MARQUEE ── */}
      <div className="marquee-wrap" aria-hidden="true">
        <div className="marquee-track">
          {doubled.map((item, i) => (
            <div className="marquee-item" key={i}>
              <span className="dot" />
              {item}
            </div>
          ))}
        </div>
      </div>

      {/* ── FEATURES ── */}
      <section className="section" id="features" aria-labelledby="feat-h2">
        <div className="wrap">
          <div className="section-head reveal">
            <div>
              <div className="section-label">Why Synapse</div>
              <h2 className="section-title" id="feat-h2">
                EVERY<br />BUG.
              </h2>
            </div>
            <p className="section-sub">
              From critical SQL injections to subtle async race conditions —
              Synapse catches what linters, tests, and code review miss.
            </p>
          </div>

          <div className="feat-table reveal">
            {[
              { idx: "01", name: "SECURITY",    tag: "Critical",  desc: "SQL injection, XSS, insecure deserialization, hardcoded secrets, and OWASP Top 10 — caught before production." },
              { idx: "02", name: "CONCURRENCY", tag: "Hard",      desc: "Race conditions, missing locks, unprotected shared state, and async/await misuse in Python, Go, JS." },
              { idx: "03", name: "ARCHITECTURE",tag: "Quality",   desc: "Blocking I/O in async contexts, missing error handling, hardcoded configs, and broken design patterns." },
              { idx: "04", name: "PERFORMANCE", tag: "Warning",   desc: "Unnecessary allocations, missing caching, N+1 queries, and redundant network calls." },
              { idx: "05", name: "SCORING",     tag: "Insight",   desc: "Every review ends with a 0–100 quality score and corrected code you can ship directly." },
            ].map((f) => (
              <div className="feat-row" key={f.idx}>
                <div className="feat-cell feat-idx">{f.idx}</div>
                <div className="feat-cell">
                  <div className="feat-tag">{f.tag}</div>
                  <div className="feat-name">{f.name}</div>
                </div>
                <div className="feat-cell">
                  <p className="feat-desc">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className="stats-bar reveal">
            {[
              { val: "< 8", unit: "S",  lbl: "Review Time" },
              { val: "70",  unit: "B",  lbl: "LLaMA Parameters" },
              { val: "5",   unit: "+",  lbl: "Audit Categories" },
              { val: "0",   unit: "ms", lbl: "Setup Required" },
            ].map((s) => (
              <div className="stat-cell" key={s.lbl}>
                <div className="stat-val">{s.val}<span>{s.unit}</span></div>
                <div className="stat-lbl">{s.lbl}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LIVE DEMO ── */}
      <section className="section" id="demo" aria-labelledby="demo-h2">
        <div className="wrap">
          <div className="section-head reveal">
            <div>
              <div className="section-label">Live Demo</div>
              <h2 className="section-title" id="demo-h2">
                TRY<br />NOW.
              </h2>
            </div>
            <p className="section-sub">
              Paste any snippet and get an expert-level review in seconds.
              Load a real vulnerability from the samples.
            </p>
          </div>
          <div className="reveal">
            <CodeAuditor />
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="section" id="how" aria-labelledby="how-h2">
        <div className="wrap">
          <div className="section-head reveal">
            <div>
              <div className="section-label">Process</div>
              <h2 className="section-title" id="how-h2">
                HOW<br />IT WORKS.
              </h2>
            </div>
            <p className="section-sub">
              Four steps from raw code to production-ready.
            </p>
          </div>

          <div className="how-list reveal">
            {[
              { n: "01", h: "PASTE",   p: "Drop any snippet — Python, JS, TypeScript, Go, Rust — and select the language." },
              { n: "02", h: "ANALYZE", p: "LLaMA 3.3-70B via Groq inspects security, concurrency, architecture, and performance simultaneously." },
              { n: "03", h: "REVIEW",  p: "Receive a structured report: Critical issues, Warnings, Suggestions, corrected code, and a quality score." },
              { n: "04", h: "SHIP",    p: "Apply the suggested fix, re-audit if needed. Iterate until your quality score meets your standard." },
            ].map((s) => (
              <div className="how-item" key={s.n}>
                <div className="how-n">{s.n}</div>
                <div className="how-h">{s.h}</div>
                <div className="how-p">{s.p}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── IDE INTEGRATION ── */}
      <section className="section" id="ide" aria-labelledby="ide-h2">
        <div className="wrap">
          <div className="section-head reveal">
            <div>
              <div className="section-label">Integration</div>
              <h2 className="section-title" id="ide-h2">
                ANY<br />IDE.
              </h2>
            </div>
            <p className="section-sub">
              Call the REST API from VS Code, JetBrains, Neovim, or any editor.
              No plugin required.
            </p>
          </div>

          <div className="ide-wrap reveal">
            {/* Code block */}
            <div className="ide-code">
              <div className="ide-code-bar">
                <span className="ide-code-label">synapse_audit.py</span>
                <div className="demo-circles">
                  <span className="demo-circle dc-r" />
                  <span className="demo-circle dc-y" />
                  <span className="demo-circle dc-g" />
                </div>
              </div>
              <div className="ide-code-body">
                <pre>
{`import requests

`}<span className="c-acc">SYNAPSE</span>{` = `}<span className="c-str">&quot;https://your-app.vercel.app/api/audit&quot;</span>{`

`}<span className="c-key">def</span>{` `}<span className="c-fn">audit_file</span>{`(path: str):
    `}<span className="c-key">with</span>{` `}<span className="c-fn">open</span>{`(path) `}<span className="c-key">as</span>{` f:
        code = f.`}<span className="c-fn">read</span>{`()

    res = requests.`}<span className="c-fn">post</span>{`(
        `}<span className="c-acc">SYNAPSE</span>{`,
        json={`}<span className="c-str">&quot;code&quot;</span>{`: code, `}<span className="c-str">&quot;language&quot;</span>{`: `}<span className="c-str">&quot;python&quot;</span>{`}
    )
    `}<span className="c-fn">print</span>{`(res.json()[`}<span className="c-str">&quot;review&quot;</span>{`])

`}<span className="c-comment"># Run from terminal</span>{`
`}<span className="c-fn">audit_file</span>{`(`}<span className="c-str">&quot;my_module.py&quot;</span>{`)`}
                </pre>
              </div>
            </div>

            {/* Steps */}
            <div className="ide-steps">
              {[
                { n: "1", h: "Deploy", p: "Deploy this Next.js project to Vercel. Your /api/audit endpoint is live instantly.", code: "npx vercel --prod" },
                { n: "2", h: "POST",   p: "Send your code and language. Get structured Markdown review back.", code: 'POST /api/audit → {"code": "...", "language": "python"}' },
                { n: "3", h: "Automate", p: "Create a VS Code task, Neovim command, or shell alias to audit the current file.", code: "Ctrl+Shift+A → Audit Buffer" },
                { n: "4", h: "Gate",   p: "Block merges when quality score drops below your threshold in CI.", code: "score >= 70 → merge allowed" },
              ].map((s) => (
                <div className="ide-step" key={s.n}>
                  <div className="ide-step-num">{s.n}</div>
                  <div className="ide-step-body">
                    <h4>{s.h}</h4>
                    <p>{s.p}</p>
                    <code>{s.code}</code>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section" aria-labelledby="cta-h2">
        <div className="cta-glow" aria-hidden="true" />
        <div className="wrap">
          <h2 className="cta-title reveal" id="cta-h2">
            SHIP CODE<br />
            THAT <em>WORKS</em>
          </h2>
          <p className="cta-sub reveal">
            Stop deploying hidden bugs from AI-generated code.
            Synapse gives you the confidence to ship.
          </p>
          <div className="cta-btns reveal">
            <a href="#demo" className="btn-accent" id="cta-demo">
              Audit Now — Free →
            </a>
            <a
              href="https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
              id="cta-hf"
            >
              HuggingFace Space ↗
            </a>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="foot" role="contentinfo">
        <div className="wrap foot-inner">
          <div className="foot-brand"><span>SYNAPSE</span> CODE AUDITOR</div>
          <ul className="foot-links" role="list">
            <li><a href="https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor" target="_blank" rel="noopener noreferrer" className="foot-link">HuggingFace</a></li>
            <li><a href="https://github.com/coderMayank69/Synapse-Code-Auditor"             target="_blank" rel="noopener noreferrer" className="foot-link">GitHub</a></li>
            <li><a href="#demo"  className="foot-link">Demo</a></li>
            <li><a href="#ide"   className="foot-link">IDE</a></li>
          </ul>
          <p className="foot-copy">© 2026 · LLaMA 3.3 70B + Groq</p>
        </div>
      </footer>
    </>
  );
}
