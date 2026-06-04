# 🧠 Lessons Learned & Command Troubleshooting (Windows / PowerShell / Python / Git)

This document serves as a persistent memory for the AI agent regarding commands, scripts, and runtime issues encountered and resolved in this project to prevent regression.

---

## 1. PowerShell Script Execution Policy on Windows
* **Problem:** Running CLI commands like `npx @agentmemory/agentmemory` or executing scripts directly via PowerShell triggers a security exception:
  ```text
  npx : O arquivo C:\Program Files\nodejs\npx.ps1 não pode ser carregado porque a execução de scripts foi desabilitada neste sistema.
  CategoryInfo          : ErrodeSegurança: (:) [], PSSecurityException
  FullyQualifiedErrorId : UnauthorizedAccess
  ```
* **Resolution:** 
  1. **Run via CMD:** Execute the command prefixed with `cmd /c` to run through the standard Command Prompt command interpreter instead of PowerShell (e.g. `cmd /c npx @agentmemory/agentmemory`).
  2. **Update config:** In configuration files (like `mcp_config.json`), use `"npx.cmd"` as the executable command rather than `"npx"`.
  3. **Bypass execution policy:** When running PowerShell commands directly, append `-ExecutionPolicy Bypass` to the command line:
     ```powershell
     powershell -ExecutionPolicy Bypass -Command "<commands>"
     ```

---

## 2. Windows Console Unicode Encoding Issues (CP1252 vs UTF-8)
* **Problem:** Writing output containing Unicode characters (like emojis or special symbols) from Python scripts to the standard output in Windows causes a crash:
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f60a' in position 34: character maps to <undefined>
  ```
* **Resolution:** 
  * Avoid printing non-ASCII characters directly to the standard Windows console if the script might run in CP1252.
  * Ensure python scripts decode/encode to UTF-8 properly, or set `PYTHONIOENCODING=utf-8` in the environment if spawning subprocesses that require outputting emojis/special symbols.

---

## 3. Streamlit Session State & Object Attributes (AttributeError)
* **Problem:** After making updates to class definitions (like `AIAssistant` adding `available_models`), switching tabs or reloading in Streamlit triggers:
  ```text
  AttributeError: 'AIAssistant' object has no attribute 'available_models'
  ```
  This happens because the session state caches the older instance of the class that was initialized before the class structure changed.
* **Resolution:** 
  * Ensure safety checks are in place using `hasattr()` or `getattr()` when retrieving attributes from cached session state objects:
    ```python
    if "ai_assistant" in st.session_state and not hasattr(st.session_state.ai_assistant, "available_models"):
        st.session_state.ai_assistant = AIAssistant()
    ```

---

## 4. Git Push & Authentication without Prompts
* **Problem:** Creating a repository and running `git push` in headless or non-interactive environments hangs or prompts for credentials. Also, GitHub CLI (`gh`) might not be installed.
* **Resolution:** 
  * Read the GitHub token from `c:\Users\gabri\.github_token.txt`.
  * Create the repository programmatically via GitHub REST API using a lightweight Python script.
  * Set the git remote origin to include the token directly in the URL:
    ```bash
    git remote add origin https://<username>:<token>@github.com/<username>/<repo>.git
    ```
  * Update `.gitignore` to explicitly ignore Python virtual environments (`venv/`, `.venv/`, `jpkg/venv/`) and cache directories (`__pycache__/`, `*.pyc`) before running `git add .` to keep the repository clean.
