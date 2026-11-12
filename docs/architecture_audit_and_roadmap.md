# Audit Architectural & Plan de Mise en Œuvre — UVM 1.2 Interactive Documentation

> **Date de l'audit** : 12 novembre 2026  
> **Périmètre analysé** : Shell SPA (`index.html`, `js/`), feuilles de styles (`css/`), générateurs et suites de tests (`scripts/`), pipeline CI/CD (`.github/workflows/deploy.yml`), et spécifications (`PRODUCT_SPEC_AND_METHODOLOGY.md`).

---

## 1. Métriques Actuelles du Projet

| Composant | Fichier | Volume | Lignes | Rôle actuel |
| :--- | :--- | ---: | ---: | :--- |
| **Index recherche** | `js/search_data.js` | 1,92 Mo | — | Arbre de navigation & index global (généré, ignoré par Git) |
| **Index symboles** | `js/uvm_symbol_quick.js` | 861 Ko | — | Dictionnaire symboles UVM & héritages (généré, ignoré par Git) |
| **Contrôleur iframes** | `js/page_common.js` | 175 Ko | 4 271 | Logique commune **et** spécifique de toutes les vues iframes |
| **Contrôleur SPA** | `js/app.js` | 159 Ko | 3 910 | Routeur, sidebar, recherche, RAG UI, modales, split-view |
| **Feuille de styles** | `css/style.css` | 155 Ko | 7 637 | Thèmes, layout SPA, docs, code studio, modales (176 `!important`) |
| **Moteur RAG** | `js/rag_engine.js` | 25,5 Ko | 729 | Inférence locale Transformers.js & similarité cosinus |
| **Build Docs** | `scripts/build_docs.py` | 107 Ko | 2 243 | Génération `docs_view/`, `src_view/`, `search_data.js` |
| **Build Examples** | `scripts/build_examples.py` | 81 Ko | 1 635 | Génération des 39 studios dans `examples_view/` |
| **Build AST DB** | `scripts/build_uvm_source_db.py` | 55 Ko | 1 375 | Extraction AST SystemVerilog / C DPI vers JSON / SQLite / JS |
| **Builder commun** | `scripts/page_builder_common.py` | 48 Ko | 1 022 | Helpers de rendu HTML partagés |
| **Highlighter SV/C** | `scripts/syntax_highlighter.py` | 36,6 Ko | 795 | Tokenisation SV/UVM/C/Makefile & symboles cliquables |
| **Quick Symbols** | `scripts/generate_quick_symbols.py` | 22,3 Ko | 555 | Génération `uvm_symbol_quick.js` et `js/doc_topics/*.js` (206 fichiers) |

---

## 2. Diagnostic Détaillé

### 2.1 Points forts existants
- **Autonomie totale (`file://` et GitHub Pages)** : aucune dépendance serveur ou bundler runtime requis pour consulter le site.
- **Protocole `postMessage` fonctionnel en local** : contournement propre des restrictions `file://` entre `index.html` et les iframes (`docs_view`, `src_view`, `examples_view`).
- **Coloration syntaxique unifiée** : `syntax_highlighter.py` garantit une taxonomie homogène sur tout le portail avec inférence statique de contexte (`data-sym-owner`, `data-sym-base`) et garde-fous contre les faux-positifs matériels.
- **Couverture de tests ciblée** : 8 scripts de vérification spécialisés existent dans `scripts/`.

### 2.2 Anomalies et points de fragilité identifiés

#### A. Pipeline CI/CD & Hygiène Git
1. **Vérification CI incomplète (`.github/workflows/deploy.yml` & `scripts/run_deploy_pipeline.py`)** :
   - Suite au retrait de `js/uvm_symbol_quick.js` et `js/doc_topics/` du suivi Git (`.gitignore`), ni `deploy.yml` (lignes 38-43) ni `run_deploy_pipeline.py` (lignes 51-55) ne contrôlent leur génération après `python scripts/build_docs.py`.
   - Aucun des 8 scripts de tests/vérification n'est exécuté en CI avant le déploiement GitHub Pages.
   - `deploy.yml` exécute `pip install fastembed` sans fichier `requirements-ci.txt` épinglé.
