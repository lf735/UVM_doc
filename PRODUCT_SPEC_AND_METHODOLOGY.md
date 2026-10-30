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
| **Shell & Layout** | **Architecture SPA** | Portail unique ([index.html](file:///c:/Users/uf755lfr/Perso/UVM_doc/index.html)) hébergeant la barre d'outils, la navigation latérale et un viewport double iframe. |
| | **Modes de Vue (View Switcher)** | **Docs** (documentation seule), **Source** (code SystemVerilog seul) et **Split** (vue côte à côte). |
| | **Split-View Redimensionnable** | Séparateur draggable (`#split-divider`) avec redimensionnement interactif et double-clic pour restaurer le ratio 50/50. |
| | **Routage par Hash** | URLs avec état profond : `#/doc/<path>#<id>`, `#/src/<path>#L<line>`, `#/split?doc=<path>&src=<path>`. |
| | **Thème Clair / Sombre** | Palette Google Developers (Light / Dark) avec bascule instantanée et propagation `postMessage` synchrone dans les iframes. |
| **Navigation Latérale** | **Multi-onglets** | 3 onglets contextuels : **Documentation** (par paquetage), **Source Tree** (arborescence des fichiers), **Index A-Z** (liste alphabétique des symboles). |
| | **Bouton Expand / Collapse All** | Bouton `#sidebar-toggle-all` permettant de déplier ou replier d'un clic tous les dossiers ou catégories visibles. |
| | **Filtre Temps Réel de Barre** | Filtrage instantané des éléments avec champ dédié, bouton effacer (`×`), mode Regex (`.*`) et pilules multi-filtres. |
| **Moteur de Recherche** | **Recherche Modale Globale** | Déclenchement via `/` ou `Ctrl+K` / `Cmd+K` couvrant 3 038 symboles et fichiers. |
| | **Distinction Function / Task** | Typage strict identifiant clairement les `functions` (non-temporelles) et les `tasks` (consommatrices de temps de simulation). |
| | **Affichage de la Classe Parente** | Présentation explicite `Classe :: Méthode` dans les résultats pour lever toute ambiguïté (ex. `uvm_driver :: run_phase`). |
| | **Recherche Multi-Mots Intelligente** | Scoring pondéré associant des termes répartis entre le nom du symbole, sa classe et sa description. |
| | **Support Regex Avancé** | Recherche par expressions régulières (`Alt+R`) avec contour d'avertissement ambre/rouge non bloquant en cas de syntaxe incomplète. |
| | **Respect de la Casse** | Bascule `Aa` (`Alt+C`) pour différencier les identifiants sensibles à la casse. |
| | **Filtres Multi-Sélection Non Exclusifs**| Pilules (`All`, `Classes`, `Functions`, `Tasks`, `Macros`, `Files`) activables simultanément sans repli forcé. |
| | **Bouton Effacer (`Clear / ×`)** | Nettoyage instantané du champ au clic ou via une première pression sur la touche `Escape`. |
| **Documentation (`docs_view`)** | **Bannière "View Source"** | En-tête injecté avec lien direct vers la ligne exacte d'implémentation dans le code source. |
| | **Sommaire Interne ("On this page")** | Barre latérale droite dynamique avec défilement espion (Scrollspy) et repli par groupes. |
| | **Défilement Précis des Liens** | Compensation de la marge supérieure (`scroll-margin-top`), suppression des conflits `scrollIntoView`, micro-ajustement géométrique. |
| | **Syntax Highlighting & Copie** | Coloration SystemVerilog des blocs `<pre>` et prototypes de méthodes avec bouton de copie en un clic. |
| **Diagrammes & Médias** | **Suppression des Sauts au Survol** | Neutralisation stricte de l'effet `transform: translateY(-2px)` sur toutes les images. |
| | **Cadrage Haute Lisibilité** | Encapsulation dans `<figure class="doc-diagram-card">` avec canevas `#ffffff` garantissant le contraste en mode sombre. |
| | **Visionneuse Zoom Plein Écran** | Modale Lightbox (`#image-zoom-modal`) avec zoom molette, déplacement drag & drop, boutons (+, -, 1:1, Fit) et raccourcis clavier. |
| | **Sécurité Non-Bloquante** | Masquage complet (`display: none; visibility: hidden; pointer-events: none;`) prévenant tout blocage d'interface à la fermeture. |
| **Explorateur Source (`src_view`)** | **Affichage SystemVerilog/C** | 155 fichiers sources colorisés avec numéros de lignes cliquables (`#L44`) et bouton retour vers la documentation. |

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
                                     │          scripts/build_docs.py          │
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
- **Conséquence** : Toutes les données d'indexation sont compilées statiquement dans [`js/search_data.js`](file:///c:/Users/uf755lfr/Perso/UVM_doc/js/search_data.js) sous forme d'un objet global `window.UVM_DATA`.

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

---

## 4. Méthodologie de Vérification & Recette Automatisée

Chaque évolution doit être validée par une suite de vérifications à trois niveaux avant toute mise en production.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Niveau 1 : Tests Unitaires Statiques                  │
│       scripts/build_docs.py (validation de génération des 146 docs)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              Niveau 2 : Scripts de Vérification DOM & CSS              │
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
- [ ] **Compilation sans erreur** : `python scripts/build_docs.py` s'exécute avec le code de retour `0`.
- [ ] **Tests d'Architecture** : Exécution de `verify_architecture.py` : les 25 tests doivent être validés (`PASS`).
- [ ] **Absence de barrière d'événements** : Vérifier que tous les backdrops de modales (`#search-modal`, `#image-zoom-modal`) sont en `display: none` et `visibility: hidden` lorsqu'ils sont inactifs.
- [ ] **Précision du scrolling** : Tester un lien vers une méthode située à plus de 15 000 px dans `uvm_component` : la section doit atterrir avec un décalage de 24 px sous le bandeau supérieur.
- [ ] **Recherche multi-mots** : Taper `component build` : `build_phase` de la classe `uvm_component` doit apparaître en tête avec les deux mots surlignés.
- [ ] **Mode Regex** : Taper une regex partielle `uvm_[` : la bordure doit devenir ambre/rouge sans générer d'exception console.
- [ ] **Fonctionnement hors-ligne** : Ouvrir `index.html` via le protocole `file:///` dans un navigateur sans connexion réseau active.

