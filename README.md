# UVM 1.2 Interactive Documentation & Source Explorer

A modern, dynamic web documentation platform and SystemVerilog source code explorer for **Universal Verification Methodology (UVM 1.2)**.

Ready for local offline browsing and automated continuous deployment to **GitHub Pages**.

---

## 🚀 Key Features

- **Dynamic Interactive Web Portal**: Fast, responsive layout with single-page navigation and deep-linking.
- **SystemVerilog Web Source Viewer**: Complete syntax highlighting, clickable line numbers (`#Lxx`), copy buttons, and raw downloads for all 155 source files (`.sv`, `.svh`, `.c`, `.h`).
- **Bidirectional Deep Linking**:
  - Class and macro reference pages include prominent **"View Source"** buttons jumping directly to their definition lines in the source code.
  - Source files include a **"Documentation"** button returning directly to the reference manual.
- **Split-Screen Mode**: View API documentation and SystemVerilog implementation side-by-side with an interactive resizable divider.
- **Instant Symbol & Full-Text Search**: Live search modal across 880+ classes, methods, macros, and source files with keyboard navigation (`/` or `Ctrl+K`).
- **Dark & Light Mode**: Seamless theme switching with local storage persistence and real-time iframe synchronization.
- **100% English Documentation**: All menus, titles, descriptions, and user interface elements in English.
- **Zero-Dependency Static Build**: Generated with Python standard library; fully functional offline without external servers.

---

## 📁 Repository Structure

```text
UVM_doc/
├── .github/
│   └── workflows/
│       └── deploy.yml        # GitHub Actions continuous deployment workflow
├── css/
│   └── style.css             # Unified stylesheet (theme variables, syntax colors, layout)
├── js/
│   ├── app.js                # Core SPA application (router, search, theme, split view)
│   └── search_data.js        # Generated index of categories, source tree, and symbols
├── scripts/
│   └── build_docs.py         # Python build script generating docs_view and src_view
├── docs_view/                # Modernized, responsive UVM 1.2 reference HTML pages
├── src_view/                 # Syntax-highlighted HTML views of all 155 source files
├── uvm-1.2/                  # Official Accellera UVM 1.2 distribution
│   ├── src/                  # Raw SystemVerilog and C source tree
│   └── docs/                 # Original reference documentation assets
├── index.html                # Main application portal shell
├── LICENSE                   # Apache 2.0 open-source license
├── NOTICE                    # Legal attributions and third-party notices
└── README.md                 # Project documentation
```

---

## 💻 Local Preview

You can preview the site immediately using any local web server:

```bash
# Start a local HTTP server
python -m http.server 8000
```

Then open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 🛠️ Rebuilding the Documentation

If you modify or update any files in `uvm-1.2/src` or `uvm-1.2/docs`, you can regenerate the entire documentation site with a single command:

```bash
python scripts/build_docs.py
```

The build script will:
1. Parse all 155 source files in `uvm-1.2/src/`.
2. Generate syntax-highlighted HTML files in `src_view/` with clickable line anchors.
3. Map every class, method, and macro to its definition line number.
4. Modernize all 146 documentation files in `docs_view/` and inject **"View Source"** deep links.
5. Generate `js/search_data.js` containing category trees, source directory trees, and search indices.

---

## 🌐 GitHub Pages Deployment

This repository is pre-configured with a GitHub Actions workflow (`.github/workflows/deploy.yml`).

1. Push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Generate dynamic UVM 1.2 documentation"
   git push origin main
   ```
2. Enable GitHub Pages:
   - Navigate to **Settings** > **Pages** in your GitHub repository.
   - Under **Build and deployment** > **Source**, select **GitHub Actions**.
3. Every push to `main` automatically deploys the updated portal.

---

## 📄 License & Attribution

This project is licensed under the **[Apache License 2.0](LICENSE)**.

### UVM Standard Attribution
- **Universal Verification Methodology (UVM) 1.2** is an open-source standard developed and maintained by the **[Accellera Systems Initiative](https://www.accellera.org/)** under the Apache 2.0 License.
- In compliance with Section 4(d) of the Apache 2.0 License, all original contributor notices (Mentor Graphics Corporation, Cadence Design Systems, Inc., Synopsys, Inc., Cypress Semiconductor Corp., NVIDIA Corporation) are preserved in the **[NOTICE](NOTICE)** file.