2. **Désynchronisation `docs_view/`** :
   - 174 fichiers dans `docs_view/` sont modifiés localement (migration des ancres `#doc-nav-item-X` vers `#uvm_barrier.new`, etc. suite à la mise à jour de `build_docs.py`) et doivent être commités pour refléter l'état du générateur.
3. **Références fantômes dans `PRODUCT_SPEC_AND_METHODOLOGY.md`** :
   - La check-list et le diagramme (§4 / §4.1) citent `verify_architecture.py` et `verify_image_features.py` alors que ces scripts n'existent pas dans `scripts/`.

#### B. Bugs et risques Runtime Frontend (`js/`)
1. **Race condition de navigation dans `js/app.js` (lignes 240-259)** :
   - `setFrameSrc()` enregistre un listener `load` et planifie 3 `setTimeout(sendScroll, 120/320/600)` sans identifiant de navigation ni annulation (`clearTimeout` / `removeEventListener`) si une nouvelle navigation démarre avant la fin de la précédente.
   - Deux listeners `load` distincts (`onFrameLoaded` et `onFrameThemeLoaded`) sont ajoutés sans déduplication.
2. **5 listeners `message` dispersés dans `js/page_common.js`** :
   - Présence de 5 `window.addEventListener('message', ...)` séparés (lignes 108, 1103, 1335, 2498, 2557) au lieu d'un routeur unique, et usage systématique de `postMessage(..., '*')` sans vérification de `e.source`.
3. **Incohérence linguistique dans `js/rag_engine.js` (lignes 35-60)** :
   - `DEFAULT_MODELS` contient des descriptions en français (`'MiniLM-L6 (Équilibré & Rapide)'`) alors que l'interface utilisateur est 100 % en anglais.
4. **Code mort (`js/main.js`)** :
   - Fichier placeholder de 5 lignes non référencé dans les pages HTML.

#### C. Goulots d'étranglement Architecturaux & Performance
1. **Monolithes JS (`page_common.js` 4 271 L, `app.js` 3 910 L)** :
   - `page_common.js` est chargé intégralement dans **toutes** les iframes alors que `initCodeStudio` (~1 090 L), `initFlowStepper` (~425 L) et `createNativeZipBlob` ne servent qu'à `examples_view/`, et `initInheritedMethodsExplorer` (~315 L) qu'à `docs_view/`.
   - `doc_page.js`, `src_page.js` et `example_page.js` existent déjà mais ne servent que de passe-plats vers `PageCommon.initAll()`.
   - Helpers dupliqués entre `app.js` et `page_common.js` (ex. `escapeHtml`).
2. **Chargement synchrone de `js/uvm_symbol_quick.js` (861 Ko)** :
   - Inclus en `<script>` bloquant dans chaque page de `docs_view/`, `src_view/` et `examples_view/`, ce qui force le navigateur à re-parser 861 Ko à chaque changement de page dans l'iframe.
3. **Dette CSS (`css/style.css` — 7 637 L, 176 `!important`)** :
   - Accumulation de règles de spécificité difficiles à maintenir sans effets de bord.
4. **Templates inline dans les scripts Python** :
   - `build_docs.py` (2 243 L) et `build_examples.py` (1 635 L) mélangent parsing, logique métier et gros blocs HTML/JS/SVG inline.

---

## 3. Plan de Mise en Œuvre par Étapes

### Phase 1 (P0) — Assainissement Git & Durcissement CI/CD
**Objectif** : Rendre le dépôt propre et fiabiliser immédiatement la pipeline GitHub Pages.

