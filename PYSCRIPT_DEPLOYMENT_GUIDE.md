# PyScript Deployment Guide for Desgoblin ASCII

## 1. Module Loading Fix (The Problem Solved)

### What Was Wrong
```html
<!-- ❌ BEFORE - Doesn't work -->
<script type="py" config='{"packages": [], "fetch": [{"from": "./src/", "to_folder": "src", "files": ["**/*.py", "**/*.json"]}]}'>
    from src.main import start_app  <!-- Import path includes 'src.' -->
</script>
```

### Why It Failed
- **Glob patterns**: PyScript doesn't support `**/*.py` recursive patterns in the `fetch` configuration
- **Import path mismatch**: The file was fetched as `src/main.py` but imported as `src.main`
- **Module path confusion**: PyScript needs explicit folder declarations for each directory level

### The Solution
```html
<!-- ✅ AFTER - Works correctly -->
<py-config>
    packages = ["noise"]
    fetch = [
        {"from": "./src", "to_folder": "src", "files": ["*.py", "*.json"]},
        {"from": "./src/battle_system", "to_folder": "src/battle_system", "files": ["*.py"]},
        {"from": "./src/game_system", "to_folder": "src/game_system", "files": ["*.py"]},
        {"from": "./src/map_system", "to_folder": "src/map_system", "files": ["*.py"]},
        {"from": "./src/data", "to_folder": "src/data", "files": ["*.json"]}
    ]
</py-config>

<script type="py">
    import sys
    sys.path.insert(0, "/src")  <!-- Add src to Python path -->
    from main import start_app  <!-- Import without 'src.' prefix -->
</script>
```

**Key Changes:**
- ✅ Each subdirectory must be explicitly listed in `fetch`
- ✅ Use `*.py` (single-level wildcard) instead of `**/*.py` (recursive)
- ✅ Add `/src` to `sys.path` so `from main import` works
- ✅ Import as `from main import` not `from src.main import`

---

## 2. Dependency Management

### Configuring External Packages

Your `requirements.txt` lists:
```
keyboard
noise
```

**Note on `keyboard` package**: The `keyboard` package **cannot run in PyScript** because it requires direct OS/hardware access. PyScript runs in a browser sandbox that doesn't allow this. Remove it from your index.html config.

The `noise` package CAN run in PyScript, so it's included:

```html
<py-config>
    packages = ["noise"]  <!-- PyScript will install this automatically -->
</py-config>
```

### How PyScript Installs Packages

When you specify `packages = ["noise"]`:
1. PyScript's initialization downloads the package metadata from PyPI
2. It fetches the package code (compiled for Pyodide, the Python runtime for WebAssembly)
3. The package is installed into the browser's virtual Python environment
4. This happens **before** your `<script type="py">` code runs

### Adding More Packages

For any new external packages you want to add:

```html
<py-config>
    packages = ["noise", "numpy", "requests"]  <!-- Add package names here -->
    fetch = [
        <!-- ... your fetch config ... -->
    ]
</py-config>
```

**⚠️ Important Limitations:**
- Not all PyPI packages work in PyScript (need Pyodide wheels)
- C-extension packages may not be available
- Use https://pyodide.org/en/stable/packages.html to check if a package is available

### Requirements Import Support

PyScript can also read from a `requirements.txt` file:

```html
<py-config>
    requirements = ["./requirements.txt"]
    fetch = [<!-- ... -->]
</py-config>
```

However, **explicitly listing packages is more reliable** for browser deployments.

---

## 3. Performance: Why PyScript Is Slow on Initial Load

### Load Time Breakdown

When a user opens your GitHub Pages link, here's what happens:

```
1. HTML Download                    ~100ms
   └─ Browser fetches and parses index.html

2. PyScript CDN Load                ~500-1000ms
   ├─ Download pyscript core JS
   ├─ Download Pyodide (7.5-15MB)
   └─ Browser cache helps future visits

3. Python Environment Bootstrap     ~2000-5000ms
   ├─ Initialize WebAssembly runtime
   ├─ Unpack Python 3.11 stdlib (20MB+)
   ├─ Set up file systems
   └─ Initialize garbage collector

4. Package Download & Install       ~500-2000ms
   ├─ Fetch "noise" package from PyPI
   ├─ Compile/install package
   └─ Time varies by package size

5. File Fetching                    ~500-3000ms
   ├─ HTTP requests to download your .py files
   │  (5 parallel requests × avg 500ms each)
   └─ JavaScript unzips/loads files

6. Module Initialization            ~1000-5000ms
   ├─ Python imports all your modules
   ├─ Executes `import` statements
   ├─ Runs module-level code
   └─ Time depends on code complexity

                                    ─────────────
TOTAL FIRST LOAD: 5-17 seconds     (typically 8-12s)
SUBSEQUENT LOADS: 2-3 seconds       (cached Pyodide)
```

