# UVM 1.2 Interactive Documentation & Source Explorer

A modern, dynamic web documentation platform and SystemVerilog source code explorer for **Universal Verification Methodology (UVM 1.2)**.

Ready for local offline browsing and automated continuous deployment to **GitHub Pages**.

---

## 🚀 Key Features

- **Dynamic Interactive Web Portal**: Fast, responsive layout with single-page navigation and deep-linking.
- **Google Developers Inspired Design**: High-contrast, crystal-clear typography (Google Sans & Roboto) with a refined Google Blue color scheme matching official documentation such as Google Apps Script and Google Cloud reference docs.
- **Full Syntax Highlighting in Documentation**: Syntax-highlighted code blocks, command-line snippets, and API prototypes with language badges and 1-click clipboard copy buttons.
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
├── config/
│   ├── rag_intent_catalog.json # Curated UVM verification intent & synonym catalog
│   ├── rag_models.json       # Catalog of AI embedding models (ratings, sizes, paths)
│   └── rag_prompts.json      # 15 starter natural language queries
├── css/
│   └── style.css             # Unified stylesheet (theme variables, syntax colors, layout)
├── js/
│   ├── app.js                # Core SPA application (router, search, theme, split view)
│   ├── rag_engine.js         # Client-side RAG & vector similarity search engine
│   └── search_data.js        # Generated index (untracked, built at deployment & locally)
├── scripts/
│   ├── build_docs.py         # Python build script generating docs_view and src_view
│   └── build_rag_embeddings.py # Generates intelligent chunks & dense vector embeddings
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
# Full rebuild: parses sources, regenerates HTML views, modernizes docs, and builds search index
python scripts/build_docs.py

# Fast search-only build (< 1s): regenerates js/search_data.js from existing views
python scripts/build_docs.py --search-only

# Generate RAG intelligent chunks and vector embeddings (data/rag_embeddings.bin)
python scripts/build_rag_embeddings.py
```

The build scripts will:
1. Parse all 155 source files in `uvm-1.2/src/`.
2. Generate syntax-highlighted HTML files in `src_view/` with clickable line anchors.
3. Map every class, method, and macro to its definition line number.
4. Modernize all 146 documentation files in `docs_view/` and inject **"View Source"** deep links.
5. Generate `js/search_data.js` containing category trees, source directory trees, and search indices.
6. Generate `data/rag_chunks.json` and `data/rag_embeddings.bin` for client-side semantic vector search.

> **Note on version control:** `js/search_data.js` (~1.5 MB) and `data/` (~5.8 MB) are excluded from Git tracking (`.gitignore`) to avoid repository bloat and diff churn. The GitHub Actions deployment workflow automatically builds these files upon deployment.

---

## ✨ Natural Language Semantic Search (Client-Side RAG)

In addition to instant symbol and regex search, the portal includes an in-browser semantic retrieval engine:
- **Toggle mode**: Press `Alt+N` or click the `✨` button in the search modal (`Ctrl+K` or `/`).
- **Privacy & zero-server**: Query embeddings are computed locally in your browser using Transformers.js (`all-MiniLM-L6-v2` or configurable models in `config/rag_models.json`). No queries or data are sent to any external server.
- **Smart Snippets**: Automatically extracts the most relevant 1-2 sentences with key concept highlights.
- **Configurable Models & Prompts**: Add or modify models in `config/rag_models.json` and question suggestions in `config/rag_prompts.json`.
- **Memory & Cache Hygiene**: The AI model is cached permanently on disk (CacheStorage) but automatically unloaded from browser RAM after 3 minutes of inactivity or when the modal closes.

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

## 📚 Product Specification & Engineering Guidelines

For comprehensive technical specifications, user guides, reverse-engineered architecture, protocol catalogs, development rules, and post-mortem lessons learned:

- **[RAG Technical Specification & Architecture](RAG_SPECIFICATION.md)**: Comprehensive specification of the client-side 2-level hierarchical RAG, intent catalog embedding enrichment, vector cosine similarity pipeline, and hybrid ranking.
- **[RAG User Guide (Recherche en Langage Naturel)](RAG_USER_GUIDE.md)**: End-user handbook on using the AI natural language search, query examples by verification domain, interpreting deep-link results, and settings customization.
- **[Product Specification & Engineering Methodology](PRODUCT_SPEC_AND_METHODOLOGY.md)**: Reverse-engineered specification, `postMessage` protocol catalog, 5 golden development rules, and 3-level verification strategy.
- **[Lessons Learned & Technical Traps Guide](LESSONS_LEARNED.md)**: Real-world post-mortem analysis of CSS pointer-events modal bugs, smooth scrolling race conditions, legacy HTML ID mapping, search engine regex error handling, and cross-frame event capture.

---

## 📄 License & Attribution

This project is licensed under the **[Apache License 2.0](LICENSE)**.

### UVM Standard Attribution
- **Universal Verification Methodology (UVM) 1.2** is an open-source standard developed and maintained by the **[Accellera Systems Initiative](https://www.accellera.org/)** under the Apache 2.0 License.
- In compliance with Section 4(d) of the Apache 2.0 License, all original contributor notices (Mentor Graphics Corporation, Cadence Design Systems, Inc., Synopsys, Inc., Cypress Semiconductor Corp., NVIDIA Corporation) are preserved in the **[NOTICE](NOTICE)** file.
