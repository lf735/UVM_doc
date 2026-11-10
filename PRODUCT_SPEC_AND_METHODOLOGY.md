# Spécification Produit à Posteriori & Méthodologie d'Ingénierie
## UVM 1.2 Interactive Documentation & Source Explorer

---

## 1. Spécification Produit à Posteriori (Reverse-Engineered Spec)

### 1.1 Vision & Objectifs
Le projet **UVM 1.2 Interactive Documentation & Source Explorer** vise à transformer le manuel de référence UVM 1.2 historique (généré à l'origine par *Natural Docs* en 2014 sous forme de pages HTML statiques non responsives et cloisonnées) en une **plateforme web moderne, fluide, réactive et unifiée**, tout en préservant une indépendance totale vis-à-vis d'un backend serveur (fonctionnement 100% autonome en mode local `file://` et déploiement statique automatisé sur GitHub Pages).

### 1.2 Acteurs & Utilisateurs Cibles
- **Ingénieurs de Vérification ASIC / FPGA** : consultation rapide des APIs UVM, vérification des prototypes de méthodes (`function` vs `task`), exploration des macros et hiérarchies de classes.
- **Développeurs SystemVerilog** : inspection directe du code source d'implémentation de la bibliothèque UVM 1.2 avec liens bidirectionnels documentation ↔ code source.
- **Étudiants et Formateurs** : support pédagogique moderne avec diagrammes contrastés, architecture visuelle claire et recherche instantanée.

---

### 1.3 Matrice des Fonctionnalités du Produit

| Domaine | Fonctionnalité | Description Détaillée |
| :--- | :--- | :--- |
| **Shell & Layout** | **Architecture SPA** | Portail unique ([index.html](file:///c:/Dev/UVM_doc/index.html)) hébergeant la barre d'outils, la sous-barre globale et un viewport double iframe. |
| | **Sous-Barre de Navigation Pleine Largeur** | Bandeau horizontal supérieur à 100% de la largeur (`.app-subbar`) hébergeant les 5 sections majeures (**Documentation**, **Source Tree**, **Examples**, **Hierarchy**, **Index A-Z**) avec icônes SVG et sélection active. |
| | **Modes de Vue (View Switcher)** | **Docs** (documentation seule), **Source** (code SystemVerilog seul) et **Split** (vue côte à côte). |
| | **Split-View Redimensionnable** | Séparateur draggable (`#split-divider`) avec redimensionnement interactif et double-clic pour restaurer le ratio 50/50. |
| | **Routage par Hash** | URLs avec état profond : `#/doc/<path>#<id>`, `#/src/<path>#L<line>`, `#/example/<path>`, `#/split?doc=<path>&src=<path>`. |
| | **Thème Clair / Sombre** | Palette Google Developers (Light / Dark) avec bascule instantanée et propagation `postMessage` synchrone dans les iframes. |
| **Navigation Latérale** | **Arborescence Hiérarchique Structurée** | Affichage en arbre avec guide visuel vertical (`border-left: 1px solid var(--border-subtle)`) et alignement harmonisé sans décalage arbitraire. |
| | **Explorateur d'Arborescence Hiérarchique (Onglet Hierarchy)** | Navigation complète dans l'arbre d'héritage UVM (328 classes avec racine `uvm_void`), indicateurs visuels de rôle (Components, Objects, Sequences, TLM, Registers, Phases), badges de métriques (méthodes propres, sous-classes directes), filtres thématiques rapides, recherche temps réel avec auto-expansion, boutons Expand/Collapse All et bouton d'accès direct au code source. |
| | **Index Alphabétique Exhaustif (Onglet Index A-Z)** | Exploration intégrale de 3 688 symboles UVM (classes, fonctions, tâches, macros, constantes, variables, types, ports, exemples). Badges sémantiques colorés, affichage du propriétaire de classe (`az-symbol-owner`), sélection persistante et visible (`.az-index-link.active`), filtres thématiques par pilules adaptés à l'onglet. |
| | **Filtres Contextuels par Pilules (Tous Onglets)** | Adaptation dynamique des pilules de filtrage selon l'onglet actif :<br/>- *Docs* : `All`, `Classes`, `Macros`, `Overviews`, `Components`, `Sequences`, `TLM`, `Registers`, `Phases`<br/>- *Source Tree* : `All`, `.svh`, `.sv`, `.c / .h`, `Base`, `Components`, `Sequences`, `TLM`, `Registers`<br/>- *Examples* : `All`, `Beginner`, `Intermediate`, `Advanced`<br/>- *Hierarchy* : `All`, `Components`, `Objects`, `Sequences`, `TLM`, `Registers`, `Phases`<br/>- *Index A-Z* : `All`, `Classes`, `Functions`, `Tasks`, `Macros`, `Variables`, `Constants`, `Types`, `Ports`. |
| | **Titres de Groupes avec Aperçu Clignotant** | Titres de sections cliquables (`overviewHref`) ouvrant la page de synthèse de la section, doublés d'un bouton chevron dédié au dépliement/repliement. |
| | **Bouton Expand / Collapse All** | Bouton `#sidebar-toggle-all` permettant de déplier ou replier d'un clic tous les dossiers ou catégories visibles. |
| | **Filtre Temps Réel de Barre** | Filtrage instantané avec champ dédié, effacement rapide (`×`), mode Regex (`.*`) et pilules multi-filtres enveloppantes (`flex-wrap`). |
| **Moteur de Recherche** | **Recherche Modale Globale** | Déclenchement via `/` ou `Ctrl+K` / `Cmd+K` couvrant 3 688 symboles, fichiers et exemples interactifs. |
| | **Persistance Non-Destructive** | Préservation complète de la session de recherche (`activeSearchSession` : requête, filtres, liste de résultats et position active), sélection du texte à l'ouverture (`searchInput.select()`). |
| | **Barre Flottante (« Search Pilot »)** | Barre dockée fixe (`#search-nav-bar`) affichant la requête, le compteur `N of Total`, boutons `◀ Précédent` (`Alt+[`), `▶ Suivant` (`Alt+]`), bouton de réouverture `All Results` et bouton de fermeture `✕`. |
| | **Traçage des Résultats Consultés**| Marquage visuel des symboles déjà examinés avec coche verte (`.viewed`) et surlignage de l'élément actif (`.current-result`). |
| | **Historique des Recherches Récentes**| Mémorisation locale des 8 dernières recherches dans `localStorage` présentées sous forme de puces interactives dès que le champ est vide en mode standard. |
| | **Distinction Function / Task** | Typage strict identifiant clairement les `functions` (non-temporelles) et les `tasks` (consommatrices de temps de simulation). |
| | **Affichage de la Classe Parente** | Présentation explicite `Classe :: Méthode` dans les résultats pour lever toute ambiguïté (ex. `uvm_driver :: run_phase`). |
| | **Recherche Multi-Mots Intelligente** | Scoring pondéré associant des termes répartis entre le nom du symbole, sa classe et sa description. |
| | **Support Regex Avancé** | Recherche par expressions régulières (`Alt+R`) avec contour d'avertissement ambre/rouge non bloquant en cas de syntaxe incomplète. |
| | **Respect de la Casse** | Bascule `Aa` (`Alt+C`) pour différencier les identifiants sensibles à la casse. |
| | **Filtres Multi-Sélection Multi-Lignes**| Pilules (`All`, `Classes`, `Functions`, `Tasks`, `Macros`, `Files`, `Examples`, `Beginner`, `Intermediate`, `Advanced`) réparties sur plusieurs lignes (`flex-wrap`). |
| | **Bouton Effacer (`Clear / ×`)** | Nettoyage instantané du champ au clic ou via une première pression sur la touche `Escape`. |
| **Documentation (`docs_view`)** | **Fil d'Ariane Cliquable Hiérarchique** | Navigation ascendant complète reliant la page courante à ses sections parentes avec aperçu direct, sans insertion du dossier technique `Overviews`. |
| | **Bannière "View Source" Discrète** | En-tête injecté avec bouton compact iconique (`.banner-icon-btn`) et badge de ligne, discret et sans bouton verbeux encombrant. |
| | **Nettoyage des En-têtes Légaux** | Élimination totale des mentions parasites de copyright dans les descriptions de classes et méthodes orphelines. |
| | **Topologie & Hiérarchie de Classes In-Situ (`class-hierarchy-widget`)** | Remplacement in-situ au même endroit de l'ancien bloc statique Natural Docs (`<div class=ClassHierarchy>`) dans le tableau Summary. Chaîne ascendante navigable (`uvm_void` ➔ ... ➔ classe courante), sous-classes directes repliables (`.hierarchy-subclasses-card`), tags de rôle architectural et badges de métriques sans duplication sur les en-têtes de sections multi-classes. |
| | **Matrice Interactive des Méthodes Héritées** | Accordéon interactif situé sous le sommaire de chaque classe, regroupant l'ensemble des méthodes héritées par classe ancêtre avec pastilles cliquables menant directement à la documentation ou à l'implémentation de la classe d'origine. |
| | **Routage Précis des Liens Dérivés** | Redirection vers l'ancre exacte de la classe au sein de la page cible (`#doc-nav-item-X`) au lieu du haut de page générique. |
| | **Bouton Copie d'Ancre au Survol** | Icône de chaîne de lien apparaissant au survol de chaque titre (`.doc-anchor-link-btn`) copiant le lien direct avec feedback "Link copied!". |
| | **Protection Anti-Récursion Iframe** | Liens de fil d'Ariane (`doc-breadcrumbs`) configurés avec `target="_top"` et interceptés en JS pour éviter toute duplication en abyme du portail dans une sous-iframe. |
| | **Documentation des Classes Orphelines** | Génération de pages documentaires pour les 15 classes UVM réelles non documentées dans l'historique NaturalDocs (ex. `uvm_spell_chkr`, `uvm_resource_specializations`). |
| | **Index NaturalDocs Modernisés** | 26 pages d'index A-Z héritées modernisées dans `docs_view/index/` et pleinement reliées aux onglets de navigation. |
| | **Différenciation Contents / Summary**| Séparation nette entre la table de contenu de fichier (`Contents`) et les résumés de méthodes de classe (`Summary`), sans collision d'identifiants DOM. |
| | **Normalisation des Entités HTML** | Décodage systématique des entités (`&amp;`, `&rsquo;`) garantissant un rendu propre sans double échappement dans les menus. |
| | **Sommaire Interne ("On this page")** | Barre latérale droite dynamique avec défilement espion (Scrollspy) et repli par groupes. |
| | **Défilement Précis des Liens & Tableaux** | Compensation de la marge supérieure (`scroll-margin-top`), suppression des conflits `scrollIntoView`, micro-ajustement géométrique. Ciblage chirurgical des lignes de tableau (`<tr>`) pour les constantes et énumérations avec halo `.doc-target-highlight`. |
| | **Résolution Multi-Variantes d'Ancres (Macros & Templates)** | Prise en charge des identifiants DOM canoniques (`doc-nav-item-X`), décodage automatique des backticks (`` ` ``) et encodages URL (`%60`), tolérance aux templates SystemVerilog (`#(BEFORE,AFTER)`). |
| | **Découplage d'Appariement Split-View (`autoPair`)** | Préservation absolue des ancres de documentation lors des navigations combinées (doc + source) évitant l'écrasement intempestif du panneau de documentation par l'appariement automatique. |
| | **Syntax Highlighting Sémantique** | Coloration SystemVerilog/UVM haute fidélité (appels système `$`, déclarations structurelles, types primitifs, qualificateurs OOP, méthodes/phases, constantes, macros et directives) sur les blocs `<pre>`, prototypes de méthodes et tables de signatures avec bouton de copie en un clic. |
| **Exemples Interactifs (`examples_view`)** | **Studio Multi-Fichiers en 2 Barres** | Barre d'outils supérieure (`.studio-toolbar` : saut direct de fichier, copie de code, téléchargement de fichier brut, copie de lien) + Barre d'onglets de fichiers pleine largeur inférieure avec défilement horizontal fluide et surlignage syntaxique multi-langages (SV, C/DPI, Makefiles). |
| | **Console d'Exécution Multi-Simulateurs** | Sorties réelles d'exécution pour Questa, VCS et Xcelium avec onglets interactifs et bannière de résumé UVM (0 errors / 0 fatals). |
| | **Archive ZIP Client-Side 1-Clic** | Téléchargement instantané de l'intégralité des fichiers de chaque exemple sans dépendance serveur via encodage binaire natif. |
| | **Visual Flow Stepper** | Progression pas-à-pas interactive avec frise chronologique sur les 5 piliers clés UVM. |
| **Diagrammes & Médias** | **Suppression des Sauts au Survol** | Neutralisation stricte de l'effet `transform: translateY(-2px)` sur toutes les images. |
| | **Cadrage Haute Lisibilité** | Encapsulation dans `<figure class="doc-diagram-card">` avec canevas `#ffffff` garantissant le contraste en mode sombre. |
| | **Visionneuse Zoom Plein Écran** | Modale Lightbox (`#image-zoom-modal`) avec zoom molette, déplacement drag & drop, boutons (+, -, 1:1, Fit) et raccourcis clavier. |
| | **Sécurité Non-Bloquante** | Masquage complet (`display: none; visibility: hidden; pointer-events: none;`) prévenant tout blocage d'interface à la fermeture. |
| **Explorateur Source (`src_view`)** | **Visualiseur Haute Fidélité (SV/C)** | 155 fichiers sources SystemVerilog et C/DPI avec tokenisation fine (fonctions système, méthodes, types, qualificateurs, opérateurs composés), numéros de lignes cliquables (`#L44`) et navigation bidirectionnelle avec la doc. |

---

### 1.4 Architecture Globale du Système

```
                              ┌────────────────────────────────────────────────────────┐
                              │                 Navigateur Web / Client                │
                              │       index.html (SPA Shell / Controller Principal)     │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
                             ┌────────────────────────────┴──────────────────────────┐
                             ▼                                                       ▼
               ┌───────────────────────────┐                           ┌───────────────────────────┐
               │    Iframe Documentation   │                           │     Iframe Code Source    │
               │   docs_view/**/*.html     │                           │     src_view/**/*.html    │
               └─────────────┬─────────────┘                           └─────────────┬─────────────┘
                             │                                                       │
                             │  ◄──────────── window.postMessage() ──────────────►  │
                             │   - openSourceView(url#Lxx)     - openDocView(url#id) │
                             │   - docNavigated(url)           - srcNavigated(url)   │
                             │   - openImageModal(src, title)  - theme(theme)        │
                             └───────────────────────────────────────────────────────┘
                                                          ▲
                                                          │ Généré par
                                                          │
                                     ┌────────────────────┴────────────────────┐
                                     │         Pipeline Python Statique         │
                                     │  - scripts/build_docs.py                │
                                     │  - scripts/build_examples.py            │
                                     │  - scripts/syntax_highlighter.py (Core) │
                                     └────────────────────▲────────────────────┘
                                                          │ Lit & Transforme
                                                          │
                               ┌──────────────────────────┴──────────────────────────┐
                               │                 Assets UVM 1.2 Sources              │
                               │ - uvm-1.2/src/ (155 fichiers SystemVerilog / C)     │
                               │ - uvm-1.2/docs/html/files/ (146 HTML Natural Docs)  │
                               └─────────────────────────────────────────────────────┘
```

---

## 2. Protocole de Communication Inter-Cadres (postMessage)

Toutes les interactions entre le conteneur principal (`index.html` / `js/app.js`) et les sous-pages intégrées dans les iframes reposent sur un protocole d'événements typés, garantissant la compatibilité aussi bien sous protocole `http://` / `https://` qu'en local sous `file://`.

### 2.1 Catalogue des Messages

| Émetteur | Destinataire | `type` de Message | Paramètres | Rôle |
| :--- | :--- | :--- | :--- | :--- |
| `docs_view` | Parent | `openSourceView` | `{ url: string }` | Demande au parent d'ouvrir un fichier source à une ligne donnée (bascule automatique en Split-View si en mode Doc). |
| `src_view` | Parent | `openDocView` | `{ url: string }` | Demande au parent d'ouvrir la documentation associée au fichier source en cours de consultation. |
| `docs_view` | Parent | `docNavigated` | `{ url: string }` | Notifie le parent qu'une nouvelle page de documentation a été chargée afin d'actualiser le titre, la sidebar et le hash URL. |
| `src_view` | Parent | `srcNavigated` | `{ url: string }` | Notifie le parent qu'un fichier source a été chargé pour actualiser le titre, la sidebar et le hash URL. |
| `docs_view` | Parent | `docSectionChanged` | `{ anchor: string, id: string, title: string }` | Informe le parent de la section active via le scrollspy pour synchroniser la navigation gauche. |
| `docs_view` | Parent | `openImageModal` | `{ src: string, title: string }` | Demande l'ouverture de la visionneuse de zoom plein écran pour un diagramme technique. |
| `docs_view` | Parent | `closeImageModal` | `{}` | Transmet la touche `Escape` pressée dans l'iframe pour fermer la visionneuse de zoom ouverte dans le parent. |
| Parent | `docs_view` | `scrollToSection` | `{ anchor: string, id: string }` | Ordonne au document de scroller directement et précisément jusqu'à un identifiant de section spécifique. |
| Parent | Tous iframes | Message objet | `{ theme: 'light' \| 'dark' }` | Diffuse le changement de thème vers les iframes pour mettre à jour `data-theme` sur `<html>`. |

---

## 3. Méthodologie de Développement pour les Prochaines Implémentations

Pour toute nouvelle fonctionnalité ou extension future (ex : ajout de nouvelles versions UVM, nouveau langage, export PDF, etc.), l'équipe doit suivre scrupuleusement les 5 principes directeurs suivants :

### Règle 1 : Zéro Dépendance Runtime Externe
- **Principe** : L'application finale doit pouvoir être ouverte directement en double-cliquant sur `index.html` sur une machine isolée sans accès Internet.
- **Interdiction** : Pas de CDN obligatoire au runtime, pas de bundler runtime lourd (Webpack/Vite requis pour lire le site), pas d'appels API AJAX bloquants vers un serveur distant.
- **Conséquence** : Toutes les données d'indexation sont compilées statiquement dans [`js/search_data.js`](file:///c:/Dev/UVM_doc/js/search_data.js) sous forme d'un objet global `window.UVM_DATA`. Ce fichier volumineux (~1,5 Mo) est exclu du versionnement Git (`.gitignore`) pour éviter le bloat de l'historique et est régénéré automatiquement lors du déploiement GitHub Pages ou localement via `python scripts/build_docs.py --search-only`.

### Règle 2 : Génération en Deux Passes pour les Liens Entrecroisés
- Lors de l'analyse et de la transformation de documents structurés :
  - **Passe 1 (Indexation globale)** : Scanner tous les fichiers, construire les tables de symboles, extraire les ancres et cartographier les correspondances `fichier + ancre -> identifiant normalisé`.
  - **Passe 2 (Transformation et réécriture)** : Appliquer les modifications HTML en utilisant le catalogue complet obtenu en passe 1 pour réécrire exhaustivement les liens internes et inter-fichiers.

### Règle 3 : Modèle Mental de Non-Collision d'Événements (Event Hygiene)
- Tout composant de type overlay/modal fixe (`position: fixed`) doit impérativement respecter la règle du triple verrouillage lorsqu'il est inactif :
  ```css
  .mon-overlay-ferme {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    opacity: 0;
  }
  ```
- Ne jamais compter uniquement sur `opacity: 0` ou `pointer-events: none` sur un conteneur si ses enfants peuvent avoir `pointer-events: auto`.

### Règle 4 : Gestion du Défilement Isolé (Scroll Isolation)
- Ne jamais appeler `element.scrollIntoView()` sur un sous-élément d'une barre latérale ou d'un menu si la fenêtre principale est en cours de défilement fluide.
- Toujours utiliser `container.scrollTo({ top: ..., behavior: 'smooth' })` ciblant explicitement le conteneur concerné.

### Règle 5 : Échappement et Modularité des Scripts Python
- Dans le script de build Python, séparer strictement :
  1. L'analyse syntaxique (Regex compilées, lexers SV).
  2. Les templates de code (attention aux f-strings contenant du JavaScript : doubler toutes les accolades `{{` et `}}`).
  3. L'écriture des fichiers finaux en encodage `UTF-8` strict avec gestion propre des fichiers sources hérités en `latin-1`.

### Règle 6 : Architecture RAG Client-Side et Respect de la Confidentialité
- **Principe** : La recherche en langage naturel ne doit jamais reposer sur une API externe payante ou distante qui collecterait les questions techniques de l'utilisateur.
- **Exécution locale** : L'embedding de la requête est généré directement sur le matériel de l'utilisateur (WASM/WebGPU via Transformers.js).
- **Précalcul CI/CD** : La base vectorielle de la documentation est calculée une fois pour toutes lors du déploiement GitHub Pages via `scripts/build_rag_embeddings.py` et stockée au format binaire compact `data/rag_embeddings.bin`.
- **Hygiène Mémoire** : Aucun modèle n'est téléchargé au chargement initial du site (0 Ko supplémentaire). L'instance en mémoire vive (RAM) est libérée dès la fermeture de la recherche.

### Règle 7 : Hygiène des Liens Iframe et Découplage de Contexte
- **Principe** : Une sous-page chargée dans une iframe (`docs_view`) ne doit jamais tenter de réinjecter le portail parent en son sein.
- **Règle** : Les liens menant à l'accueil ou au portail racine doivent porter `target="_top"`. Tout lien interne menant au code source ou à une autre page doit être intercepté via `postMessage` pour piloter la SPA parente de manière cohérente.

### Règle 8 : Normalisation Systématique des Entités HTML au Build
- **Principe** : Tout texte extrait de fichiers HTML historiques (NaturalDocs, XML) doit être converti en texte brut via `html.unescape()` avant stockage dans les index JavaScript / JSON.
- **Règle** : Ne jamais stocker de chaînes contenant des entités brutes (`&amp;`, `&rsquo;`) dans les structures de données, afin d'éviter les doubles échappements lors de l'application des filtres ou de la coloration syntaxique frontend.

### Règle 9 : Coloration Syntaxique Sémantique et Source Unique de Vérité
- **Principe** : La coloration syntaxique de l'ensemble du projet (documentation, visualiseur source et code studio des exemples) doit être pilotée par un moteur unifié (`scripts/syntax_highlighter.py`) garantissant une taxonomie sémantique riche et cohérente.
- **Règles d'implémentation** :
  1. **Taxonomie fine** : Dissocier impérativement les mots-clés de contrôle (`.sv-keyword`), les déclarations de structure (`.sv-keyword-decl`), les types primitifs (`.sv-type`), les qualificateurs OOP (`.sv-qualifier`), les classes UVM (`.sv-uvm-type`) et les constantes (`.sv-constant`).
  2. **Appels système prioritaires** : Capturer les symboles débutant par `$` (`$display`, `$cast`, `$time`, `$sformatf`) comme fonctions système (`.sv-system-tf`) avant toute tokenisation d'opérateurs.
  3. **Opérateurs composés atomiques** : Traiter les opérateurs multi-caractères (`::`, `->`, `<=`, `==`, `!=`, `&&`, etc.) en un seul élément HTML sans découpage caractère par caractère.
  4. **Multi-Langages** : Prise en charge native de SystemVerilog (IEEE 1800), C / C++ DPI (`.c`, `.cc`, `.h`) et Makefiles (`Makefile.*`).
  5. **Contraste binaire Dual-Theme** : Synchroniser rigoureusement les variables `--sv-*` en mode clair et mode sombre en respectant les critères d'accessibilité WCAG AA.

### Règle 10 : Persistance Non-Destructive de Session de Recherche et Navigation Flottante (« Search Pilot »)
- **Principe** : La recherche technique ne doit jamais pénaliser l'exploration séquentielle des résultats. La sélection d'un résultat ne doit pas anéantir le contexte de recherche.
- **Règles d'implémentation** :
  1. **Conservation d'état** : L'état `activeSearchSession` mémorise la requête, le mode (standard/IA), les résultats filtrés et l'index actif. La réouverture de la modale restaure la liste sans recalcul et sélectionne le champ texte (`searchInput.select()`).
  2. **Contrôle flottant docké** : Un bandeau discret `#search-nav-bar` (« Search Pilot ») apparaît en bas d'écran dès qu'un résultat est sélectionné. Il permet de passer au résultat suivant/précédent sans réouvrir la modale, d'afficher la position `N of Total`, ou de réouvrir la liste complète d'un clic.
  3. **Raccourcis clavier ergonomiques** : Navigation globale via `Alt + [` (Précédent) et `Alt + ]` (Suivant).
  4. **Traçage visuel d'exploration** : Tout résultat ouvert durant la session reçoit la classe `.viewed` (avec coche SVG vectorielle non déformée `.res-viewed-icon`), et le résultat actif est surligné avec `.current-result` (sans figer artificiellement le premier élément).
  5. **Historique local contextualisé & Modèle de validation délibéré (Entrée / Clic)** : Aucun résultat n'est sélectionné par défaut (`searchSelectedIndex = -1`). Lors de la saisie, un premier appui sur `Entrée` sélectionne et met en évidence le premier résultat (`.selected`), tout en enregistrant la requête dans l'historique (`localStorage`, 8 entrées max avec badge `[Standard]` ou `[AI]`). Un second appui ouvre le document. Si l'utilisateur clique directement sur un résultat sans valider par `Entrée`, la requête est également mémorisée dans l'historique. En mode IA, les suggestions de requêtes (`#modal-search-prompts`) sont positionnées avant l'historique (`#modal-recent-searches`). Les entrées d'historique s'affichent en liste plein format Spotlight avec hint clavier et suppression unitaire `✕`. Le clic sur une entrée bascule automatiquement le mode correspondant (`toggleAiSearchMode`) et lance la recherche.

### Règle 11 : Intégrité Sémantique et Remplacement In-Situ des Composants Hérités (In-Place Replacement)
- **Principe** : Ne jamais juxtaposer un nouveau composant modernisé en haut de document (`</h1>`/`</h2>`) si un composant équivalent existe déjà plus bas dans le document d'origine.
- **Règles d'implémentation** :
  1. **Remplacement in-situ** : Substituer directement l'ancien conteneur HTML (ex. `<div class=ClassHierarchy>...</div>`) par le nouveau composant interactif `.class-hierarchy-widget` au sein même de la table de sommaire (`STable`).
  2. **Typage strict des topics** : Restreindre strictement les enrichissements de classe au type `cls_name == 'CClass'`. Ne jamais appliquer de données de classe sur des en-têtes de section générale (`CSection`) ou de fichier pour éliminer toute duplication sur les pages multi-classes (ex. `uvm_pair-svh.html`).
  3. **Fallback ordonné dans le sommaire** : Si un document de classe ne possède pas l'ancien conteneur de hiérarchie, insérer la nouvelle section immédiatement avant la déclaration de classe (`Class Declaration`) dans le sommaire, et uniquement en dernier recours sous le titre si aucun sommaire n'existe.

### Règle 12 : Découplage CSS Strict pour les Éléments d'Arborescence Latérale
- **Principe** : Éviter d'assigner des classes CSS transversales génériques (ex. `.nav-item-link`) à des éléments d'arborescences spécialisées ayant leur propre conteneur de ligne (`.hierarchy-row`).
- **Règles d'implémentation** :
  1. **Absence de classes concurrentes** : Le lien interne `.hierarchy-link` ne doit pas hériter de règles d'état actif `.active` (fonds colorés, bordures latérales) réservées aux liens simples, sous peine de créer un effet disgracieux de "boîte dans une boîte" avec son conteneur parent `.hierarchy-row.active`.
  2. **Indicateur d'accent sans décalage géométrique** : Pour les arborescences à forte densité, matérialiser la sélection active via un pseudo-élément positionné en absolu (`.hierarchy-row.active::before`) de largeur fixe avec bords arrondis, sans altérer les marges ni le padding de la rangée.

---

## 4. Méthodologie de Vérification & Recette Automatisée

Chaque évolution doit être validée par une suite de vérifications à trois niveaux avant toute mise en production.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Niveau 1 : Tests Unitaires Statiques                  │
│  - scripts/test_syntax_highlighter.py (assertions lexer & tokens)      │
│  - scripts/verify_search_pilot.py (assertions DOM, CSS & JS du Search) │
│  - scripts/build_docs.py (validation de génération des 146 docs & 155 src)│
│  - scripts/build_examples.py (génération des 39 studios interactifs)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              Niveau 2 : Scripts de Vérification DOM & CSS              │
│  - verify_examples.py (27 assertions fonctionnelles sur les studios)   │
│  - verify_architecture.py (25 assertions structurelles & fonctionnelles)│
│  - verify_image_features.py (cadrage, boutons zoom, règles CSS non-bloqu)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                  Niveau 3 : Matrice de Recette Visuelle                 │
│         Vérification croisée Chrome / Firefox / Edge en local          │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Check-list de Vérification Obligatoire

Avant de valider une version :
- [ ] **Tests Unitaires de Coloration Syntaxique** : `python scripts/test_syntax_highlighter.py` (7/7 tests validés).
- [ ] **Vérification du Search Pilot & Session** : `python scripts/verify_search_pilot.py` (assertions DOM, CSS et JS validées).
- [ ] **Compilation sans erreur** : `python scripts/build_docs.py` s'exécute avec le code de retour `0`.
- [ ] **Génération des Exemples** : `python scripts/build_examples.py` génère les 39 suites sans warning.
- [ ] **Validation des Studios** : `python scripts/verify_examples.py` (27/27 assertions validées).
- [ ] **Tests d'Architecture** : Exécution de `verify_architecture.py` : les 25 tests doivent être validés (`PASS`).
- [ ] **Absence de barrière d'événements** : Vérifier que tous les backdrops de modales (`#search-modal`, `#image-zoom-modal`) sont en `display: none` et `visibility: hidden` lorsqu'ils sont inactifs.
- [ ] **Précision du scrolling** : Tester un lien vers une méthode située à plus de 15 000 px dans `uvm_component` : la section doit atterrir avec un décalage de 24 px sous le bandeau supérieur.
- [ ] **Recherche multi-mots & Search Pilot** : Taper `component build` : sélectionner un résultat, vérifier l'apparition du Search Pilot en bas d'écran (`1 of N`), naviguer avec `Alt+]`, et vérifier la présence de la coche `✓` sur les résultats consultés.
- [ ] **Cycle de sélection & Historique IA** : Aucun élément ne doit rester surligné après un clic (`searchSelectedIndex = -1`). En mode IA, la section d'historique doit toujours être visible sous les prompts (avec état vide ou requêtes enregistrées), et la touche `Entrée` doit mémoriser immédiatement la requête.
- [ ] **Mode Regex** : Taper une regex partielle `uvm_[` : la bordure doit devenir ambre/rouge sans générer d'exception console.
- [ ] **Fonctionnement hors-ligne** : Ouvrir `index.html` via le protocole `file:///` dans un navigateur sans connexion réseau active.

