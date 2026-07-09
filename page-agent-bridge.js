(() => {
  "use strict";

  const BRIDGE_ID = "renova-page-agent-bridge";
  const STYLE_ID = "renova-page-agent-bridge-style";
  const DEMO_CONFIG = {
    model: "qwen3.5-plus",
    baseURL: "https://page-ag-testing-ohftxirgbn.cn-shanghai.fcapp.run",
    apiKey: "NA",
    language: "en-US"
  };

  const examples = [
    "Open the terminal and run help",
    "Open the files app and inspect the home folder",
    "Open the system app and explain the current state",
    "Read the virtual desktop and summarize what I can do here"
  ];

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      #${BRIDGE_ID} {
        position: fixed;
        right: 18px;
        bottom: 82px;
        z-index: 180;
        width: min(360px, calc(100vw - 32px));
        color: #f4eee1;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      #${BRIDGE_ID} .pa-shell {
        border: 1px solid rgba(244, 238, 225, 0.2);
        border-radius: 10px;
        background: rgba(7, 8, 11, 0.9);
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42);
        backdrop-filter: blur(16px);
        overflow: hidden;
      }

      #${BRIDGE_ID} .pa-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 10px 12px;
        border-bottom: 1px solid rgba(244, 238, 225, 0.14);
        background: rgba(17, 20, 26, 0.92);
      }

      #${BRIDGE_ID} .pa-title {
        display: grid;
        gap: 2px;
        min-width: 0;
      }

      #${BRIDGE_ID} .pa-title strong {
        font-size: 13px;
        line-height: 1.2;
      }

      #${BRIDGE_ID} .pa-title span,
      #${BRIDGE_ID} .pa-status,
      #${BRIDGE_ID} .pa-hint {
        color: #b8b1a4;
        font-size: 11px;
        line-height: 1.35;
      }

      #${BRIDGE_ID} .pa-body {
        display: grid;
        gap: 10px;
        padding: 12px;
      }

      #${BRIDGE_ID} textarea {
        width: 100%;
        min-height: 92px;
        resize: vertical;
        border: 1px solid rgba(244, 238, 225, 0.18);
        border-radius: 8px;
        background: rgba(17, 20, 26, 0.95);
        color: #f4eee1;
        padding: 10px;
        outline: 0;
      }

      #${BRIDGE_ID} textarea:focus {
        border-color: rgba(200, 164, 81, 0.7);
      }

      #${BRIDGE_ID} .pa-actions,
      #${BRIDGE_ID} .pa-examples {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      #${BRIDGE_ID} button {
        border: 1px solid rgba(244, 238, 225, 0.18);
        border-radius: 8px;
        background: rgba(244, 238, 225, 0.08);
        color: #f4eee1;
        padding: 7px 9px;
        cursor: pointer;
        font-size: 12px;
      }

      #${BRIDGE_ID} button:hover,
      #${BRIDGE_ID} button:focus-visible {
        border-color: rgba(200, 164, 81, 0.75);
        outline: 0;
      }

      #${BRIDGE_ID} button.primary {
        border-color: rgba(200, 164, 81, 0.75);
        background: rgba(200, 164, 81, 0.18);
      }

      #${BRIDGE_ID} button.icon {
        width: 30px;
        height: 30px;
        display: grid;
        place-items: center;
        padding: 0;
      }

      #${BRIDGE_ID}.is-collapsed {
        width: auto;
      }

      #${BRIDGE_ID}.is-collapsed .pa-shell {
        display: none;
      }

      #${BRIDGE_ID} .pa-launcher {
        display: none;
        border-color: rgba(200, 164, 81, 0.75);
        background: rgba(7, 8, 11, 0.92);
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42);
        font-weight: 700;
      }

      #${BRIDGE_ID}.is-collapsed .pa-launcher {
        display: block;
      }
    `;
    document.head.appendChild(style);
  }

  function setDesktopStatus(message) {
    const status = document.getElementById("statusText");
    if (status) status.textContent = message;
  }

  function waitForPageAgent(timeoutMs = 10_000) {
    const startedAt = Date.now();
    return new Promise((resolve, reject) => {
      const tick = () => {
        if (window.pageAgent) {
          resolve(window.pageAgent);
          return;
        }

        if (window.PageAgent) {
          try {
            window.pageAgent = new window.PageAgent(DEMO_CONFIG);
            resolve(window.pageAgent);
            return;
          } catch {
            /* Keep polling while the IIFE bundle finishes mounting. */
          }
        }

        if (Date.now() - startedAt > timeoutMs) {
          reject(new Error("Page Agent no se cargó. Revisa la conexión al CDN o usa npm install page-agent."));
          return;
        }

        window.setTimeout(tick, 160);
      };
      tick();
    });
  }

  function createBridge() {
    if (document.getElementById(BRIDGE_ID)) return;
    injectStyles();

    const root = document.createElement("aside");
    root.id = BRIDGE_ID;
    root.setAttribute("aria-label", "Page Agent para SERESARTE V-OS");
    root.innerHTML = `
      <button class="pa-launcher" type="button" aria-label="Abrir Page Agent">Page Agent</button>
      <div class="pa-shell">
        <header class="pa-header">
          <div class="pa-title">
            <strong>Page Agent · RENOVA</strong>
            <span>Agente GUI dentro del escritorio web</span>
          </div>
          <button class="icon" type="button" data-action="collapse" aria-label="Minimizar">_</button>
        </header>
        <div class="pa-body">
          <textarea data-role="prompt" spellcheck="true" placeholder="Ejemplo: Open the terminal and run help"></textarea>
          <div class="pa-actions">
            <button class="primary" type="button" data-action="run">Ejecutar</button>
            <button type="button" data-action="show-panel">Panel oficial</button>
            <button type="button" data-action="clear">Limpiar</button>
          </div>
          <div class="pa-examples" data-role="examples"></div>
          <div class="pa-status" data-role="status">Cargando Page Agent...</div>
          <div class="pa-hint">Usa instrucciones breves en inglés para mayor precisión. El demo usa el LLM de prueba público de Page Agent; no pegues secretos.</div>
        </div>
      </div>
    `;

    document.body.appendChild(root);

    const prompt = root.querySelector('[data-role="prompt"]');
    const status = root.querySelector('[data-role="status"]');
    const runButton = root.querySelector('[data-action="run"]');
    const examplesBox = root.querySelector('[data-role="examples"]');

    function setStatus(message) {
      status.textContent = message;
      setDesktopStatus(message);
    }

    function setBusy(isBusy) {
      root.querySelectorAll("button, textarea").forEach((el) => {
        if (el.classList.contains("pa-launcher")) return;
        el.disabled = isBusy;
      });
    }

    examples.forEach((example) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = example;
      button.addEventListener("click", () => {
        prompt.value = example;
        prompt.focus();
      });
      examplesBox.appendChild(button);
    });

    root.querySelector('[data-action="collapse"]').addEventListener("click", () => {
      root.classList.add("is-collapsed");
    });

    root.querySelector(".pa-launcher").addEventListener("click", () => {
      root.classList.remove("is-collapsed");
      prompt.focus();
    });

    root.querySelector('[data-action="clear"]').addEventListener("click", () => {
      prompt.value = "";
      prompt.focus();
    });

    root.querySelector('[data-action="show-panel"]').addEventListener("click", async () => {
      try {
        const agent = await waitForPageAgent();
        if (agent.panel && typeof agent.panel.show === "function") {
          agent.panel.show();
          setStatus("Panel oficial de Page Agent abierto.");
        } else {
          setStatus("Page Agent está cargado, pero el panel oficial no está disponible en este bundle.");
        }
      } catch (error) {
        setStatus(error.message);
      }
    });

    async function runPrompt() {
      const command = prompt.value.trim();
      if (!command) {
        setStatus("Escribe una instrucción para Page Agent.");
        prompt.focus();
        return;
      }

      setBusy(true);
      setStatus("Ejecutando Page Agent...");
      try {
        const agent = await waitForPageAgent();
        if (typeof agent.execute !== "function") {
          throw new Error("La instancia de Page Agent no expone execute().");
        }
        const result = await agent.execute(command);
        const resultText = result ? ` Resultado: ${typeof result === "string" ? result : JSON.stringify(result)}` : "";
        setStatus(`Page Agent terminó.${resultText}`);
      } catch (error) {
        setStatus(`Error Page Agent: ${error.message}`);
      } finally {
        setBusy(false);
      }
    }

    runButton.addEventListener("click", runPrompt);
    prompt.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        runPrompt();
      }
    });

    waitForPageAgent()
      .then(() => setStatus("Page Agent listo."))
      .catch((error) => setStatus(error.message));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createBridge, { once: true });
  } else {
    createBridge();
  }
})();
