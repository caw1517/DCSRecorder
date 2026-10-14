# Desktop shell for the companion

Researched 2026-10-13 for [#48](https://github.com/caw1517/DCSRecorder/issues/48) (part of #47, blocking #57). Question: which desktop shell should host the companion as a standalone Windows app for public DCS World players? The app needs its own window, no console, an installer and a Start Menu shortcut.

## Recommendation

**Use pywebview (WebView2 backend), freeze with PyInstaller `--onedir --windowed`, and ship a per-user Inno Setup installer that checks for WebView2.** Sign releases once there is a public audience.

The companion is a Python backend serving a single plain HTML/JS page. pywebview is the only option that keeps that stack exactly as it is. It adds one Python dependency and one window call, and needs no second language, toolchain or process. It also ships no browser engine, because WebView2 is already on Windows 11 and nearly all Windows 10 machines. Tauri gets the same small webview, but it adds Rust, a sidecar process and its lifecycle, and a frozen Python binary anyway. Electron and Qt WebEngine each bundle their own Chromium, so they ship much more for no benefit to this UI.

## What the companion is today (repo facts)

- `companion/app.py`: stdlib `ThreadingHTTPServer` on `127.0.0.1` with a random port. It checks the `Host` header, and POSTs need an `X-Recorder-Token` that is injected into `index.html`. Responses carry a nonce CSP. A single-instance lock uses `msvcrt.locking` on `companion.lock`; a second launch re-opens the URL saved in `companion-url.txt`. The browser opens via `webbrowser.open`.
- `companion/index.html`: one page of plain JS/CSS that uses `fetch` against `/api/*`. The authored-mission path is a **typed text input** (`#authoredPath`, placeholder `C:\Users\you\Saved Games\DCS\Missions\My scene.miz`), so there is no file picker today.
- `companion/Start-DCSRecorder.ps1`: runs `Start-Process` with a local `python` path from `companion-launch.json`, using `-WindowStyle Hidden`.
- `library.py` already starts child processes (`tasklist.exe`, `luae.exe`) with `CREATE_NO_WINDOW`, so a windowed build will not flash consoles from them.
- Local Python is 3.14.3.

## Options compared

| | pywebview | Tauri + Python sidecar | Electron + Python sidecar | Qt / PySide6 (QtWebEngine) |
|---|---|---|---|---|
| Web engine | System WebView2 (Edge Chromium) | System WebView2 | Bundled Chromium + Node | Bundled Chromium (QtWebEngine) |
| Extra languages/toolchains | None (Python) | Rust + Node/npm CLI | Node/npm | None (Python), Qt tooling |
| Processes | 1 Python process (+ WebView2's own) | Rust host + frozen Python sidecar | Electron + frozen Python sidecar | 1 Python process + QtWebEngineProcess |
| Reuse `index.html` + `app.py` | As is: point the window at `http://127.0.0.1:<port>/` | As is, with sidecar start/stop and port handoff | As is, with sidecar start/stop and port handoff | As is in a `QWebEngineView`, or rewrite as native widgets |
| Native file picker | `window.create_file_dialog(FileDialog.OPEN, file_types=...)` from Python | Dialog plugin (JS/Rust) | `dialog.showOpenDialog` | `QFileDialog` |
| Installer | Not included; use Inno Setup/NSIS/WiX | Built in: NSIS `-setup.exe` or WiX `.msi` | Electron Forge makers (Squirrel.Windows, etc.) | Not included; use Inno Setup/NSIS/WiX |
| Size driver | Python runtime + pythonnet; no browser | Tiny host + frozen Python | Chromium + Node + frozen Python | Qt + Chromium resources + Python |

Sizes and startup times were **not measured** in this research (see Open questions). The table records only what the sources state about what each option bundles.

### pywebview

- On Windows the renderer order is `edgechromium` first. EdgeChromium needs ".NET Framework 4.6.2 and Edge Runtime installed". [pywebview: web engine](https://pywebview.flowrl.com/guide/web_engine.html)
- Version 6.2.1 (15 Apr 2026), BSD-3-Clause, `requires-python >=3.10`. [PyPI](https://pypi.org/project/pywebview/) Its Windows dependency is `pythonnet`, and it also pulls `bottle` and `proxy_tools`. [pyproject.toml](https://github.com/r0x0r/pywebview/blob/master/pyproject.toml) The trove classifiers stop at 3.13, but pythonnet 3.2.1 (8 Oct 2026) ships wheels for CPython 3.11–3.15. [PyPI: pythonnet](https://pypi.org/project/pythonnet/) **Running on 3.14 is plausible but unverified.**
- API ([pywebview API](https://pywebview.flowrl.com/api/)):
  - `create_window(title, url=None, html=None, js_api=None, ...)` accepts a URL, so the existing loopback server can be loaded unchanged.
  - `window.create_file_dialog(dialog_type=FileDialog.OPEN, directory='', allow_multiple=False, save_filename='', file_types=())` returns the chosen paths, or `None` if the user cancels. `file_types` use the form `"Description (*.ext)"`.
  - `js_api` / `window.expose` make Python callables available as `window.pywebview.api.*` and return promises.
  - `webview.start(..., private_mode=True, storage_path=None)` keeps nothing between sessions by default.
- Packaging: the docs recommend PyInstaller on Windows and say Nuitka also works. PyInstaller "picks all the dependencies found in pywebview, even if you don't use them", so exclude unused backends such as Qt in the spec file. [pywebview: freezing](https://pywebview.flowrl.com/guide/freezing.html)
- pywebview creates a session token for its own built-in server (`webview.token`). [pywebview: security](https://pywebview.flowrl.com/guide/security.html) We keep our own server and token, so this doesn't matter for us.

**Fit:** `app.py` already has the right shape. The change is to run `serve()` on a background thread instead of calling `webbrowser.open`, then call `webview.create_window(url)` and `webview.start()` on the main thread. The `Host` check, token and CSP keep working because the page is still served from `127.0.0.1:<port>`. A small `js_api` method such as `pick_mission()` calls `create_file_dialog` with `('DCS mission (*.miz)',)` and fills `#authoredPath`. That removes the hand-typed path, which matters for public players.

### Tauri v2 + Python sidecar

- Tauri is "a framework for building tiny, fast binaries" that uses "the web view already available on every user's system". The docs say a minimal app "can be less than 600KB". [Tauri: start](https://v2.tauri.app/start/)
- Sidecars are declared in `bundle.externalBin`. Each one needs a copy with a target-triple suffix and `shell:allow-execute`/`allow-spawn` capability grants. The docs name "Python CLI applications or API servers bundled using `pyinstaller`" as a use case but give no Python-specific steps. [Tauri: sidecar](https://v2.tauri.app/develop/sidecar/)
- Installers are built in: WiX `.msi` (Windows-only build) or NSIS `-setup.exe`. NSIS defaults to per-user under `%LOCALAPPDATA%` with no admin. WebView2 modes are `downloadBootstrapper` (default, +0 MB), `embedBootstrapper` (~1.8 MB), `offlineInstaller` (~127 MB) and `fixedRuntime` (~180 MB). [Tauri: Windows installer](https://v2.tauri.app/distribute/windows-installer/)

**Fit:** you still freeze Python with PyInstaller, then add a Rust project and Node CLI on top. You also have to own sidecar spawn and kill, pass the random port and token to the webview, and decide which side holds the single-instance lock. The installer is the best of the four, but Inno Setup provides the same (below). Choose Tauri only if a non-Python host is wanted later.

### Electron + Python sidecar

- Electron works "by embedding Chromium and Node.js into its binary". [Electron docs](https://www.electronjs.org/docs/latest/) The docs recommend Electron Forge for packaging. [Electron: distribution](https://www.electronjs.org/docs/latest/tutorial/application-distribution)
- Forge's Squirrel.Windows maker is "a no-prompt, no-hassle, no-admin method" that produces `Setup.exe` plus update `.nupkg`/`RELEASES`. It has caveats with spaces in app names and extra app launches during install and update. [Electron Forge: Squirrel.Windows](https://www.electronforge.io/config/makers/squirrel.windows)

**Fit:** it has the same sidecar work as Tauri, and also ships a full Chromium and Node runtime that this UI doesn't need. It is the largest download with no matching benefit.

### Qt for Python (PySide6)

- `pyside6-deploy` "is a wrapper around Nuitka". Since 6.12 it defaults to a folder (standalone) build, and `--mode onefile` is optional. [Qt: pyside6-deploy](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)
- QtWebEngine deployment needs `QtWebEngineProcess.exe`, the Chromium `.pak` resources, `icudtl.dat`, `v8_context_snapshot.bin`, locale `.pak` files and VC++ Redistributable 14.28 or later. [Qt WebEngine: deploying](https://doc-snapshots.qt.io/qtwebengine/qtwebengine-deploying.html)

**Fit:** keeping the HTML UI means shipping Qt plus a second Chromium. Using native widgets instead means rewriting `index.html`. Either way it costs more than pywebview, and LGPL compliance adds to the burden.

## Bundling and installer pieces (shared by any Python option)

- **PyInstaller.** Version 6.22.3; Python 3.14 support since 6.15.0 and 3.15 since 6.21.0. [PyInstaller](https://pyinstaller.org/en/stable/), [changelog](https://pyinstaller.org/en/stable/CHANGES.html)
  - `--windowed`/`--noconsole` means no console window.
  - `--onedir` is the default. `--onefile` extracts to a temp `_MEIxxxxxx` folder on every start, and the docs warn that "large applications may have long extraction/startup times".
  - `--icon file.ico` sets the exe icon. [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html)
  - Use **`--onedir`** behind an installer.
- **Nuitka** is the alternative. It supports Python 3.4–3.14. `--windows-console-mode=disable` suppresses the console, and the build modes are `--mode=standalone|onefile|app`. [Nuitka manual](https://nuitka.net/user-documentation/user-manual.html) It is slower to build but compiles to C. Keep it as a fallback if PyInstaller output trips antivirus heuristics; that claim is not covered by the sources above.
- **Inno Setup** is free "for any purpose, including commercial applications". [license](https://jrsoftware.org/files/is/license.txt) It supports administrative and non-administrative installs, shortcuts "anywhere, including in the Start Menu and on the desktop", and "complete uninstall". [Inno Setup](https://jrsoftware.org/isinfo.php) A per-user install (`PrivilegesRequired=lowest`) avoids UAC, and an `[Icons]` entry adds the Start Menu shortcut.
- **WebView2 runtime.** Microsoft says the Evergreen runtime "will be included as part of the Windows 11 operating system" and that "the vast majority of Windows 10 devices have the WebView2 Runtime installed already". Apps should still check before use. [Microsoft: WebView2 distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)
  - The check reads registry value `pv` under `...\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` (HKLM WOW6432Node or HKCU).
  - If it is missing, run the ~2 MB bootstrapper `MicrosoftEdgeWebview2Setup.exe /silent /install`. Without elevation it installs per-user.
  - The Fixed Version runtime is "over 250 MB". Avoid it.
- **MSIX / Microsoft Store.** Store-distributed apps "are never subject to SmartScreen download warnings". [Microsoft: SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation) MSIX can declare WebView2 as a dependency. [WebView2 distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution) However, the companion writes into `Saved Games\DCS\Scripts\Hooks` and the DCS install, and its library lives beside them. Check how packaged-app file virtualisation interacts with that before choosing MSIX. This is out of scope here; prefer Inno Setup first.
- **Signing / SmartScreen.**
  - Unsigned or self-signed: "Windows protected your PC", and the user must choose "Run anyway".
  - OV/EV signed: still flagged as unrecognised until reputation builds. "EV certificates no longer bypass SmartScreen."
  - Microsoft recommends Artifact Signing (formerly Trusted Signing), "starts at $9.99/month".
  - On Windows 11, Smart App Control "will block execution of unsigned files unless the file has a positive reputation". [Microsoft: SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
  - This applies equally to every shell option, so it doesn't change the recommendation. It is a release cost for public players.

## Fit with #8 (portable distribution)

#8 was closed as deferred on 8 Oct 2026. The planning direction it recorded:

- trusted testers first;
- an installer with uninstall and rollback;
- a check of the DCS build and hashes before install and preparation;
- a diagnostics bundle;
- never shipping stock Hornet or ED files, but copying them from each user's own DCS install.

All of that logic is Python in `library.py`/`setups.py`/`inventory.py`. The pywebview + PyInstaller + Inno route keeps it in one process. The installer only lays down the frozen app, shortcut and uninstaller. The companion itself does the DCS-side install, build check and rollback at first run, where it can show refusals in the UI. This keeps ED assets out of the installer. Tauri and Electron would split that across a Rust or Node host and a Python sidecar without simplifying it.

The shell choice does **not** settle #8's open redistribution question: the controller DLL compiles `ED_FM_Template.cpp` and embeds `DCS.exe` byte patterns. That question still has to be decided before a public installer ships.

The hard-coded paths listed in #8 (`D:/DCS World`, `E:/Projects/...`, `C:\Users\w_can`) and `companion-launch.json`'s local `python` path must go. A frozen app finds its own files via `sys._MEIPASS`/the exe directory, and has to discover DCS and Saved Games itself.

## Implementation notes for the follow-up

1. Refactor `serve()` so it returns the bound server and URL, without blocking or opening a browser. Run `serve_forever` on a daemon thread. Call `webview.create_window('DCS Recorder', url)` and then `webview.start(private_mode=True)` on the main thread, and shut the server down when the window closes.
2. Single instance: today a second launch calls `webbrowser.open(saved_url)`. With a window it should instead bring the existing window to the front. Two ways to do this: a small loopback `POST /api/focus` (token-protected) handled with `window.restore()`/`show()`, or a named mutex plus `FindWindow`. Never open a browser tab as a fallback, or users get two UIs.
3. File picker: expose `pick_mission()` via `js_api`, and keep the text input as a fallback.
4. Freeze with PyInstaller `--onedir --windowed --icon`, adding `index.html`, `recording_sink.lua` and the other Lua and payload files via `--add-data`. Exclude unused pywebview backends.
5. Write an Inno Setup script: per-user, Start Menu shortcut, uninstaller, WebView2 registry check plus the bundled ~2 MB bootstrapper.
6. Settings: replace `--settings <json>` from the PowerShell launcher with a default location under `%LOCALAPPDATA%\DCSRecorder`, plus first-run discovery of DCS and Saved Games.

## Open questions (not answered by sources)

- **Measured size and cold-start time** of a frozen pywebview build on Python 3.14 against the current Start-DCSRecorder.ps1 + browser launch. A one-hour spike settles this, and it should also confirm that pywebview 6.2.1 + pythonnet 3.2.1 run on 3.14, since pywebview's classifiers list up to 3.13 only.
- Whether PyInstaller onedir output triggers Defender or SmartScreen false positives for this app before it is signed.
- Whether MSIX/Store distribution can write to `Saved Games\DCS` and the DCS install directory without breaking the hook install.