1. **Synchroniser les artefacts versionnés** :
   - Vérifier et committer `.gitignore`, les mises à jour documentaires (`README.md`, `PRODUCT_SPEC_AND_METHODOLOGY.md`, `LESSONS_LEARNED.md`), le retrait de `js/doc_topics/` et `js/uvm_symbol_quick.js` de l'index Git, ainsi que les 174 fichiers `docs_view/` régénérés.
2. **Mettre à jour `.github/workflows/deploy.yml` et `scripts/run_deploy_pipeline.py`** :
   - Ajouter le contrôle d'existence et de non-vacuité de `js/uvm_symbol_quick.js` et `js/doc_topics/*.js` après `build_docs.py`.
   - Créer `requirements-ci.txt` (ex. `fastembed`, `numpy`) et l'utiliser dans `deploy.yml`.
3. **Critère de validation** : `git status` propre après exécution locale de `python scripts/run_deploy_pipeline.py`.

---

### Phase 2 (P1) — Stabilisation Runtime JS & Nettoyage Rapide
**Objectif** : Éliminer les race conditions de navigation et les incohérences mineures sans changer l'architecture globale.

1. **Corriger `setFrameSrc()` dans `js/app.js`** :
   - Associer à chaque iframe un objet d'état `frame._pendingNav = { token, timeouts: [], onLoad }`.
   - À chaque appel à `setFrameSrc`, incrémenter le token, exécuter `clearTimeout` sur tous les timers en attente et `removeEventListener('load', ...)` sur le précédent handler.
   - Fusionner `onFrameLoaded` et `onFrameThemeLoaded` en un seul handler `load`.
   - Ajouter un message `scrollAck` émis par `page_common.js` une fois l'ancre trouvée et centrée, afin d'annuler les `setTimeout` restants côté `app.js`.
2. **Unifier le routage `postMessage` dans `js/page_common.js`** :
   - Regrouper les 5 listeners `window.addEventListener('message', ...)` en un dispatcher unique `handleCrossFrameMessage(e)` vérifiant `e.source === window.parent || e.source === window` et validant `e.data && typeof e.data === 'object'`.
3. **Nettoyages ciblés** :
   - Traduire `DEFAULT_MODELS` en anglais dans `js/rag_engine.js`.
   - Supprimer le fichier mort `js/main.js`.
4. **Critère de validation** : Navigation rapide entre résultats de recherche (ex. clics successifs sur `uvm_component`, `uvm_driver`, méthodes héritées) sans défilement parasite ni erreur console.

---

### Phase 3 (P1) — Optimisation du Chargement de `uvm_symbol_quick.js` (861 Ko)
**Objectif** : Supprimer le coût de parsing répété de 861 Ko à chaque navigation d'iframe tout en préservant le mode `file://` autonome.

1. **Partage via `window.parent` dans le shell SPA** :
   - Charger `js/uvm_symbol_quick.js` une seule fois dans `index.html` (avec `defer`), ou le conserver en cache sur `window.top.__UVM_SYMBOLS_CACHE`.
   - Dans `js/page_common.js`, résoudre `getUvmSymbols()` en priorité depuis `window.UVM_SYMBOLS || (window.parent && window.parent.UVM_SYMBOLS)` (avec fallback `try/catch` pour `file://` cross-origin strict).
2. **Chargement différé / `defer` dans les pages générées** :
   - Modifier `scripts/build_docs.py` et `scripts/build_examples.py` pour injecter `<script src="../../js/uvm_symbol_quick.js" defer></script>` uniquement si nécessaire, ou via injection dynamique à la demande au premier survol/clic d'un token `.clickable-uvm-sym` lorsque `window.parent.UVM_SYMBOLS` n'est pas accessible.
3. **Critère de validation** : Temps de chargement des iframes réduit, popover de désambiguïsation et liens symboles 100 % fonctionnels en mode SPA (`http://`) et autonome (`file://`).

---

