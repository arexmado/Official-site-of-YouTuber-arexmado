import React, { useEffect, useMemo, useRef, useState } from "react";
import Editor from "@monaco-editor/react";

/**
 * AREXMADO Online IDE — VS Code 스타일 단일 파일 React 컴포넌트
 *
 * ✅ 주요 기능
 * - 좌측 파일 트리 + 탭형 에디터(모나코)
 * - HTML/CSS/JS 프로젝트 즉시 실행(iframe 미리보기)
 * - JS console 로그/에러 캡처 및 표시
 * - Python 파일(.py) 실행: Pyodide를 필요 시 동적 로드
 * - 다크/라이트 테마 토글, 글꼴 크기, 자동 저장(LocalStorage)
 * - 한국어 UI 기본
 *
 * ⚙️ 확장 아이디어(빠른 추가 가능)
 * - 프로젝트 .zip 내보내기/가져오기(JSZip)
 * - 파일 검색(Ctrl+P), 다국어 UI, 플러그인 훅
 * - Markdown 미리보기, 코드 포맷터(Prettier)
 */

// 로컬스토리지 키
const LS_KEY = "arexmado-ide-project-v1";
const THEME_KEY = "arexmado-ide-theme";
const FONT_KEY = "arexmado-ide-fontsize";

// 기본 파일들
const DEFAULT_FILES = {
  "index.html": {
    name: "index.html",
    language: "html",
    content: `<!doctype html>\n<html lang="ko">\n<head>\n  <meta charset="utf-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1" />\n  <title>AREXMADO 온라인 IDE</title>\n  <link rel="stylesheet" href="style.css" />\n</head>\n<body>\n  <div id="app">\n    <h1>AREXMADO 온라인 IDE 🚀</h1>\n    <p>왼쪽에서 파일을 선택하고, 상단의 ▶ 실행 버튼으로 미리보세요.</p>\n  </div>\n  <script src="main.js"></script>\n</body>\n</html>\n`,
  },
  "style.css": {
    name: "style.css",
    language: "css",
    content: `:root{--bg:#0b1020;--fg:#e3e8f5;--acc:#7aa2f7} body{margin:0;background:var(--bg);color:var(--fg);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,Pretendard,Malgun Gothic,Arial} h1{color:var(--acc)} #app{padding:24px} button{padding:.5rem 1rem;border-radius:.5rem;border:1px solid #334; background:#111827;color:#e5e7eb} button:hover{background:#1f2937}`,
  },
  "main.js": {
    name: "main.js",
    language: "javascript",
    content: `console.log("Hello from AREXMADO IDE!");\nconst app=document.getElementById('app');\nconst el=document.createElement('p');\nel.textContent='JS가 정상적으로 로드되었습니다.';\napp.appendChild(el);\n`,
  },
  "hello.py": {
    name: "hello.py",
    language: "python",
    content: `print('파이썬도 됩니다!\n1+1=', 1+1)`
  },
};

// 유틸: 파일 확장자 → 모나코 언어
function extToLang(name) {
  if (name.endsWith(".html")) return "html";
  if (name.endsWith(".css")) return "css";
  if (name.endsWith(".js")) return "javascript";
  if (name.endsWith(".ts")) return "typescript";
  if (name.endsWith(".json")) return "json";
  if (name.endsWith(".md")) return "markdown";
  if (name.endsWith(".py")) return "python";
  return "plaintext";
}