### Why Each Step Takes So Long

| Step | Why It's Slow | Optimization |
|------|---------------|--------------|
| **Pyodide (7-15MB)** | First-time download of Python+WASM runtime | Browser caching helps; users only wait once |
| **Python Bootstrap (2-5s)** | Initializing 3.11+ stdlib in WebAssembly | This is unavoidable; lower on subsequent visits |
| **Package Download** | Each external package fetched from PyPI | Minimize dependencies; use lighter packages |
| **File Fetching (5+ requests)** | HTTP overhead for each `fetch` entry | Combine into fewer requests; compress files |
| **Module Loading** | Your code runs at import time | Defer expensive operations; use lazy loading |

### Why Browser-Based Python Is Different

```
Native Python CLI:
  python main.py  →  100-500ms startup

Browser (PyScript):
  1. Download 15MB runtime
  2. Decompress WASM binary
  3. Initialize WebAssembly VM
  4. Boot Python interpreter
  5. Fetch your files
  6. Import and run code
  →  8-12s startup
```

The difference is **order of magnitude** because the runtime doesn't exist until you fetch it.

---

## 4. Debugging Guide: Finding Bottlenecks

### Step 1: Open Browser DevTools

1. Visit your deployed GitHub Pages URL
2. Right-click → **Inspect** or press **F12**
3. Go to the **Console** tab

### Step 2: Monitor Network Activity

Open **Network** tab to see file downloads:

1. Click **Network** tab
2. Reload the page (`Ctrl+R`)
3. Look for these types of requests:

```
Type        URL                                          Size      Time
────────────────────────────────────────────────────────────────────────
js          pyscript.net/.../core.js                    200KB     300ms
wasm        pyodide.org/.../pyodide-core.wasm           7.5MB     2000ms  ← Biggest!
json        pypi.org/pypi/noise/json                    50KB      800ms
py          yourdomain.com/src/main.py                  5KB       100ms
py          yourdomain.com/src/battle_system/*.py       15KB total 300ms
```

**What to look for:**
- ❌ Files showing in red = HTTP errors (404, 500)
- ❌ Files taking >5s = network issues or server problems
- ⏱️ Pyodide WASM = expected to take 2-5s
- ⚠️ Many small requests = too many `fetch` entries

### Step 3: Monitor Console Timing

Add timing markers to see which step is slowest:

```javascript
// In your browser console, paste this:
console.time("PyScript Load");

// Then add this to your HTML script tag:
<script type="py">
    import time
    print(f"[TIMING] Python runtime initialized: {time.time()}")
</script>
```

### Step 4: Check Console for Errors

Watch the **Console** for messages:

```
✅ [SYSTEM]: Initializing game modules...
✅ [SYSTEM]: Game Logic Loaded successfully.
✅ [SYSTEM]: Welcome, Traveler.

❌ [ERROR]: Failed to load game: ModuleNotFoundError
❌ Uncaught PythonError: ...
```

**If you see errors:**
- Check that all `.py` files appear in Network tab with 200 status
- Verify `fetch` paths are correct (relative to index.html)
- Check console for ImportError messages

### Step 5: Performance Profiling in DevTools

1. Open **Performance** tab (in Chrome: `Shift+Cmd+P` → "Record")
2. Click Record
3. Reload page
4. Wait for "Welcome, Traveler" message
5. Stop recording
6. Analyze the timeline:

```
Timeline View:
──────────────────────────────────────────
[     HTML Parse      ]
[        Script Load (Pyodide)    ←  Red bar = bottleneck
[  Python Runtime      ]
[    Module Loading    ]
[ Your Game Code       ]
```

**Long bars = slow operations.** Click on them to see details.

### Step 6: Create a Debugging Checklist

Use this to diagnose issues:

```html
<script type="py">
    import sys
    import time
    from pyscript import display
    
    def debug_checkpoint(name):
        print(f"[DEBUG {time.time():.1f}s] {name}")
    
    debug_checkpoint("Python runtime ready")
    debug_checkpoint(f"sys.path: {sys.path}")
    debug_checkpoint(f"Available modules: {dir()}")
    
    try:
        from main import start_app
        debug_checkpoint("main.py imported successfully")
    except ImportError as e:
        debug_checkpoint(f"❌ Import failed: {e}")
        
    debug_checkpoint("Game startup")
</script>
```