### Phase 4 (P2) — Unification de la Suite de Tests & Alignement Spec
**Objectif** : Permettre l'exécution de toute la recette en une seule commande locale et en CI.

1. **Créer `scripts/run_tests.py`** :
   - Orchestrateur exécutant séquentiellement :
     1. `test_syntax_highlighter.py`
     2. `verify_code_containers.py`
     3. `verify_code_editor_tools.py`
     4. `verify_examples.py`
     5. `verify_inherited_members.py`
     6. `verify_search_pilot.py`
     7. `verify_source_notes.py`
     8. `verify_stepper_calibration.py`
   - Affiche un récapitulatif `[PASS/FAIL]` et retourne un code de sortie non nul en cas d'échec.
2. **Brancher `scripts/run_tests.py` dans `.github/workflows/deploy.yml`** (après `build_docs.py`).
3. **Mettre à jour `PRODUCT_SPEC_AND_METHODOLOGY.md`** :
   - Retirer les références fantômes `verify_architecture.py` et `verify_image_features.py` ou pointer vers `scripts/run_tests.py`.
4. **Critère de validation** : `python scripts/run_tests.py` retourne `0` localement et sur GitHub Actions.

---

### Phase 5 (P3) — Refactorisation Modulaire (JS, CSS & Templates Python)
**Objectif** : Améliorer la maintenabilité long terme sans casser la compatibilité `file://`.

1. **Découpage de `js/page_common.js` (4 271 L → modules spécialisés)** :
   - `js/core_frame.js` : thème, clipboard, `escapeHtml`, routeur `postMessage`, zoom diagrammes, lookup symboles & popover.
   - `js/doc_page.js` : `initTOC`, `expandAllRetractedAncestors`, `initInheritedMethodsExplorer`, `initDerivedClasses`, `initHeadingAnchors`.
   - `js/example_page.js` : `initCodeStudio`, `initSimulationConsole`, `initFlowStepper`, `createNativeZipBlob`.
   - `js/src_page.js` : ancrage de lignes `#Lxx` et bouton documentation.
   - Mettre à jour les `<script>` injectés par `build_docs.py` et `build_examples.py`.
2. **Découpage de `js/app.js` (3 910 L)** :
   - Séparer en `js/app_utils.js` (normalisation URLs, `escapeHtml`), `js/app_sidebar.js`, `js/app_search.js`, `js/app_modals.js`, `js/app.js` (orchestration & routeur).
3. **Restructuration de `css/style.css` (7 637 L, 176 `!important`)** :
   - Introduire `@layer base, layout, components, studio, states;` pour résorber les conflits de spécificité et supprimer progressivement les `!important`.
   - Découper en fichiers thématiques sous `css/` (importés ou concaténés au build).
4. **Extraction des templates Python** :
   - Déplacer les gros gabarits HTML/SVG de `build_docs.py` et `build_examples.py` vers `scripts/templates/` via `string.Template`.
5. **Critère de validation** : Aucune régression fonctionnelle sur `python scripts/run_tests.py` ni sur la recette visuelle multi-navigateurs (Light/Dark, Docs/Source/Split, Search/RAG, Examples Studio).

---

## 4. Garde-fous & Risques à Surveiller

| Risque | Mitigation |
| :--- | :--- |
| **Rupture du mode `file://` (CORS / ES Modules)** | Ne pas utiliser `<script type="module">` (bloqué par CORS sur `file://`). Conserver des IIFE classiques attachées à `window.*`. |
| **Désynchronisation entre `docs_view` / `examples_view` et les scripts JS** | Toute modification de nom ou de découpage de scripts JS doit être répercutée dans `build_docs.py`, `build_examples.py` et re-générée immédiatement. |
| **Régressions sur la navigation d'ancres / zones rétractées** | Tester systématiquement les liens vers des méthodes héritées (`uvm_driver` → `build_phase`), des macros (`` `uvm_info ``) et des lignes de tableaux avant de valider chaque phase. |