export default function OnlineVSCodeLikeIDE() {
  const [files, setFiles] = useState(() => {
    try {
      const saved = localStorage.getItem(LS_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return DEFAULT_FILES;
  });
  const [active, setActive] = useState("index.html");
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || "dark");
  const [fontSize, setFontSize] = useState(() => Number(localStorage.getItem(FONT_KEY) || 14));
  const [previewHTML, setPreviewHTML] = useState("");
  const [consoleLogs, setConsoleLogs] = useState([]);
  const [pyReady, setPyReady] = useState(false);
  const pyodideRef = useRef(null);
  const iframeRef = useRef(null);

  // 자동 저장
  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify(files));
  }, [files]);
  useEffect(() => localStorage.setItem(THEME_KEY, theme), [theme]);
  useEffect(() => localStorage.setItem(FONT_KEY, String(fontSize)), [fontSize]);

  // iframe 메시지 수신(JS 콘솔 전달)
  useEffect(() => {
    const onMsg = (e) => {
      if (e?.data?.__arex_console) {
        setConsoleLogs((prev) => [...prev, e.data.__arex_console]);
      }
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  const fileList = useMemo(() => Object.values(files), [files]);

  const updateFile = (name, content) => {
    setFiles((prev) => ({
      ...prev,
      [name]: { ...prev[name], content },
    }));
  };

  const addFile = () => {
    const base = prompt("새 파일 이름(예: script.js, page.html, note.md, app.py)", "new.js");
    if (!base) return;
    if (files[base]) return alert("이미 존재하는 파일입니다.");
    setFiles((prev) => ({
      ...prev,
      [base]: { name: base, language: extToLang(base), content: "" },
    }));
    setActive(base);
  };

  const renameFile = (name) => {
    const next = prompt("새 파일 이름", name);
    if (!next || next === name) return;
    if (files[next]) return alert("해당 이름의 파일이 이미 있습니다.");
    const { [name]: old, ...rest } = files;
    const updated = { ...rest, [next]: { ...old, name: next, language: extToLang(next) } };
    setFiles(updated);
    if (active === name) setActive(next);
  };

  const deleteFile = (name) => {
    if (!confirm(`${name} 파일을 삭제할까요?`)) return;
    const { [name]: _, ...rest } = files;
    setFiles(rest);
    if (active === name) setActive(Object.keys(rest)[0] || "");
  };

  // ▶ 실행: HTML/CSS/JS → iframe, Python → Pyodide
  const runProject = async () => {
    setConsoleLogs([]);
    const current = files[active];
    if (!current) return;

    if (current.language === "python") {
      await ensurePyodide();
      if (!pyodideRef.current) {
        alert("Pyodide 로드 실패");
        return;
      }
      try {
        const out = await pyodideRef.current.runPythonAsync(current.content);
        setConsoleLogs((prev) => [...prev, { type: "log", text: String(out ?? "(완료)") }]);
      } catch (err) {
        setConsoleLogs((prev) => [...prev, { type: "error", text: String(err) }]);
      }
      return;
    }

    // HTML/CSS/JS 프로젝트 빌드
    const html = files["index.html"]?.content || "";
    const css = files["style.css"]?.content || "";
    const js = files["main.js"]?.content || "";

    const srcdoc = `<!doctype html>\n<html><head>\n<meta charset=\"utf-8\" />\n<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>\n<style>${escapeHTML(css)}</style>\n</head>\n<body>\n${injectBody(html)}\n<script>\n(function(){\n  function post(type, text){ parent.postMessage({__arex_console:{type, text}}, '*'); }\n  const _log = console.log; const _err = console.error; const _warn = console.warn;\n  console.log = function(...a){ post('log', a.map(String).join(' ')); _log.apply(console,a); };\n  console.error = function(...a){ post('error', a.map(String).join(' ')); _err.apply(console,a); };\n  console.warn = function(...a){ post('warn', a.map(String).join(' ')); _warn.apply(console,a); };\n  window.addEventListener('error', e=>post('error', e.message));\n})();\n</script>\n<script>\n${js}\n</script>\n</body></html>`;

    setPreviewHTML(srcdoc);
    // iframe을 리프레시
    setTimeout(() => {
      if (iframeRef.current) {
        iframeRef.current.srcdoc = srcdoc;
      }
    }, 0);
  };

  async function ensurePyodide() {
    if (pyodideRef.current) return;
    try {
      setConsoleLogs((prev) => [...prev, { type: "log", text: "Pyodide 로드 중... (최초 1회)" }]);
      // CDN 로드
      // @ts-ignore
      if (!window.loadPyodide) {
        await loadExternalScript("https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js");
      }
      // @ts-ignore
      const pyodide = await window.loadPyodide({ stdout: (t) => pushLog("log", t), stderr: (t) => pushLog("error", t) });
      pyodideRef.current = pyodide;
      setPyReady(true);
      setConsoleLogs((prev) => [...prev, { type: "log", text: "Pyodide 준비 완료" }]);
    } catch (e) {
      setConsoleLogs((prev) => [...prev, { type: "error", text: `Pyodide 로드 실패: ${e}` }]);
    }
  }

  function pushLog(type, text) {
    setConsoleLogs((prev) => [...prev, { type, text: String(text) }]);
  }

  function loadExternalScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  const isDark = theme === "dark";

  return (
    <div className={"min-h-screen w-full flex flex-col " + (isDark ? "bg-[#0b1020] text-slate-100" : "bg-white text-slate-900") }>
      {/* 헤더 */}
      <div className="sticky top-0 z-10 flex items-center gap-2 px-3 py-2 border-b border-slate-700/40 bg-black/20 backdrop-blur">
        <div className="font-bold text-lg">AREXMADO IDE</div>
        <div className="text-xs opacity-80">VS Code 스타일 온라인 코드 편집기</div>
        <div className="flex-1" />
        <button className="px-3 py-1.5 rounded-xl border border-slate-600 hover:bg-slate-800" onClick={runProject}>▶ 실행</button>
        <button className="px-3 py-1.5 rounded-xl border border-slate-600 hover:bg-slate-800" onClick={addFile}>＋ 새 파일</button>
        <div className="flex items-center gap-2 ml-2 text-sm">
          <label>글꼴</label>
          <input
            type="number"
            min={10}
            max={24}
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="w-16 px-2 py-1 rounded-md bg-transparent border border-slate-600"
          />
          <label className="ml-3">테마</label>
          <button
            className="px-2 py-1 rounded-md border border-slate-600 hover:bg-slate-800"
            onClick={() => setTheme(isDark ? "light" : "dark")}
            title="테마 전환"
          >
            {isDark ? "다크" : "라이트"}
          </button>
        </div>
      </div>

      {/* 본문: 좌 파일트리 / 중 에디터 / 우 미리보기/콘솔 */}
      <div className="flex flex-1 min-h-0">
        {/* 사이드바 */}
        <aside className="w-60 border-r border-slate-700/40 p-2 overflow-auto">
          <div className="text-xs uppercase tracking-wide opacity-70 mb-2">파일</div>
          <ul className="space-y-1">
            {fileList.map((f) => (
              <li key={f.name} className={`group flex items-center justify-between rounded-lg ${active===f.name? (isDark?"bg-slate-800":"bg-slate-100"):"hover:bg-slate-700/30"}`}>
                <button
                  className="flex-1 text-left px-2 py-1 truncate"
                  onClick={() => setActive(f.name)}
                  title={f.name}
                >
                  {f.name}
                </button>
                <div className="opacity-0 group-hover:opacity-100 transition-all flex items-center">
                  <button className="px-1 text-xs opacity-80 hover:opacity-100" onClick={() => renameFile(f.name)}>이름</button>
                  <button className="px-1 text-xs text-red-400 hover:text-red-300" onClick={() => deleteFile(f.name)}>삭제</button>
                </div>
              </li>
            ))}
          </ul>
        </aside>

        {/* 중앙: 탭 + 에디터 */}
        <main className="flex-1 min-w-0 flex flex-col">
          {/* 탭바 */}
          <div className="flex items-center gap-2 border-b border-slate-700/40 px-2 py-1 overflow-auto">
            {fileList.map((f) => (
              <button
                key={f.name}
                className={`px-2 py-1 rounded-t-lg border-x border-t text-sm ${active===f.name? (isDark?"bg-slate-900 border-slate-600":"bg-white border-slate-300") : "opacity-70 hover:opacity-100 border-transparent"}`}
                onClick={() => setActive(f.name)}
                title={f.name}
              >
                {iconFor(f.language)} {f.name}
              </button>
            ))}
          </div>

          {/* 에디터 */}
          <div className="flex-1 min-h-0">
            {active && files[active] ? (
              <Editor
                height="100%"
                theme={isDark ? "vs-dark" : "light"}
                defaultLanguage={files[active].language}
                language={files[active].language}
                value={files[active].content}
                onChange={(val) => updateFile(active, val ?? "")}
                options={{ fontSize, minimap: { enabled: true }, smoothScrolling: true, wordWrap: "on" }}
              />
            ) : (
              <div className="h-full flex items-center justify-center opacity-70">파일을 선택하세요</div>
            )}
          </div>
        </main>

        {/* 우측: 미리보기 / 콘솔 */}
        <section className="w-[34%] min-w-[320px] border-l border-slate-700/40 flex flex-col">
          <div className="flex items-center gap-2 px-2 py-2 border-b border-slate-700/40">
            <span className="text-sm opacity-80">미리보기 / 콘솔</span>
            <div className="flex-1" />
            <button className="px-2 py-1 rounded-md border border-slate-600 hover:bg-slate-800" onClick={()=>setConsoleLogs([])}>콘솔 지우기</button>
          </div>

          {/* iframe 미리보기 */}
          <div className="h-1/2 min-h-[200px] border-b border-slate-700/40">
            <iframe ref={iframeRef} title="preview" className="w-full h-full bg-white" sandbox="allow-scripts allow-same-origin" srcDoc={previewHTML} />
          </div>

          {/* 콘솔 영역 */}
          <div className="flex-1 overflow-auto p-2 text-sm font-mono">
            {consoleLogs.length === 0 ? (
              <div className="opacity-60">콘솔 출력이 여기 표시됩니다… (JS/Python)</div>
            ) : (
              consoleLogs.map((l, i) => (
                <div key={i} className={`whitespace-pre-wrap mb-1 ${l.type==='error'?'text-red-400': l.type==='warn'?'text-yellow-400':'text-slate-200'}`}>{l.text}</div>
              ))
            )}
          </div>
        </section>
      </div>

      {/* 푸터 */}
      <footer className="px-3 py-2 text-xs opacity-70 border-t border-slate-700/40">
        © {new Date().getFullYear()} AREXMADO — 온라인 IDE (모나코/파이오다이드 기반). 저장은 브라우저 로컬에 보관됩니다.
      </footer>
    </div>
  );
}

function escapeHTML(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function injectBody(html) {
  // index.html의 <body> 안쪽만 추출하려 시도, 실패 시 원문 그대로 삽입
  try {
    const m = /<body[^>]*>([\s\S]*?)<\/body>/i.exec(html);
    if (m) return m[1];
  } catch (e) {}
  return html;
}

function iconFor(lang) {
  const cls = "inline-flex items-center justify-center w-5 h-5 mr-1 rounded-sm text-[10px] font-bold";
  const map = {
    html: <span className={cls + " bg-orange-600/70"}>H</span>,
    css: <span className={cls + " bg-blue-600/70"}>C</span>,
    javascript: <span className={cls + " bg-yellow-500/70 text-black"}>JS</span>,
    typescript: <span className={cls + " bg-blue-500/70"}>TS</span>,
    json: <span className={cls + " bg-emerald-600/70"}>J</span>,
    markdown: <span className={cls + " bg-slate-600/70"}>MD</span>,
    python: <span className={cls + " bg-indigo-600/70"}>PY</span>,
    plaintext: <span className={cls + " bg-slate-700/70"}>TXT</span>,
  };
  return map[lang] || map.plaintext;
}