### Step 7: Common Issues & Solutions

| Issue | Check | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'src.main'` | Network tab for .py files | Verify `fetch` paths; check file was downloaded |
| `ModuleNotFoundError: No module named 'noise'` | Console for pip install | Add `packages = ["noise"]` to `<py-config>` |
| 15+ second load time | Network tab | Check Pyodide WASM download time; use CDN closer to user |
| Files not found (404) | Network tab shows red | Check relative paths in `fetch`; verify files exist |
| `ImportError: dynamic module not allowed` | Console | Some packages require async loading; use dynamic imports |

### Step 8: Monitor Browser Storage

Check what's being cached:

1. DevTools → **Application** tab
2. Check **Cache Storage** and **Service Workers**
3. Pyodide caches to browser storage after first load
4. Subsequent visits should use cached Pyodide

```javascript
// Check cache from console:
caches.keys().then(names => console.log("Caches:", names));
```

---

## 5. Optimization Tips for Faster Load Times

### Quick Wins

1. **Reduce fetch entries** (merge related directories)
2. **Remove unused packages** from `packages = []`
3. **Lazy load modules** (import only when needed)
4. **Minify your Python** (remove comments, use shorter variable names)

### Code Example: Lazy Loading

```python
# ❌ SLOW - Imports everything at startup
from src.game_system import *
from src.battle_system import *
from src.map_system import *

# ✅ FAST - Imports only when needed
async def boot():
    # Only import when user clicks "Start Game"
    from src.main import start_app
    await start_app()
```

### Progressive Enhancement

```html
<div id="terminal">
    Loading Desgoblin-ASCII Engine...
    <progress id="loadProgress" max="100" value="0"></progress>
</div>

<script type="py">
    from pyscript import display
    
    def progress(msg):
        display(f"⏳ {msg}", target="terminal", append=True)
    
    progress("Initializing Python runtime...")
    # ... user sees feedback during long load
</script>
```

---

## 6. Testing Your Fix Locally

### Before Pushing to GitHub Pages

1. **Start a local web server:**
   ```bash
   cd /home/namurz/desgoblin-ascii
   python -m http.server 8000
   ```

2. **Open browser:**
   ```
   http://localhost:8000
   ```

3. **Check DevTools Console:**
   - Verify no 404 errors
   - Confirm "Welcome, Traveler" message appears
   - Check Network tab timing

4. **Monitor performance:**
   - Record Performance tab
   - Note startup time
   - Compare before/after your changes

### Verification Checklist

- [ ] No 404 errors in Network tab
- [ ] Console shows "Welcome, Traveler" message
- [ ] Game is playable (can see terminal output)
- [ ] No Python errors in console
- [ ] Load time is reasonable (< 15s first load)

---

## 7. Next Steps

1. **Commit your changes:**
   ```bash
   git add index.html docs/index.html web/index.html PYSCRIPT_DEPLOYMENT_GUIDE.md
   git commit -m "Fix PyScript module loading and add deployment guide"
   git push origin main
   ```

2. **GitHub Pages will deploy automatically** (check Actions tab)

3. **Monitor your live deployment:**
   - Open your GitHub Pages URL
   - Check Console for errors
   - Report any issues back to this guide

---

## 8. Additional Resources

- **PyScript Docs:** https://docs.pyscript.net/
- **Pyodide Packages:** https://pyodide.org/en/stable/packages.html
- **Python Module Import:** https://docs.python.org/3/tutorial/modules.html
- **Browser DevTools Guide:** https://developer.chrome.com/docs/devtools/

---

## Quick Reference: Configuration Checklist

```html
<py-config>
    ✅ packages = ["only_packages_that_exist_on_pyodide"]
    ✅ fetch = [
        {"from": "./src", "to_folder": "src", "files": ["*.py", "*.json"]},
        {"from": "./src/battle_system", "to_folder": "src/battle_system", "files": ["*.py"]},
        <!-- List EVERY subdirectory with files -->
    ]
</py-config>

<script type="py">
    ✅ import sys
    ✅ sys.path.insert(0, "/src")  <!-- Enable absolute imports -->
    ✅ from main import start_app   <!-- No "src." prefix -->
    ✅ Add error handling with try/except
</script>
```

---

**Summary:** Your module loading fix explicitly lists all directories and uses proper import paths. PyScript's slow load time is expected (5-17s first visit) due to downloading and initializing Python+WASM. Use the debugging guide to profile and optimize further if needed.
