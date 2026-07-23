(() => {
  "use strict";

  const VERSION = "0.2.0";
  const STORAGE_KEY = "seresarte_v_os_state_v1";
  const HOME = "/home/renova";

  const appConfig = {
    terminal: { title: "Terminal", x: 90, y: 72, w: 780, h: 500 },
    files: { title: "Archivos", x: 230, y: 112, w: 700, h: 470 },
    notes: { title: "Notas", x: 300, y: 138, w: 720, h: 510 },
    browser: { title: "Navegador interno", x: 360, y: 92, w: 760, h: 500 },
    calculator: { title: "Calculadora", x: 450, y: 150, w: 360, h: 420 },
    system: { title: "Sistema", x: 500, y: 118, w: 630, h: 430 }
  };

  const appAliases = {
    calc: "calculator",
    calculadora: "calculator",
    archivo: "files",
    archivos: "files",
    notas: "notes",
    navegador: "browser",
    sistema: "system",
    terminal: "terminal"
  };

  const defaultFS = {
    "/": { type: "dir", children: ["home", "apps", "system", "var"] },
    "/home": { type: "dir", children: ["renova"] },
    "/home/renova": { type: "dir", children: ["README.md", "bitacora.md", "notas.txt", "proyectos"] },
    "/home/renova/proyectos": { type: "dir", children: ["codex.txt", "renova.txt", "seresarte.txt"] },
    "/apps": { type: "dir", children: ["browser.app", "calculator.app", "files.app", "notes.app", "system.app", "terminal.app"] },
    "/system": { type: "dir", children: ["about.txt", "changelog.txt", "limits.txt"] },
    "/var": { type: "dir", children: ["log"] },
    "/var/log": { type: "dir", children: ["boot.log"] },
    "/home/renova/README.md": {
      type: "file",
      content: "# SERESARTE V-OS\n\nOrdenador virtual web para RENOVA/SERESARTE.\n\nComandos iniciales:\n- help\n- ls\n- tree\n- cat README.md\n- write prueba.txt \"hola\"\n- open notes\n- neofetch\n"
    },
    "/home/renova/notas.txt": {
      type: "file",
      content: "Notas iniciales de SERESARTE V-OS.\n\nEste archivo vive en el sistema de archivos virtual y se guarda en localStorage.\n"
    },
    "/home/renova/bitacora.md": {
      type: "file",
      content: "# Bitacora\n\n- v0.1: escritorio, terminal, archivos, notas, navegador simulado, calculadora y sistema.\n- v0.2: servidor allowlisted, Page Agent opt-in, CSP y calculadora sin evaluacion dinamica.\n"
    },
    "/home/renova/proyectos/codex.txt": {
      type: "file",
      content: "Codex puede extender este ordenador virtual desde app.js sin dependencias externas.\n"
    },
    "/home/renova/proyectos/renova.txt": {
      type: "file",
      content: "RENOVA: programa de vida, habitat, herida y horizonte. Este V-OS lo trata como contexto cultural y operativo, no como una VM real.\n"
    },
    "/home/renova/proyectos/seresarte.txt": {
      type: "file",
      content: "SERESARTE: escritorio narrativo para archivos, notas, investigacion, produccion cultural y prototipos web.\n"
    },
    "/apps/terminal.app": { type: "file", content: "Terminal virtual renova-sh." },
    "/apps/files.app": { type: "file", content: "Explorador del sistema de archivos virtual." },
    "/apps/notes.app": { type: "file", content: "Editor de notas persistente." },
    "/apps/browser.app": { type: "file", content: "Navegador interno simulado." },
    "/apps/calculator.app": { type: "file", content: "Calculadora local." },
    "/apps/system.app": { type: "file", content: "Panel del sistema." },
    "/system/about.txt": {
      type: "file",
      content: "SERESARTE V-OS v0.2.0\nTipo: ordenador virtual web simulado.\nRuntime: HTML, CSS y JavaScript.\nPersistencia: localStorage.\nServidor seguro: python3 server.py en http://127.0.0.1:8000.\n"
    },
    "/system/limits.txt": {
      type: "file",
      content: "Limites: no ejecuta binarios reales, no virtualiza hardware y no accede al sistema de archivos real. Es una interfaz web con memoria local del navegador.\n"
    },
    "/system/changelog.txt": {
      type: "file",
      content: "v0.1.0: primera version funcional del escritorio virtual SERESARTE V-OS.\nv0.2.0: endurecimiento del servidor, privacidad del agente y verificacion ampliada.\n"
    },
    "/var/log/boot.log": {
      type: "file",
      content: "Boot completado. Apps cargadas: Terminal, Archivos, Notas, Navegador, Calculadora, Sistema.\n"
    }
  };

  let state = loadState();
  let zIndex = 100;
  const openWindows = new Map();

  const bootLines = [
    "SERESARTE V-OS BIOS 0.2.0",
    "Verificando entorno de navegador",
    "Montando sistema de archivos virtual",
    "Cargando escritorio y gestor de ventanas",
    "Activando Terminal, Archivos, Notas, Navegador, Calculadora y Sistema",
    "Persistencia local: localStorage disponible",
    "Sistema listo"
  ];

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function defaultState() {
    return {
      version: VERSION,
      cwd: HOME,
      fs: clone(defaultFS),
      notesFile: `${HOME}/notas.txt`,
      fileBrowserPath: HOME,
      browserAddress: "seresarte://home",
      windowState: {}
    };
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      return migrateState(JSON.parse(raw));
    } catch {
      return defaultState();
    }
  }

  function migrateState(input) {
    const base = defaultState();
    const next = { ...base, ...input };
    next.fs = input && typeof input.fs === "object" && input.fs ? input.fs : clone(defaultFS);

    for (const [path, nodeValue] of Object.entries(defaultFS)) {
      if (!next.fs[path]) next.fs[path] = clone(nodeValue);
    }

    for (const [path, nodeValue] of Object.entries(next.fs)) {
      if (!nodeValue || typeof nodeValue !== "object") {
        delete next.fs[path];
        continue;
      }
      if (nodeValue.type === "dir") {
        nodeValue.children = Array.isArray(nodeValue.children) ? uniqueSorted(nodeValue.children) : [];
      } else if (nodeValue.type === "file") {
        nodeValue.content = typeof nodeValue.content === "string" ? nodeValue.content : "";
      } else {
        delete next.fs[path];
      }
    }

    for (const path of Object.keys(next.fs)) {
      if (path === "/") continue;
      const parentPath = dirname(path);
      const parent = next.fs[parentPath];
      if (parent && parent.type === "dir" && !parent.children.includes(basename(path))) {
        parent.children.push(basename(path));
        parent.children = uniqueSorted(parent.children);
      }
    }

    if (!isDirIn(next.fs, next.cwd)) next.cwd = HOME;
    if (!isFileIn(next.fs, next.notesFile)) next.notesFile = `${HOME}/notas.txt`;
    if (!isDirIn(next.fs, next.fileBrowserPath)) next.fileBrowserPath = HOME;
    if (!next.windowState || typeof next.windowState !== "object") next.windowState = {};
    next.version = VERSION;
    return next;
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function resetState() {
    localStorage.removeItem(STORAGE_KEY);
    state = defaultState();
    location.reload();
  }

  function normalizePath(path = "/") {
    const raw = String(path || "/").replace(/\\/g, "/");
    const parts = [];
    for (const part of raw.split("/")) {
      if (!part || part === ".") continue;
      if (part === "..") parts.pop();
      else parts.push(part);
    }
    return `/${parts.join("/")}`;
  }

  function resolvePath(path = ".", base = state.cwd) {
    const value = String(path || ".").trim();
    if (value === "~") return HOME;
    if (value.startsWith("~/")) return normalizePath(`${HOME}/${value.slice(2)}`);
    if (value.startsWith("/")) return normalizePath(value);
    return normalizePath(`${base.replace(/\/$/, "")}/${value}`);
  }

  function dirname(path) {
    const normalized = normalizePath(path);
    if (normalized === "/") return "/";
    const parts = normalized.split("/").filter(Boolean);
    parts.pop();
    return parts.length ? `/${parts.join("/")}` : "/";
  }

  function basename(path) {
    const normalized = normalizePath(path);
    if (normalized === "/") return "/";
    return normalized.split("/").filter(Boolean).pop();
  }

  function uniqueSorted(items) {
    return [...new Set(items)].sort((a, b) => a.localeCompare(b));
  }

  function getNode(path) {
    return state.fs[normalizePath(path)];
  }

  function exists(path) {
    return Boolean(getNode(path));
  }

  function isDir(path) {
    const item = getNode(path);
    return Boolean(item && item.type === "dir");
  }

  function isFile(path) {
    const item = getNode(path);
    return Boolean(item && item.type === "file");
  }

  function isDirIn(fs, path) {
    const item = fs && fs[normalizePath(path)];
    return Boolean(item && item.type === "dir");
  }

  function isFileIn(fs, path) {
    const item = fs && fs[normalizePath(path)];
    return Boolean(item && item.type === "file");
  }

  function ensureParent(path) {
    const parentPath = dirname(path);
    const parent = getNode(parentPath);
    if (!parent || parent.type !== "dir") {
      throw new Error(`No existe el directorio padre: ${parentPath}`);
    }
    return parentPath;
  }

  function addChild(parentPath, childName) {
    const parent = getNode(parentPath);
    if (!parent || parent.type !== "dir") return;
    parent.children = uniqueSorted([...parent.children, childName]);
  }

  function removeChild(parentPath, childName) {
    const parent = getNode(parentPath);
    if (!parent || parent.type !== "dir") return;
    parent.children = parent.children.filter((item) => item !== childName);
  }

  function createFile(path, content = "") {
    const normalized = normalizePath(path);
    if (normalized === "/") throw new Error("No se puede escribir en /");
    const parentPath = ensureParent(normalized);
    const current = getNode(normalized);
    if (current && current.type === "dir") throw new Error(`Es directorio: ${normalized}`);
    state.fs[normalized] = { type: "file", content };
    addChild(parentPath, basename(normalized));
    return normalized;
  }

  function createDir(path) {
    const normalized = normalizePath(path);
    if (normalized === "/") throw new Error("El directorio / ya existe");
    const parentPath = ensureParent(normalized);
    const current = getNode(normalized);
    if (current && current.type === "file") throw new Error(`Ya existe un archivo: ${normalized}`);
    if (!current) state.fs[normalized] = { type: "dir", children: [] };
    addChild(parentPath, basename(normalized));
    return normalized;
  }

  function removePath(path, recursive = false) {
    const normalized = normalizePath(path);
    if (normalized === "/") throw new Error("No se puede borrar /");
    const item = getNode(normalized);
    if (!item) throw new Error(`No existe: ${normalized}`);
    if (item.type === "dir") {
      if (item.children.length && !recursive) {
        throw new Error("Directorio no vacio. Usa rm -r <ruta>.");
      }
      for (const child of [...item.children]) {
        removePath(resolvePath(child, normalized), true);
      }
    }
    delete state.fs[normalized];
    removeChild(dirname(normalized), basename(normalized));
    if (state.cwd.startsWith(`${normalized}/`)) state.cwd = dirname(normalized);
    if (state.notesFile === normalized) state.notesFile = `${HOME}/notas.txt`;
    if (state.fileBrowserPath === normalized || state.fileBrowserPath.startsWith(`${normalized}/`)) {
      state.fileBrowserPath = dirname(normalized);
    }
    return normalized;
  }

  function listFilePaths() {
    return Object.keys(state.fs)
      .filter((path) => state.fs[path].type === "file")
      .sort((a, b) => a.localeCompare(b));
  }

  function boot() {
    const bootEl = document.getElementById("boot");
    const bootLog = document.getElementById("bootLog");
    const progress = document.getElementById("bootProgress");
    const desktop = document.getElementById("desktop");
    let index = 0;

    const tick = () => {
      bootLog.textContent += `${bootLines[index]}\n`;
      progress.style.width = `${Math.round(((index + 1) / bootLines.length) * 100)}%`;
      index += 1;
      if (index < bootLines.length) {
        window.setTimeout(tick, 130);
        return;
      }
      window.setTimeout(() => {
        bootEl.hidden = true;
        desktop.hidden = false;
        setStatus("Sistema listo");
        openApp("files");
        openApp("terminal");
      }, 260);
    };

    tick();
  }

  function updateClock() {
    const clock = document.getElementById("clock");
    const now = new Date();
    clock.textContent = now.toLocaleString("es-MX", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function setStatus(message) {
    document.getElementById("statusText").textContent = message;
  }

  function canonicalApp(app) {
    return appAliases[app] || app;
  }

  function openApp(app, options = {}) {
    const id = canonicalApp(app);
    const config = appConfig[id];
    if (!config) {
      setStatus(`App no encontrada: ${app}`);
      return;
    }

    if (id === "files" && options.path) state.fileBrowserPath = normalizePath(options.path);
    if (id === "notes" && options.file) state.notesFile = normalizePath(options.file);

    const body = createWindow(id, config);
    body.innerHTML = "";

    if (id === "terminal") renderTerminal(body);
    if (id === "files") renderFiles(body, state.fileBrowserPath);
    if (id === "notes") renderNotes(body);
    if (id === "browser") renderBrowser(body);
    if (id === "calculator") renderCalculator(body);
    if (id === "system") renderSystem(body);

    setStatus(`${config.title} abierto`);
    saveState();
  }

  function createWindow(id, config) {
    if (openWindows.has(id)) {
      const existing = openWindows.get(id);
      existing.classList.remove("is-minimized");
      focusWindow(existing);
      state.windowState[id] = { ...state.windowState[id], open: true, minimized: false };
      saveState();
      return existing.querySelector(".window-body");
    }

    const saved = state.windowState[id] || {};
    const template = document.getElementById("window-template");
    const win = template.content.firstElementChild.cloneNode(true);
    const left = numberOr(saved.left, config.x);
    const top = numberOr(saved.top, config.y);
    const width = numberOr(saved.width, config.w);
    const height = numberOr(saved.height, config.h);

    win.dataset.app = id;
    win.dataset.testid = `window-${id}`;
    win.style.left = `${left}px`;
    win.style.top = `${top}px`;
    win.style.width = `${width}px`;
    win.style.height = `${height}px`;
    win.querySelector(".window-title").textContent = config.title;

    const close = win.querySelector(".window-close");
    const minimize = win.querySelector(".window-minimize");
    const header = win.querySelector(".window-header");

    close.addEventListener("click", () => {
      win.remove();
      openWindows.delete(id);
      state.windowState[id] = { ...state.windowState[id], open: false, minimized: false };
      saveState();
      setStatus(`${config.title} cerrado`);
    });

    minimize.addEventListener("click", () => {
      win.classList.add("is-minimized");
      state.windowState[id] = { ...state.windowState[id], open: true, minimized: true };
      saveState();
      setStatus(`${config.title} minimizado`);
    });

    win.addEventListener("pointerdown", () => focusWindow(win));
    attachDrag(win, header, id);

    const observer = new ResizeObserver(() => {
      state.windowState[id] = {
        ...state.windowState[id],
        width: Math.round(win.offsetWidth),
        height: Math.round(win.offsetHeight)
      };
      saveState();
    });
    observer.observe(win);

    document.getElementById("windows").appendChild(win);
    openWindows.set(id, win);
    focusWindow(win);
    boundWindow(win);
    return win.querySelector(".window-body");
  }

  function numberOr(value, fallback) {
    return Number.isFinite(Number(value)) ? Number(value) : fallback;
  }

  function focusWindow(win) {
    win.style.zIndex = String(++zIndex);
  }

  function attachDrag(win, handle, id) {
    let dragging = false;
    let offsetX = 0;
    let offsetY = 0;

    handle.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 && event.pointerType !== "touch") return;
      dragging = true;
      offsetX = event.clientX - win.offsetLeft;
      offsetY = event.clientY - win.offsetTop;
      handle.setPointerCapture(event.pointerId);
      focusWindow(win);
      event.preventDefault();
    });

    handle.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      win.style.left = `${event.clientX - offsetX}px`;
      win.style.top = `${event.clientY - offsetY}px`;
      boundWindow(win);
    });

    const endDrag = (event) => {
      if (!dragging) return;
      dragging = false;
      try {
        handle.releasePointerCapture(event.pointerId);
      } catch {
        /* Pointer capture may already be released. */
      }
      state.windowState[id] = {
        ...state.windowState[id],
        left: Math.round(win.offsetLeft),
        top: Math.round(win.offsetTop),
        width: Math.round(win.offsetWidth),
        height: Math.round(win.offsetHeight),
        open: true,
        minimized: false
      };
      saveState();
    };

    handle.addEventListener("pointerup", endDrag);
    handle.addEventListener("pointercancel", endDrag);
  }

  function boundWindow(win) {
    const maxLeft = Math.max(0, window.innerWidth - 90);
    const maxTop = Math.max(42, window.innerHeight - 120);
    const left = Math.max(0, Math.min(maxLeft, win.offsetLeft));
    const top = Math.max(42, Math.min(maxTop, win.offsetTop));
    win.style.left = `${left}px`;
    win.style.top = `${top}px`;
  }

  function renderTerminal(body) {
    body.innerHTML = `
      <div class="terminal">
        <pre class="terminal-output" data-testid="terminal-output"></pre>
        <div class="terminal-input-row">
          <span class="terminal-prompt" data-testid="terminal-prompt"></span>
          <input class="terminal-input" data-testid="terminal-input" autocomplete="off" spellcheck="false" autofocus>
        </div>
      </div>
    `;

    const output = body.querySelector(".terminal-output");
    const input = body.querySelector(".terminal-input");
    const prompt = body.querySelector(".terminal-prompt");
    const history = [];
    let historyIndex = 0;

    const term = {
      print(text = "") {
        output.textContent += `${text}\n`;
        output.scrollTop = output.scrollHeight;
      },
      clear() {
        output.textContent = "";
      }
    };

    const refreshPrompt = () => {
      prompt.textContent = `renova:${state.cwd}$`;
    };

    term.print("SERESARTE V-OS Terminal");
    term.print("Escribe help para ver comandos.");
    term.print("");
    refreshPrompt();

    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowUp") {
        if (history.length) {
          historyIndex = Math.max(0, historyIndex - 1);
          input.value = history[historyIndex] || "";
        }
        event.preventDefault();
        return;
      }

      if (event.key === "ArrowDown") {
        if (history.length) {
          historyIndex = Math.min(history.length, historyIndex + 1);
          input.value = history[historyIndex] || "";
        }
        event.preventDefault();
        return;
      }

      if (event.key !== "Enter") return;
      const raw = input.value.trim();
      term.print(`${prompt.textContent} ${raw}`);
      input.value = "";
      if (raw) {
        history.push(raw);
        historyIndex = history.length;
        runCommand(raw, term);
      }
      refreshPrompt();
      saveState();
    });

    window.setTimeout(() => input.focus(), 0);
  }

  function tokenize(raw) {
    const tokens = [];
    let current = "";
    let quote = "";
    let escaped = false;

    for (const char of raw) {
      if (escaped) {
        current += char;
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (quote) {
        if (char === quote) quote = "";
        else current += char;
        continue;
      }
      if (char === "\"" || char === "'") {
        quote = char;
        continue;
      }
      if (/\s/.test(char)) {
        if (current) {
          tokens.push(current);
          current = "";
        }
        continue;
      }
      current += char;
    }

    if (quote) throw new Error("Comillas sin cerrar");
    if (escaped) current += "\\";
    if (current) tokens.push(current);
    return tokens;
  }

  function runCommand(raw, term) {
    try {
      const tokens = tokenize(raw);
      const command = (tokens.shift() || "").toLowerCase();

      switch (command) {
        case "help":
          term.print(`Comandos disponibles:
  help                  Muestra esta ayuda
  pwd                   Muestra la ruta actual
  ls [ruta]             Lista archivos o directorios
  cd [ruta]             Cambia de directorio
  tree [ruta]           Muestra el arbol virtual
  cat <archivo>         Lee un archivo
  write <archivo> <txt> Escribe o reemplaza un archivo
  append <archivo> <t>  Anade texto a un archivo
  touch <archivo>       Crea archivo vacio
  mkdir <dir>           Crea directorio
  rm [-r] <ruta>        Borra archivo o directorio
  open <app|ruta>       Abre app, archivo o directorio
  apps                  Lista aplicaciones
  date                  Fecha local
  whoami                Usuario virtual
  neofetch              Perfil del sistema
  export                Imprime estado JSON
  reset                 Reinicia el V-OS`);
          break;

        case "pwd":
          term.print(state.cwd);
          break;

        case "ls": {
          const path = resolvePath(tokens[0] || ".");
          const item = getNode(path);
          if (!item) throw new Error(`No existe: ${path}`);
          if (item.type === "file") {
            term.print(basename(path));
          } else {
            term.print(formatDirectory(path));
          }
          break;
        }

        case "cd": {
          const path = resolvePath(tokens[0] || HOME);
          if (!isDir(path)) throw new Error(`No es directorio: ${path}`);
          state.cwd = path;
          state.fileBrowserPath = path;
          refreshFilesIfOpen(path);
          break;
        }

        case "tree": {
          const path = resolvePath(tokens[0] || ".");
          term.print(renderTree(path));
          break;
        }

        case "cat": {
          const target = requireArg(tokens, "Uso: cat <archivo>");
          const path = resolvePath(target);
          if (!isFile(path)) throw new Error(`No es archivo: ${path}`);
          term.print(getNode(path).content);
          break;
        }

        case "write": {
          const target = requireArg(tokens, "Uso: write <archivo> <texto>");
          const path = createFile(resolvePath(target), tokens.join(" "));
          notifyFileChanged(path);
          term.print(`Escrito: ${path}`);
          break;
        }

        case "append": {
          const target = requireArg(tokens, "Uso: append <archivo> <texto>");
          const path = resolvePath(target);
          if (!exists(path)) createFile(path, "");
          if (!isFile(path)) throw new Error(`No es archivo: ${path}`);
          const item = getNode(path);
          const addition = tokens.join(" ");
          if (item.content && !item.content.endsWith("\n")) item.content += "\n";
          item.content += addition;
          if (!item.content.endsWith("\n")) item.content += "\n";
          notifyFileChanged(path);
          term.print(`Anadido: ${path}`);
          break;
        }

        case "touch": {
          const target = requireArg(tokens, "Uso: touch <archivo>");
          const path = resolvePath(target);
          if (exists(path) && !isFile(path)) throw new Error(`No es archivo: ${path}`);
          if (!exists(path)) createFile(path, "");
          notifyFileChanged(path);
          term.print(`Archivo listo: ${path}`);
          break;
        }

        case "mkdir": {
          const target = requireArg(tokens, "Uso: mkdir <directorio>");
          const path = createDir(resolvePath(target));
          notifyFileChanged(path);
          term.print(`Directorio listo: ${path}`);
          break;
        }

        case "rm": {
          const recursive = tokens[0] === "-r" || tokens[0] === "-rf";
          if (recursive) tokens.shift();
          const target = requireArg(tokens, "Uso: rm [-r] <ruta>");
          const path = removePath(resolvePath(target), recursive);
          notifyFileChanged(path);
          term.print(`Borrado: ${path}`);
          break;
        }

        case "open": {
          const target = requireArg(tokens, "Uso: open <terminal|files|notes|browser|calculator|system|ruta>");
          const maybeApp = canonicalApp(target.toLowerCase());
          if (appConfig[maybeApp]) {
            openApp(maybeApp);
            break;
          }
          const path = resolvePath(target);
          if (isDir(path)) {
            openApp("files", { path });
          } else if (isFile(path)) {
            openApp("notes", { file: path });
          } else {
            throw new Error(`No existe app o ruta: ${target}`);
          }
          break;
        }

        case "apps":
          term.print("terminal  files  notes  browser  calculator  system");
          break;

        case "date":
          term.print(new Date().toLocaleString("es-MX", { dateStyle: "full", timeStyle: "medium" }));
          break;

        case "whoami":
          term.print("renova@seresarte-v-os");
          break;

        case "neofetch":
          term.print(`SERESARTE V-OS ${VERSION}
Host: navegador moderno
Shell: renova-sh
FS: localStorage virtual
Directorio: ${state.cwd}
Apps: Terminal, Archivos, Notas, Navegador, Calculadora, Sistema
Modo: ordenador virtual web simulado`);
          break;

        case "export":
          term.print(JSON.stringify(state, null, 2));
          break;

        case "reset":
          resetState();
          break;

        case "clear":
          term.clear();
          break;

        default:
          term.print(`Comando no reconocido: ${command}. Escribe help.`);
      }
    } catch (error) {
      term.print(`Error: ${error.message}`);
    }
  }

  function requireArg(tokens, usage) {
    const value = tokens.shift();
    if (!value) throw new Error(usage);
    return value;
  }

  function formatDirectory(path) {
    const item = getNode(path);
    if (!item || item.type !== "dir") throw new Error(`No es directorio: ${path}`);
    if (!item.children.length) return "(vacio)";
    return item.children
      .map((child) => {
        const childPath = resolvePath(child, path);
        const childNode = getNode(childPath);
        return childNode && childNode.type === "dir" ? `${child}/` : child;
      })
      .join("  ");
  }

  function renderTree(path, prefix = "") {
    const normalized = normalizePath(path);
    const item = getNode(normalized);
    if (!item) throw new Error(`No existe: ${normalized}`);
    const label = normalized === "/" ? "/" : `${basename(normalized)}${item.type === "dir" ? "/" : ""}`;
    let output = `${prefix}${label}`;
    if (item.type === "dir") {
      for (const child of item.children) {
        output += `\n${renderTree(resolvePath(child, normalized), `${prefix}  `)}`;
      }
    }
    return output;
  }

  function notifyFileChanged(path) {
    saveState();
    refreshFilesIfOpen(dirname(path));
    refreshNotesIfOpen();
    refreshSystemIfOpen();
  }

  function refreshFilesIfOpen(path = state.fileBrowserPath) {
    const win = openWindows.get("files");
    if (win) renderFiles(win.querySelector(".window-body"), path);
  }

  function refreshNotesIfOpen() {
    const win = openWindows.get("notes");
    if (win) renderNotes(win.querySelector(".window-body"));
  }

  function refreshSystemIfOpen() {
    const win = openWindows.get("system");
    if (win) renderSystem(win.querySelector(".window-body"));
  }

  function renderFiles(body, currentPath = state.fileBrowserPath) {
    let current = normalizePath(currentPath || HOME);
    if (!isDir(current)) current = HOME;
    state.fileBrowserPath = current;
    saveState();

    body.innerHTML = `
      <div class="toolbar">
        <button data-action="home">Home</button>
        <button data-action="up">Subir</button>
        <button data-action="new-file">Nuevo archivo</button>
        <button data-action="new-dir">Nuevo directorio</button>
        <button data-action="refresh">Actualizar</button>
      </div>
      <div class="pathline"><strong>Ruta:</strong><span class="muted">${escapeHTML(current)}</span></div>
      <div class="file-list" data-testid="file-list"></div>
    `;

    const list = body.querySelector(".file-list");
    const item = getNode(current);

    if (!item.children.length) {
      const empty = document.createElement("div");
      empty.className = "panel muted";
      empty.textContent = "Directorio vacio";
      list.appendChild(empty);
    }

    for (const child of item.children) {
      const childPath = resolvePath(child, current);
      const childNode = getNode(childPath);
      if (!childNode) continue;
      const row = document.createElement("div");
      row.className = "file-row";
      row.dataset.path = childPath;

      const name = document.createElement("div");
      name.className = "file-name";
      name.textContent = childNode.type === "dir" ? `${child}/` : child;
      row.appendChild(name);

      const actions = document.createElement("div");
      actions.className = "file-row-actions";
      row.appendChild(actions);

      const openButton = makeButton(childNode.type === "dir" ? "Abrir" : "Editar", () => {
        if (childNode.type === "dir") {
          renderFiles(body, childPath);
        } else {
          state.notesFile = childPath;
          saveState();
          openApp("notes");
        }
      });
      actions.appendChild(openButton);

      const readButton = makeButton("Leer", () => {
        alert(childNode.type === "dir" ? childNode.children.join("\n") : childNode.content);
      });
      actions.appendChild(readButton);

      const deleteButton = makeButton("Borrar", () => {
        if (!confirm(`Borrar ${childPath}?`)) return;
        removePath(childPath, true);
        saveState();
        renderFiles(body, current);
        refreshNotesIfOpen();
        refreshSystemIfOpen();
      });
      actions.appendChild(deleteButton);
      list.appendChild(row);
    }

    body.querySelector('[data-action="home"]').addEventListener("click", () => renderFiles(body, HOME));
    body.querySelector('[data-action="up"]').addEventListener("click", () => renderFiles(body, dirname(current)));
    body.querySelector('[data-action="refresh"]').addEventListener("click", () => renderFiles(body, current));
    body.querySelector('[data-action="new-file"]').addEventListener("click", () => {
      const name = prompt("Nombre del archivo:", "nuevo.txt");
      if (!name) return;
      createFile(resolvePath(name, current), "");
      saveState();
      renderFiles(body, current);
      refreshSystemIfOpen();
    });
    body.querySelector('[data-action="new-dir"]').addEventListener("click", () => {
      const name = prompt("Nombre del directorio:", "nuevo");
      if (!name) return;
      createDir(resolvePath(name, current));
      saveState();
      renderFiles(body, current);
      refreshSystemIfOpen();
    });
  }

  function makeButton(label, handler) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", handler);
    return button;
  }

  function renderNotes(body) {
    if (!isFile(state.notesFile)) state.notesFile = `${HOME}/notas.txt`;
    const files = listFilePaths();
    const file = state.notesFile;
    const content = getNode(file).content;

    body.innerHTML = `
      <div class="editor-layout">
        <div class="toolbar">
          <button data-action="save" data-testid="notes-save">Guardar</button>
          <button data-action="new">Nuevo</button>
          <button data-action="download">Descargar</button>
        </div>
        <div class="notes-picker">
          <select class="select" data-testid="notes-file-select" aria-label="Archivo de notas"></select>
          <button class="primary-button" data-action="open-path">Abrir ruta</button>
        </div>
        <textarea class="editor" data-testid="notes-editor" spellcheck="true"></textarea>
      </div>
    `;

    const select = body.querySelector(".select");
    const editor = body.querySelector(".editor");
    for (const path of files) {
      const option = document.createElement("option");
      option.value = path;
      option.textContent = path;
      option.selected = path === file;
      select.appendChild(option);
    }
    editor.value = content;

    const saveNote = () => {
      getNode(state.notesFile).content = editor.value;
      saveState();
      setStatus(`Guardado ${state.notesFile}`);
      refreshFilesIfOpen();
      refreshSystemIfOpen();
    };

    body.querySelector('[data-action="save"]').addEventListener("click", saveNote);
    editor.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveNote();
      }
    });

    select.addEventListener("change", () => {
      state.notesFile = select.value;
      saveState();
      renderNotes(body);
    });

    body.querySelector('[data-action="new"]').addEventListener("click", () => {
      const path = prompt("Ruta del nuevo archivo:", `${HOME}/nueva-nota.txt`);
      if (!path) return;
      state.notesFile = createFile(resolvePath(path), "");
      saveState();
      renderNotes(body);
      refreshFilesIfOpen(dirname(state.notesFile));
      refreshSystemIfOpen();
    });

    body.querySelector('[data-action="open-path"]').addEventListener("click", () => {
      const path = prompt("Ruta del archivo:", state.notesFile);
      if (!path) return;
      const resolved = resolvePath(path);
      if (!isFile(resolved)) {
        alert(`No es archivo: ${resolved}`);
        return;
      }
      state.notesFile = resolved;
      saveState();
      renderNotes(body);
    });

    body.querySelector('[data-action="download"]').addEventListener("click", () => {
      downloadText(basename(state.notesFile), editor.value, "text/plain");
    });
  }

  function renderBrowser(body) {
    body.innerHTML = `
      <div class="browser-shell">
        <div class="browser-address">
          <input class="input" data-testid="browser-address" aria-label="Direccion interna" spellcheck="false">
          <button class="primary-button" data-action="go">Ir</button>
        </div>
        <div class="toolbar">
          <button data-url="seresarte://home">Inicio</button>
          <button data-url="seresarte://apps">Apps</button>
          <button data-url="seresarte://fs">FS</button>
          <button data-url="/system/about.txt">Acerca</button>
          <button data-url="/system/limits.txt">Limites</button>
        </div>
        <pre class="browser-view" data-testid="browser-view"></pre>
      </div>
    `;

    const input = body.querySelector(".input");
    const view = body.querySelector(".browser-view");
    input.value = state.browserAddress || "seresarte://home";

    const navigate = (address) => {
      const value = String(address || "seresarte://home").trim() || "seresarte://home";
      state.browserAddress = value;
      input.value = value;
      view.textContent = renderInternalPage(value);
      saveState();
    };

    body.querySelector('[data-action="go"]').addEventListener("click", () => navigate(input.value));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") navigate(input.value);
    });
    body.querySelectorAll("[data-url]").forEach((button) => {
      button.addEventListener("click", () => navigate(button.dataset.url));
    });

    navigate(input.value);
  }

  function renderInternalPage(address) {
    if (address === "seresarte://home") {
      return `SERESARTE V-OS

Sistema operativo web simulado para RENOVA/SERESARTE.

Rutas utiles:
  seresarte://apps
  seresarte://fs
  /home/renova/README.md
  /system/about.txt`;
    }

    if (address === "seresarte://apps") {
      return Object.entries(appConfig)
        .map(([id, config]) => `${id.padEnd(12)} ${config.title}`)
        .join("\n");
    }

    if (address === "seresarte://fs") {
      return renderTree("/");
    }

    if (/^https?:\/\//i.test(address)) {
      return `Navegador simulado

URL solicitada:
${address}

Este prototipo no hace peticiones web. Usa rutas internas, por ejemplo /home/renova/README.md.`;
    }

    const path = address.startsWith("file://") ? address.replace(/^file:\/\//, "") : address;
    const resolved = path.startsWith("/") ? normalizePath(path) : resolvePath(path);
    const item = getNode(resolved);
    if (!item) return `No existe: ${resolved}`;
    if (item.type === "dir") return `${resolved}\n\n${formatDirectory(resolved)}`;
    return item.content;
  }

  function renderCalculator(body) {
    body.innerHTML = `
      <div class="calc">
        <input class="calc-display" data-testid="calc-display" aria-label="Expresion" spellcheck="false">
        <div class="calc-grid" data-testid="calc-grid"></div>
        <div class="panel muted">Operadores: + - * / % ( ) .</div>
      </div>
    `;

    const display = body.querySelector(".calc-display");
    const grid = body.querySelector(".calc-grid");
    const keys = ["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "%", "+", "(", ")", "DEL", "C", "="];

    for (const key of keys) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "calc-key";
      button.textContent = key;
      if (key === "=") button.dataset.role = "equals";
      if (key === "C") button.dataset.role = "clear";
      button.addEventListener("click", () => handleCalcKey(display, key));
      grid.appendChild(button);
    }

    display.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        calculate(display);
      }
    });
  }

  function handleCalcKey(display, key) {
    if (key === "C") {
      display.value = "";
      return;
    }
    if (key === "DEL") {
      display.value = display.value.slice(0, -1);
      return;
    }
    if (key === "=") {
      calculate(display);
      return;
    }
    display.value += key;
  }

  function calculate(display) {
    const expression = display.value.trim();
    try {
      const result = window.RenovaCalculator.evaluate(expression);
      display.value = String(result);
    } catch {
      display.value = "Error";
    }
  }

  function renderSystem(body) {
    const files = Object.values(state.fs).filter((item) => item.type === "file").length;
    const dirs = Object.values(state.fs).filter((item) => item.type === "dir").length;
    const bytes = new Blob([JSON.stringify(state)]).size;

    body.innerHTML = `
      <div class="system-grid">
        <section>
          <h3>Estado</h3>
          <p><span class="status-dot"></span>Sistema listo</p>
          <p><strong>Version:</strong> ${VERSION}</p>
          <p><strong>Usuario:</strong> renova</p>
          <p><strong>Ruta:</strong> <span class="muted">${escapeHTML(state.cwd)}</span></p>
        </section>
        <section>
          <h3>Almacenamiento</h3>
          <p><strong>Archivos:</strong> ${files}</p>
          <p><strong>Directorios:</strong> ${dirs}</p>
          <p><strong>Estado:</strong> ${bytes} bytes aprox.</p>
          <p><strong>Backend:</strong> localStorage</p>
        </section>
        <section>
          <h3>Acciones</h3>
          <div class="toolbar">
            <button data-action="export">Exportar</button>
            <button data-action="import">Importar</button>
            <button data-action="reset">Reiniciar</button>
          </div>
          <input type="file" id="stateImport" accept="application/json" hidden>
        </section>
        <section>
          <h3>Apps</h3>
          <p>Terminal, Archivos, Notas, Navegador, Calculadora, Sistema.</p>
        </section>
      </div>
    `;

    body.querySelector('[data-action="export"]').addEventListener("click", () => {
      downloadText("seresarte-v-os-state.json", JSON.stringify(state, null, 2), "application/json");
    });

    body.querySelector('[data-action="import"]').addEventListener("click", () => {
      body.querySelector("#stateImport").click();
    });

    body.querySelector("#stateImport").addEventListener("change", async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      try {
        const parsed = JSON.parse(await file.text());
        if (!parsed.fs) throw new Error("Estado invalido");
        state = migrateState(parsed);
        saveState();
        location.reload();
      } catch (error) {
        alert(`No se pudo importar: ${error.message}`);
      }
    });

    body.querySelector('[data-action="reset"]').addEventListener("click", () => {
      if (confirm("Reiniciar SERESARTE V-OS y borrar localStorage?")) resetState();
    });
  }

  function downloadText(filename, text, mime) {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#039;"
    }[char]));
  }

  document.querySelectorAll("[data-open]").forEach((button) => {
    button.addEventListener("click", () => openApp(button.dataset.open));
  });

  window.addEventListener("resize", () => {
    for (const win of openWindows.values()) boundWindow(win);
  });

  updateClock();
  window.setInterval(updateClock, 20_000);
  boot();
})();
