# Retours d'Expérience & Leçons Tirées (Lessons Learned)
## Guide Pratique des Pièges Évités & Bonnes Pratiques d'Architecture Web

Ce document récapitule les incidents techniques réels, les pièges de bas niveau rencontrés durant le développement de la plateforme **UVM 1.2 Interactive Documentation**, et les solutions architecturales pérennes mises en œuvre pour les résoudre définitivement.

---

## 1. Le Piège CSS du `pointer-events: none` et des Modales Invisibles

### Le Symptôme Observé
> *"Quand la fenêtre de zoom se ferme, le site reste bloqué."*  
> Après avoir agrandi un diagramme et fermé la visionneuse de zoom, l'utilisateur ne pouvait plus cliquer sur aucun élément de l'écran (ni les liens de documentation, ni l'arborescence, ni les boutons de vue).

### L'Anatomie du Piège
En CSS moderne, l'attribut `pointer-events` possède une spécificité méconnue mais destructrice :
- Si un conteneur parent (la modale `.image-modal-backdrop`) a `pointer-events: none;` et `opacity: 0`, on pourrait croire que l'intégralité de son contenu devient invisible aux clics.
- **C'est faux** : si un élément descendant (ici `.image-modal-img`) possède explicitement `pointer-events: auto;`, **l'enfant passe outre le conteneur parent** et continue de capturer l'ensemble des événements de souris !
- Dans notre cas, l'image zoomée s'étendait sur 90% de la largeur et 90% de la hauteur de l'écran, en position `fixed`, au niveau `z-index: 2000`. Même devenue invisible (`opacity: 0`), l'image formait une plaque de verre impénétrable au centre du viewport, absorbant tous les clics destinés aux iframes ou aux boutons de l'application.

```
┌────────────────────────────────────────────────────────────────────────┐
│  .image-modal-backdrop (z-index: 2000, opacity: 0, pointer-events: none)│
│                                                                        │
│        ┌────────────────────────────────────────────────────────┐      │
│        │   .image-modal-img (pointer-events: auto) ◄── PIÈGE !  │      │
│        │   Bouclier invisible à 90% de l'écran absorbant       │      │
│        │   tous les clics de l'utilisateur !                   │      │
│        └────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

### La Règle d'Or (Le Triple Verrouillage)
Pour tout composant overlay / modal fixe :
1. **Toujours combiner `display: none` et `visibility: hidden`** dès que la modale est inactive :
   ```css
   .image-modal-backdrop {
     display: none;
     visibility: hidden;
     pointer-events: none;
     opacity: 0;
   }
   .image-modal-backdrop.open {
     display: flex;
     visibility: visible;
     pointer-events: auto;
     opacity: 1;
   }
   ```
2. **Ne jamais mettre `pointer-events: auto` sur une image passive** : l'image doit avoir `pointer-events: none;`. Si l'utilisateur clique ou glisse pour déplacer l'image, c'est le conteneur sous-jacent (`viewport`) qui doit capter l'événement.
3. **Nettoyer dans le script de fermeture** :
   ```javascript
   function closeImageZoomModal() {
     imageZoomModal.classList.remove('open');
     imageZoomModal.style.pointerEvents = 'none';
     imageZoomModal.style.display = 'none';
     imageModalImg.src = ''; // Libère la mémoire GPU
     if (document.activeElement && imageZoomModal.contains(document.activeElement)) {
       document.activeElement.blur(); // Libère le focus clavier
     }
   }
   ```

---

## 2. Le Piège du Smooth Scrolling et la Guerre Scrollspy / `scrollIntoView()`

### Le Symptôme Observé
> *"Parfois lorsque je clique sur un lien qui est loin dans la page, le scrolling ne va pas exactement à la bonne position."*  
> Sur de longs documents UVM (ex. `uvm_component` de 25 000 px de hauteur), le défilement fluide s'arrêtait en plein milieu de course ou sautait brusquement vers une autre section.

### L'Anatomie du Piège
Trois phénomènes distincts se combinaient pour perturber la navigation :
1. **L'interruption par `scrollIntoView()`** :  
   Pour garder visible l'élément actif dans le sommaire de droite ("On this page"), le code exécutait `activeLink.scrollIntoView({ block: 'nearest' })`. Or, dans plusieurs moteurs de rendu (Blink/Gecko), déclencher un `scrollIntoView()` dans un conteneur enfant pendant qu'une animation fluide de défilement est active dans la fenêtre principale **annule brutalement l'animation de défilement en cours** !
2. **La minuterie aveugle (`setTimeout`)** :  
   Le script tentait de désactiver temporairement le scrollspy pendant 800 ms pour laisser le temps au scroll de s'effectuer. Or, un défilement de 20 000 px prend plus de 1 200 ms. À 800 ms, le scrollspy se réveillait en plein vol, détectait une section intermédiaire, l'activait et coupait l'élan du défilement.
3. **La butée mécanique en bas de document** :  
   Si une méthode est située à 200 px du bas de page, le navigateur ne peut physiquement pas la remonter en haut de l'écran car le défilement atteint la butée maximale `scrollHeight - clientHeight`.

### La Solution Appliquée
1. **Marge de confort en bas de page** : Ajout de `padding-bottom: 60vh;` sur `.doc-main-content` afin que chaque élément, même le dernier du document, dispose de l'espace nécessaire pour venir se positionner confortablement en haut du viewport.
2. **Suppression de `scrollIntoView()`** : Remplacement par une fonction dédiée `scrollTocToItem()` qui n'opère que sur la barre latérale via `tocSidebar.scrollTo({ top: ... })`, sans jamais toucher à la fenêtre principale.
3. **Verrou dynamique et écoute de `scrollend`** :
   ```javascript
   let isManualScrolling = false;
   let manualScrollTimer = null;

   window.addEventListener('scrollend', () => {
     if (isManualScrolling) checkAndCorrectScroll();
   });
   ```
4. **Passe de micro-ajustement géométrique (`checkAndCorrectScroll`)** : Dès que le défilement se stabilise, le script mesure la position réelle de l'élément cible par rapport au haut de l'écran (`getBoundingClientRect().top`). Si un écart supérieur à 6 px subsiste, une micro-correction instantanée le replace au pixel près sous la bannière.

---

## 3. Le Piège de la Modernisation du HTML Hérité (Natural Docs 2014)

### Le Problème
Les pages UVM générées par *Natural Docs* utilisaient une syntaxe d'ancres archaïque :
```html
<!-- Ancien format -->
<a name="uvm_component.build_phase"></a>
<a href="#uvm_component.build_phase">build_phase</a>
```
Dans une SPA moderne, les identifiants d'éléments doivent respecter la syntaxe d'identifiant valide du DOM (`id="doc-nav-item-4"`).

### Les Pièges Rencontrés
- Les noms d'ancres contenaient des points (`.`), des deux-points (`::`) et des espaces. En JavaScript, `document.querySelector('#uvm_component.build_phase')` lève une exception de syntaxe car le point est interprété comme une classe CSS !
- Tenter d'attribuer des identifiants à la volée côté client au chargement de chaque iframe créait un désalignement avec les liens inter-fichiers (`href="uvm_root-svh.html#uvm_top"`).

### La Solution en Deux Passes Côté Build
Dans [`scripts/build_docs.py`](file:///c:/Users/uf755lfr/Perso/UVM_doc/scripts/build_docs.py) :
- **Passe 1** : Pré-scan de l'ensemble des 146 fichiers pour dresser le dictionnaire complet de correspondance `(fichier, ancre) -> id_normalisé`.
- **Passe 2** : Réécriture systématique dans le code HTML statique :
  - Chaque titre reçoit son identifiant propre : `id="doc-nav-item-4" data-anchor="uvm_component.build_phase"`.
  - La balise d'origine conserve `name="..."` et reçoit `id="..."` pour préserver la rétrocompatibilité des liens profonds.
  - Tous les liens intra-pages et inter-pages sont réécrits avec leur `data-target-id` exact.

---

## 4. Les Pièges du Moteur de Recherche Interne & Regex

### Piège 4.1 : L'exception fatale sur Regex non terminée
Lorsqu'un utilisateur tape une expression régulière dans un champ avec recherche en temps réel :
- Dès qu'il tape `uvm_[`, `uvm_(` ou `*`, `new RegExp(query)` lève immédiatement une exception `SyntaxError: Unterminated character class`.
- Si l'exception n'est pas interceptée, le script JS plante, la saisie se fige et la liste de résultats ne se met plus à jour.
- **Règle** : Toujours encapsuler l'instanciation de `RegExp` dans un `try...catch` et transformer l'erreur en indicateur visuel bienveillant :
  ```javascript
  try {
    regex = new RegExp(pattern, flags);
    return { valid: true, regex };
  } catch (err) {
    // Ne jamais crasher la console ni interrompre la frappe
    return { valid: false, error: err.message, type: 'regex' };
  }
  ```
  Le contour du champ prend alors une discrète lueur d'avertissement (`.regex-error`), sans bloquer la frappe de l'utilisateur.

### Piège 4.2 : La recherche multi-mots à travers les classes
- Une requête comme `component build` tapée par un ingénieur signifie : *"Je cherche la méthode `build` dans la classe `component`"*.
- Si l'algorithme teste uniquement si la chaîne brute `"component build"` est présente dans le nom du symbole, il ne trouvera rien.
- **Règle** : Découper la requête en mots (`tokens`) et calculer une note de pertinence (*scoring*) :
  - Tous les mots dans le nom du symbole : score maximal (800).
  - Un mot dans la classe parente et un mot dans la méthode : score élevé (700).
  - Tous les mots surlignés individuellement dans l'interface (`highlightMatch`).

### Piège 4.3 : Le modèle mental des filtres non exclusifs
- Lorsque des filtres sont proposés (`Classes`, `Functions`, `Tasks`, `Macros`) :
- **Piège UX** : Si l'utilisateur clique successivement sur tous les boutons pour tout voir, désélectionner automatiquement tous les filtres pour n'activer que `All` désoriente l'utilisateur.
- **Règle** : Si l'utilisateur a sélectionné explicitement tous les boutons, **ils doivent rester tous visuellement actifs**. Seul un clic délibéré sur le bouton `All` doit réinitialiser la sélection.

---

## 5. Les Pièges de la Communication Inter-Frames (postMessage)

### Le Problème du Contexte Local (`file://`)
En environnement local ou corporate sécurisé, les documents sont ouverts via `file:///C:/...`.
- Sous `file://`, la valeur de `window.location.origin` est la chaîne `"null"`.
- Tout appel de type `targetWindow.postMessage(data, window.location.origin)` échoue silencieusement avec une erreur de sécurité.
- **Règle** : Pour les outils distribuables localement en mode zéro-serveur, utiliser `postMessage(data, '*')` et valider rigoureusement le type et la structure de l'objet de données reçu côté récepteur :
  ```javascript
  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.type === 'openImageModal') { ... }
  });
  ```

### Le Piège de la Capture des Touches Clavier
Quand l'utilisateur clique dans la documentation, le focus du navigateur passe à l'intérieur de l'iframe `docs_view`.
- Si l'utilisateur presse la touche `Échap` pour fermer la visionneuse d'image ou la recherche, l'événement `keydown` se déclenche dans l'iframe, et non dans la fenêtre principale !
- **Règle** : Chaque iframe doit relayer les touches de contrôle au parent :
  ```javascript
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'closeImageModal' }, '*');
    }
  });
  ```

---

## 6. Les Pièges de l'Environnement Windows & PowerShell

### Piège 6.1 : Les guillemets dans les commandes inline PowerShell
Sous PowerShell Windows :
- Exécuter des commandes du type `python -c "import re; print(\"...\")"` échoue quasi-systématiquement car le moteur d'analyse de PowerShell réinterprète et supprime les guillemets échappés.
- **Règle** : Ne jamais exécuter de logique Python complexe en ligne de commande inline. Toujours écrire un script scratch dédié dans `scratch/script.py` et l'exécuter via `python scratch/script.py`.

### Piège 6.2 : Les f-strings Python contenant du JavaScript
Dans le générateur de documentation [`scripts/build_docs.py`](file:///c:/Users/uf755lfr/Perso/UVM_doc/scripts/build_docs.py) :
- Les fichiers HTML générés intègrent des balises `<script>` contenant des objets et fonctions JavaScript avec des accolades `{ ... }`.
- Dans une f-string Python (`f"""..."""`), toute accolade simple est interprétée comme une variable Python.
- Si une accolade n'est pas doublée (`{{` et `}}`), Python lève un `KeyError` ou corrompt silencieusement le script généré.
- **Règle** : Pour tout template HTML/JS généré par Python, doubler méticuleusement chaque accolade JS (`function() {{ ... }}`) ou séparer les scripts volumineux dans des fichiers statiques importés.

---

## 7. Synthèse des Bonnes Pratiques pour les Projets Futurs

| Domaine | Pratique Recommandée | Ce qu'il faut absolument éviter |
| :--- | :--- | :--- |
| **CSS Overlay** | `display: none; visibility: hidden; pointer-events: none;` | Se reposer uniquement sur `opacity: 0` ou `pointer-events: none` sur le parent. |
| **Images plein écran** | `pointer-events: none;` sur l'élément `<img>` de la modale. | Mettre `pointer-events: auto;` sur une image flottante dans une modale. |
| **Scrolling & TOC** | Mesure d'offset géométrique + écoute de fin réelle de scroll. | Utiliser `scrollIntoView()` au sein d'une sidebar pendant un défilement. |
| **Pages très longues** | Ajouter `padding-bottom: 50vh` à `60vh` sur le corps de texte. | Laisser le bas de page en butée sans marge d'accès pour les derniers ancrages. |
| **Moteur Regex** | `try...catch` obligatoire avec feedback de bordure d'avertissement. | Laisser l'exception `SyntaxError` se propager dans le gestionnaire d'événement. |
| **Recherche Multi-termes**| Tokenisation des mots et calcul de score multi-champs. | Comparaison naïve `item.name.includes(query)`. |
| **Architecture SPA** | Shell parent source de vérité unique (Hash URL, Thème, Modales). | Synchronisation décentralisée ou modification directe du hash depuis les iframes. |
| **Outillage Python** | Scripts autonomes `.py` dans un dossier scratch. | Lignes de commande inline complexes `python -c "..."` sous PowerShell. |

---

## 8. Gestion des Gros Fichiers Générés et CI/CD (GitHub Pages)

### Le Problème du Fichier `js/search_data.js`
Le fichier de données de recherche [`js/search_data.js`](file:///c:/Dev/UVM_doc/js/search_data.js) regroupe l'ensemble des index, catégories et symboles, pour un poids d'environ 1,5 Mo.
- À chaque mise à jour de la documentation ou des sources, ce fichier volumineux change dans son intégralité.
- Versionner un tel fichier dans Git produit un encombrement rapide de l'historique (.git bloat) et un churn de commit inutile.

### La Solution Mise en Œuvre
1. **Exclusion Git** : `js/search_data.js` est retiré de l'index (`git rm --cached`) et ignoré dans [`.gitignore`](file:///c:/Dev/UVM_doc/.gitignore).
2. **Génération au Déploiement** : Le workflow GitHub Actions ([`.github/workflows/deploy.yml`](file:///c:/Dev/UVM_doc/.github/workflows/deploy.yml)) configure Python et exécute [`scripts/build_docs.py`](file:///c:/Dev/UVM_doc/scripts/build_docs.py) sur le runner Ubuntu juste avant le packaging et le déploiement sur GitHub Pages.
3. **Fins de ligne déterministes (`LF`)** : En spécifiant `open(..., 'w', encoding='utf-8', newline='\n')`, Python sous Windows écrit systématiquement des retours chariot Unix `\n`, éliminant les diffs fantômes causés par CRLF.
4. **Mode Rapide `--search-only`** : Pour le développement local, une option `--search-only` permet de regénérer uniquement `search_data.js` en moins d'une seconde en lisant les en-têtes directement depuis `docs_view` sans devoir réécrire l'ensemble des 300+ pages HTML.
5. **Résilience Frontend** : Si un développeur ouvre `index.html` en local sans avoir généré l'index, la barre latérale affiche un message d'aide explicite indiquant la commande à lancer.

---

## 9. Architecture RAG Client-Side (Embeddings Vectoriels & Transformers.js)

### 9.1 Découpage Sémantique Enrichi (*Contextual Retrieval*)
- Pour un corpus technique structuré (comme la documentation de l'IEEE 1800 UVM), un découpage naïf en blocs de caractères détruit le sens (signatures tronquées, méthodes isolées de leur classe).
- **Règle** : Chaque segment doit être injecté d'un en-tête contextuel :
  `[UVM 1.2 Method] [{class_name}::{method_name}] Class: {class_name}. Category: {category}.`
  Cela permet aux modèles d'embedding de comprendre immédiatement le contexte parent sans devoir augmenter artificiellement la taille du chunk.

### 9.2 Calcul Vectoriel Instantané en TypedArrays
- Pour 2 500 segments et un vecteur de dimension 384 :
  - Stocker les données sous forme de fichier binaire brut `Float32Array` contigu (`rag_embeddings.bin`) ne pèse que 3,8 Mo (contre > 15 Mo en JSON textuel).
  - Le chargement en mémoire se fait via `new Float32Array(arrayBuffer)` en 0 ms.
  - Le produit scalaire (similarité cosinus) sur 2 500 vecteurs en JavaScript s'exécute en **moins de 3 millisecondes** grâce aux optimisations SIMD des moteurs V8 modernes.

### 9.3 Gestion du Cycle de Vie Mémoire (RAM vs Disque)
- Les modèles WASM/ONNX peuvent rapidement consommer 60 à 150 Mo de RAM dans le processus du navigateur.
- **Règle** : Dissocier strictement le stockage persistant sur disque (géré par la `Cache API`) de l'instance en mémoire vive (RAM).
  - La RAM du modèle est libérée dès la fermeture de la modale de recherche ou après 3 minutes d'inactivité via `session.release()`.
  - Au rechargement, le modèle se réinstancie depuis le cache disque local sans aucun appel réseau.

### 9.4 Extraits Intelligents (*Smart Snippets*) sans Surcharge
- Plutôt que d'exécuter un modèle NLP lourd pour générer des résumés, le système découpe le segment en phrases via regex et calcule la densité de pertinence textuelle uniquement sur le **Top 10** des résultats au moment de l'affichage (< 2 ms).

---

## 10. Pièges de Structuration des Données Héritées & Parsing Multi-Sujets

### Piège 10.1 : La Confusion entre "Contents" et "Summary"
- **Symptôme** : Dans les fichiers multi-classes (ex. `uvm_port_base-svh.html`, `uvm_callback-svh.html`, 53 fichiers au total), cliquer sur "Summary" dans le sommaire scrollait vers une table intitulée `Contents` (la liste des classes du fichier), tandis que les véritables tables de méthodes des classes étaient écrasées ou confondues.
- **Cause racine** : NaturalDocs génère la même classe CSS `<div class=Summary>` pour la table récapitulative des contenus du fichier (`<div class=STitle>Contents</div>`) et pour les résumés des méthodes de chaque classe (`<div class=STitle>Summary</div>`). Un simple remplacement global par chaîne de caractères dans `build_docs.py` attribuait le même identifiant dupliqué `id="doc-nav-summary"` à toutes ces tables !
- **Solution pérenne** :
  1. Inspecter le contenu textuel réel de chaque `<div class="STitle">` lors du parsing Python.
  2. Assigner des identifiants et des classes CSS spécifiques et uniques :
     - Table globale de fichier : `id="doc-nav-contents" data-anchor="Contents"` avec classe `.ContentsSummary`.
     - Tables de résumés par classe : `id="doc-nav-summary-{topicId}" data-anchor="Summary-{topicId}"` avec classe `.ClassSummary`.
  3. Mettre à jour `extract_doc_headings()` pour enregistrer séparément l'ancre `Contents` et l'ancre `Summary` dans l'arbre documentaire.

### Piège 10.2 : Le Double Échappement des Entités HTML dans les Menus et Listes
- **Symptôme** : Des titres comme `TLM Generic Payload &amp; Extensions` ou `What&rsquo;s Changed` s'affichaient avec leurs entités HTML littérales dans le menu de gauche et les info-bulles.
- **Cause racine** : `menu.html` et les fichiers HTML NaturalDocs stockaient déjà du texte contenant des entités HTML (`&amp;`, `&rsquo;`). Côté frontend, les fonctions d'affichage et de surbrillance (`highlightMatch()`) appelaient à leur tour `escapeHtml(text)`. Le `&` de `&amp;` était ainsi ré-échappé en `&amp;amp;`, produisant un double échappement visible.
- **Règle d'or** :
  - **Toutes les chaînes extraites de HTML lors du build doivent être normalisées en texte brut** via `html.unescape()` avant d'être insérées dans les structures de données JSON / JS (`search_data.js`).
  - Le frontend peut alors appliquer sereinement son propre échappement XSS (`escapeHtml`) au moment du rendu sans risque de double échappement.

### Piège 10.3 : Récursion Infinie des Iframes par Clics Relatifs
- **Symptôme** : Cliquer sur le logo ou le lien racine d'un fil d'Ariane (`doc-breadcrumbs`) à l'intérieur d'une page de documentation ouvrait une réplique complète du portail principal `index.html` à l'intérieur de la sous-iframe (mise en abyme).
- **Règle d'or** :
  - Pour tout lien renvoyant vers le shell de navigation ou la racine de l'application, toujours forcer la cible au niveau supérieur (`target="_top"`).
  - Côté contrôleur client (`doc_page.js`), intercepter les clics sur les éléments de fil d'Ariane racine pour communiquer avec le parent via `window.parent.postMessage({ type: 'openDocView', ... })` au lieu de laisser le navigateur résoudre l'URL localement dans l'iframe.

### Piège 10.4 : Clarté Visuelle & État par Défaut des Cartes de Sous-Classes (`derived-classes-card`)
- **Symptôme** : L'injection de la liste des sous-classes polymorphiques sous le titre de chaque classe occupait un espace vertical important dès l'ouverture de la page, masquant la description et les méthodes principales.
- **Solution pérenne** :
  - Encapsuler la liste dans une carte stylisée discrète dotée d'une bordure latérale Google Blue (`.derived-classes-card`).
  - **Replier la carte par défaut** via la classe `.collapsed` (`display: none` sur la liste des pilules).
  - Fournir un en-tête cliquable (`role="button"`, `tabindex="0"`) avec un chevron rotatif animé et un gestionnaire d'événements clavier (`Entrée` / `Espace`) et souris.

### Piège 10.5 : Précision du Routage Profond vers les Classes Dérivées
- **Symptôme** : Les pilules de sous-classes renvoyaient vers l'ancre générique `#doc-nav-main`. Si la classe cible partageait un fichier avec d'autres classes (fichiers multi-classes), le clic atterrissait en haut du fichier plutôt qu'au niveau du titre de la classe cible.
- **Solution pérenne** : Lors de la génération des pilules dans `build_docs.py`, consulter le dictionnaire global d'ancres `GLOBAL_DOC_ANCHOR_MAPS[doc_file]` pour pointer vers l'identifiant exact de la classe (`#doc-nav-item-X`) avec l'attribut `data-target-id`.

### Piège 10.6 : Bouton de Copie d'Ancre Directe au Survol des Titres
- **Pattern moderne (Google Developer Docs)** : Les titres de rubriques et de méthodes affichent une icône de chaîne de lien au survol (`.doc-anchor-link-btn`).
- **Piège UX** : Si le clic effectue uniquement une copie dans le presse-papiers sans retour visuel, l'utilisateur doute de la prise en compte de l'action.
- **Solution** :
  1. Copie de l'URL complète avec le hash profond correspondant (`location.origin + location.pathname + '#' + targetId`).
  2. Remplacement temporaire (1,5 s) de l'icône par un checkmark vert accompagné d'un tooltip *"Link copied!"* avec classe `.copied`.

---

## 11. Leçons Tirées sur l'Architecture d'Arborescence & Navigation Multi-Onglets

### Piège 11.1 : L'Infiltration des En-Têtes de Licence / Copyright dans l'AST et les Pages Générées
- **Symptôme** : Dans les fichiers sources sans bloc de documentation NaturalDocs formel (ex. `uvm_sequencer_analysis_fifo.svh`, `uvm_spell_chkr.svh`, `uvm_resource_converter.svh`), le résumé de classe affichait le texte brut de la licence Apache et du copyright (`Copyright 2007-2011 Mentor Graphics... All Rights Reserved Worldwide`).
- **Cause racine** : L'analyseur AST Python (`build_uvm_source_db.py:parse_doc_above`) cherchait les commentaires immédiatement au-dessus de la ligne de déclaration `class ...`. Lorsque aucun commentaire de doc n'était présent, la remontée atteignait l'en-tête de fichier de licence/copyright et le capturait comme docstring de la classe.
- **Solution architecturale pérenne** :
  1. Détection systématique des en-têtes légaux dans `clean_doc_comment()` : si le bloc commence par `copyright`, `all rights reserved` ou `licensed under the apache license`, le bloc entier est ignoré sauf si une vraie balise de doc (`CLASS:`, `Function:`) apparaît plus bas.
  2. Garde-fou défensif dans le générateur HTML (`build_docs.py`) : toute description contenant des mentions légales est interceptée et remplacée par une description technique propre (`Class <name> defined in src/<file>`).
  3. Résultat : 0 mention de copyright parasite résiduelle dans les bases de données et les pages générées.

### Piège 11.2 : Les Titres de Groupes comme Pages d'Accueil de Sections (Section Overviews)
- **Symptôme** : Cliquer sur le titre d'une grande section dans le menu de gauche ne faisait que déplier/replier la liste, forçant l'utilisateur à chercher et cliquer sur un élément enfant nommé "Overview".
- **Solution architecturale** :
  - Lors de l'analyse du menu (`build_docs.py:parse_snippet`), si le premier enfant d'un groupe est un fichier d'aperçu (`Overview`), son URL est attachée directement à l'en-tête du groupe sous la propriété `overviewHref`, et cet enfant est retiré de la liste des sous-éléments pour éviter la redondance.
  - L'en-tête du groupe dans le menu combine un lien cliquable (`.nav-group-title-link`) qui ouvre la page d'overview, et un bouton chevron distinct (`.nav-group-chevron-btn`) dédié au dépliement/repliement.

### Piège 11.3 : Les Fils d'Ariane Intermédiaires Cliquables & Élimination du Segment Technique "Overviews"
- **Symptôme** : Les fils d'Ariane (`doc-breadcrumbs`) affichaient des catégories intermédiaires non cliquables (`<span>`) ou inséraient un segment technique `Overviews` sans valeur ajoutée pour l'utilisateur (`Home / Overviews / Core Base Classes`).
- **Solution** :
  - Construction d'un index ascendant hiérarchique reliant chaque page à la chaîne de ses groupes parents et à leurs pages d'overview respectives.
  - Suppression automatique du préfixe de dossier physique `overviews/` dans la hiérarchie affichée : les aperçus de premier niveau affichent `Home / Nom de la section`, tandis que les sous-groupes affichent `Home / Section Parente / Sous-Section`.
  - Clics interceptés dans `doc_page.js` pour communiquer via `window.parent.location.hash` sans recharger les iframes.

### Piège 11.4 : Alignement et Hiérarchie de l'Arborescence dans la Barre Latérale
- **Symptôme** : Les sous-groupes imbriqués (comme `TLM1`, `TLM2`, `Register Model`) subissaient un décalage horizontal inline arbitraire (`margin-left: 0.5rem; font-size: 0.775rem`) causant un désalignement avec les éléments frères et parents.
- **Solution** :
  - Standardisation de la taille et de la structure de tous les en-têtes de groupes.
  - Utilisation d'un guide visuel d'arborescence CSS moderne : chaque conteneur de sous-éléments (`.nav-group-items`) possède une bordure fine à gauche (`border-left: 1px solid var(--border-subtle);`) avec une indentation maîtrisée (`0.85rem`).
  - Alignement au pixel près des éléments racine uniques (`.nav-single-item`) avec les en-têtes de groupes.

### Piège 11.5 : La Sous-Barre de Navigation Pleine Largeur (Full-Width Navigation Sub-Bar)
- **Symptôme** : L'intégration des 4 onglets majeurs de navigation (`Documentation`, `Source Tree`, `Examples`, `Index A-Z`) dans la colonne latérale restreinte (320px) créait un encombrement visuel et comprimait les libellés.
- **Solution** :
  - Déplacement de ces 4 sections dans une sous-barre horizontale dédiée (`<nav class="app-subbar">`) occupant 100% de la largeur de l'écran directement sous le header principal.
  - Chaque section dispose d'une icône vectorielle explicite et d'un grand confort de lecture, tout en libérant l'intégralité de la hauteur de la barre latérale pour la recherche et l'arbre de navigation.

---

## 12. Pièges et Bonnes Pratiques de la Coloration Syntaxique SystemVerilog & Multi-Langages

### Piège 12.1 : L'Écrasement Sémantique des Tokens et l'Uniformité Monotone (Le Piège du "Tout-en-Violet")
- **Symptôme** : Dans les versions initiales, les mots-clés de contrôle (`if`, `case`, `return`), les déclarations structurelles (`class`, `module`, `task`, `function`), les types primitifs (`logic`, `bit`, `int`, `void`, `string`), les qualificateurs OOP (`virtual`, `rand`, `local`) et les classes UVM étaient tous regroupés dans une liste unique de mots-clés sous la même classe `.sv-keyword` (#af00db en clair, #c58af9 en sombre).
- **Conséquence UX** : Le code était visuellement plat et difficile à scanner pour un ingénieur de vérification. Impossible de repérer en un coup d'œil la frontière entre la structure d'une classe, ses types et ses structures de contrôle.
- **Solution architecturale** :
  - Décomposition stricte en catégories de tokens spécialisées :
    - `.sv-keyword` : Mots-clés de contrôle et exécution (`if`, `else`, `case`, `for`, `fork`, `join`, `begin`, `end`, etc.).
    - `.sv-keyword-decl` : Mots-clés de déclaration (`class`, `module`, `task`, `function`, `package`, `typedef`, etc.).
    - `.sv-type` : Types de données IEEE 1800 (`bit`, `logic`, `byte`, `int`, `time`, `string`, `void`, etc.).
    - `.sv-qualifier` : Modificateurs d'accès et de stockage (`virtual`, `local`, `protected`, `rand`, `static`, etc.).
    - `.sv-constant` : Littéraux constants (`null`, `this`, `super`, `UVM_LOW`, `UVM_NONE`, `UVM_ALL_ON`, etc.).
  - Palette CSS haute lisibilité inspirée des IDEs modernes (VS Code, JetBrains, DVT Eclipse) avec contrastes conformes WCAG AA.

### Piège 12.2 : Le Piège du Préfixe `$` des Tâches et Fonctions Système (`$display`, `$cast`, `$time`)
- **Symptôme** : Les appels système fondamentaux de SystemVerilog (`$display`, `$cast`, `$time`, `$sformatf`, `$finish`, `$urandom_range`) s'affichaient sans coloration : le caractère `$` était isolé comme un opérateur de ponctuation générique (`.sv-op`), tandis que le nom de la tâche était rendu en texte noir ordinaire (`.sv-ident`).
- **Cause racine** : L'expression régulière du tokenizer analysait les opérateurs via `[#+\-*/%=&|~^!<>?:;.,()\[\]{}]` (incluant ou excluant `$`), tandis que l'analyse des identifiants utilisait `[a-zA-Z_][a-zA-Z0-9_]*` sans prise en compte du préfixe `$`.
- **Solution** :
  - Introduction d'une règle de tokenisation prioritaire dédiée :
    ```python
    r'(?P<SYSTEM_TF>\$[a-zA-Z_][a-zA-Z0-9_$]*)'
    ```
  - Attribué à la classe `.sv-system-tf` stylisée dans une nuance ambrée/orange vive (`#b35900` en clair, `#f0883e` en sombre).

### Piège 12.3 : La Détection Contextuelle des Méthodes sans Parenthèses en SystemVerilog
- **Symptôme** : En SystemVerilog, une fonction ou tâche sans arguments peut être déclarée ou implémentée sans parenthèses vides :
  ```systemverilog
  function void uvm_component::m_do_pre_abort;
  pre_abort();
  ```
  Un tokenizer classique basé uniquement sur un lookahead `(` identifiait `pre_abort()` comme méthode, mais laissait `m_do_pre_abort` en texte ordinaire (`sv-ident`) !
- **Solution** :
  - Détection contextuelle bidirectionnelle (lookahead et lookbehind) :
    1. Si l'identifiant est immédiatement suivi d'une parenthèse ouvrante `(` -> `.sv-method`.
    2. Si l'identifiant est précédé de l'opérateur de portée `::` et que la ligne contient une déclaration `function` ou `task` ou se termine par `;` -> `.sv-method`.
    3. Si l'identifiant appartient au dictionnaire des méthodes canoniques du cycle de vie UVM (`KNOWN_UVM_METHODS` : `build_phase`, `connect_phase`, `run_phase`, `raise_objection`, `drop_objection`, `start_item`, `create`, etc.) -> `.sv-method`.

### Piège 12.4 : La Fragmentation des Opérateurs Multi-Caractères (`::`, `->`, `<=`, `&&`)
- **Symptôme** : Une expression comme `uvm_component::type_id` était découpée en :
  `<span class="sv-op">:</span><span class="sv-op">:</span>` au lieu d'un token unitaire `::`.
- **Cause racine** : Utilisation d'une classe de caractères Regex à un seul caractère `[#+\-*/%=&|~^!<>]` appliquée caractère par caractère.
- **Solution** :
  - Regex ordonné plaçant les opérateurs multi-caractères les plus longs en tête de l'alternative :
    ```python
    r'(?P<OP>::|->>|->|<=|>=|===|!==|==\?|!=\?|==|!=|&&|\|\||\+:|-:|\+:=|-:=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|<<<=|>>>=|<<<|>>>|<<|>>|\+\+|--|\|->|\|=>|##|@@|#\(|[#+\-*/%=&|~^!<>?:;.,()\[\]{}])'
    ```
  - Les opérateurs composés sont ainsi émis sous un seul élément HTML propre et atomique (`<span class="sv-op">::</span>`).

### Piège 12.5 : Le Piège de l'Échappement des Apostrophes dans `html.escape()` (`8'hA5`)
- **Symptôme** : Les nombres basés SystemVerilog (`8'hA5`, `32'hDEAD_BEEF`, `'0`, `'1`) généraient `<span class="sv-number">8&#x27;hA5</span>`.
- **Cause racine** : En Python 3.8+, `html.escape(s, quote=True)` remplace par défaut l'apostrophe `'` par l'entité `&#x27;`.
- **Bonne pratique** :
  - S'assurer que le tokenizer capture le littéral basé dans sa globalité via `\b\d+\s*\'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xzXZ]+\b` pour que le nombre entier soit encapsulé dans un unique span `.sv-number`.
  - Dans les suites de tests unitaires, vérifier la compatibilité des assertions sur les deux formes de chaîne (`'8\'hA5'` et `'8&#x27;hA5'`).

### Piège 12.6 : La Duplication de Code de Coloration entre Scripts (`build_docs.py` vs `build_examples.py`)
- **Symptôme** : Initialement, `build_docs.py` possédait son propre tokenizer, et `build_examples.py` en possédait un second distinct. Les exemples interactifs n'avaient pas le même rendu que les sources officielles, et tout ajout de mot-clé devait être dupliqué dans deux fichiers.
- **Solution architecturale pérenne** :
  - Création d'un module unique et partagé `scripts/syntax_highlighter.py`.
  - `build_docs.py` et `build_examples.py` importent ce module comme source de vérité unique.
  - Ajout d'une suite de tests unitaires dédiée `scripts/test_syntax_highlighter.py` intégrée au cycle de recette automatisé.

---

## 13. Le Piège de l'Effacement Destructif de Recherche & La Barre Flottante (« Search Pilot »)

### Le Symptôme Observé
> *"Quand l'utilisateur clique sur un résultat, il faut qu'il puisse revenir aux autres résultats."*  
> Dans l'implémentation initiale, cliquer sur un résultat de recherche fermait la modale et réinitialisait complètement la requête (`searchInput.value = ''`). Pour consulter un second résultat d'une même recherche (par exemple en comparant différentes implémentations de `phase_ready_to_end` ou `uvm_sequence_base`), l'utilisateur devait ré-ouvrir la modale, retaper sa requête en entier, ré-appliquer ses filtres et faire défiler à nouveau les résultats.

### Piège 13.1 : La Réinitialisation Destructrice de l'Input lors de l'Ouverture de Modale
- **Cause racine** : La fonction `openSearchModal()` exécutait inconditionnellement `searchInput.value = ''; executeSearch('');` à chaque ouverture. Ce comportement, classique sur les moteurs de recherche simplistes, brise totalement le flux de travail exploratoire d'un ingénieur consultant une documentation technique.
- **Solution** :
  - Introduction d'un état de session actif non-destructif `activeSearchSession` :
    ```javascript
    const activeSearchSession = {
      query: '',
      mode: 'standard', // 'standard' | 'ai'
      results: [],
      currentIndex: -1,
      viewedIndices: new Set(),
      isActive: false
    };
    ```
  - Lors de la réouverture (via le bouton « Search », le raccourci `/`, `Ctrl+K` ou le bouton « All Results »), `openSearchModal({ preserveSession: true })` restaure la requête, restitue les résultats instantanément sans recalcul, et sélectionne le champ (`searchInput.select()`). L'utilisateur peut ainsi continuer sa navigation ou écraser sa saisie d'une seule touche.

### Piège 13.2 : L'Effet Tunnel du Résultat Unique & La Solution « Search Pilot »
- **Problème** : Consulter une liste de résultats à travers une modale pleine page crée une friction cognitive majeure : la modale masque le contenu du document, empêchant de lire et de naviguer simultanément dans la liste des correspondances.
- **Solution architecturale pérenne** :
  - Déploiement d'une barre de contrôle flottante discrète et dockée en bas de l'écran : `#search-nav-bar` (« Search Pilot »).
  - Dès qu'un résultat est sélectionné, le Search Pilot affiche la requête, le compteur de position (`N of Total`), deux boutons de saut rapide `◀ Précédent` et `▶ Suivant`, un bouton de réouverture immédiate de la modale complète `All Results`, et un bouton de fermeture `✕`.
  - Intégration de raccourcis clavier globaux non-conflictuels : `Alt + [` (Précédent) et `Alt + ]` (Suivant).

### Piège 13.3 : Le Traçage Visuel des Éléments Consultés (`.viewed` et `.current-result`)
- **Problème** : Lors du retour dans la modale de recherche avec 30 ou 50 résultats, l'utilisateur oubliait quels symboles avaient déjà été examinés.
- **Solution** :
  - Traçage dans un `Set` (`activeSearchSession.viewedIndices`) de tous les index consultés durant la session de recherche.
  - Ajout des classes CSS `.current-result` (surlignage accentué et barre latérale primaire) et `.viewed` (opacité adoucie et coche verte/primaire injectée via un composant vectoriel SVG dédié).

### Piège 13.4 : La Présentation Visuelle Bancale des Recherches Récentes (Pilules Squelettiques vs Liste Native)
- **Symptôme** : L'affichage initial des recherches récentes utilisait un conteneur rigide de 85px max (`max-height: 85px`) avec des pilules enroulées horizontalement et une bordure inférieure arbitraire. En dessous, la zone de résultats laissait un grand vide blanc ou sombre, donnant une impression de composant "bancal" et inachevé. De plus, aucune suppression unitaire n'était possible (seul un bouton "Clear" effaçant tout l'historique était présent).
- **Solution architecturale pérenne** :
  - Restructuration complète de `.modal-recent-searches` en conteneur pleine hauteur (`flex: 1; overflow-y: auto`).
  - Passage d'un nuage de tags étriqué à une liste verticale élégante (`.recent-search-row`) calquée sur le modèle des résultats de recherche :
    1. Icône historique horloge discrète virant au bleu primaire au survol.
    2. Typographie monospace propre pour le terme recherché.
    3. Indication contextuelle subtile « Jump to search ↵ » apparaissant au survol de la ligne.
    4. Bouton de suppression individuelle `✕` permettant d'effacer une requête erronée d'un clic sans vider tout son historique.
    5. Gestion d'un état d'accueil chaleureux quand l'historique est vide invitant à la découverte des 3 096 symboles UVM.

### Piège 13.5 : La Déformation des Glyphes Unicode dans les Conteneurs Monospace (`Consolas` vs `content: " ✓"`)
- **Symptôme** : Dans la recherche standard (sans IA), la coche de validation `✓` apparaissait étirée, crénelée, écrasée ou disproportionnée, alors qu'en mode IA elle s'affichait normalement.
- **Cause racine** :
  - Dans la recherche standard, le pseudo-élément `::after` était rattaché à `.res-name` (`.search-result-item.viewed .res-name::after`).
  - Or, `.res-name` possède la règle `font-family: var(--font-mono)` (Consolas sous Windows, Menlo/Monaco sous macOS).
  - La police Consolas ne contient pas le glyphe Unicode `✓` (U+2713). Le moteur de rendu de Windows effectuait un *font fallback* arbitraire (ex. MS Gothic ou Segoe UI Symbol) en tentant d'étirer ou de forcer le glyphe dans une cellule de largeur fixe monospace, provoquant une distorsion géométrique disgracieuse.
- **Solution architecturale pérenne** :
  - Bannir les caractères textuels Unicode arbitraires dans les pseudo-éléments de chaînes typées en police monospace.
  - Remplacer le `::after` par un badge d'icône vectoriel SVG dédié (`.res-viewed-icon`) :
    ```html
    <span class="res-viewed-icon" title="Viewed in this session">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
    </span>
    ```
  - L'icône est désormais 100% vectorielle, indépendante de la police système, parfaitement centrée verticalement et nette sur tous les écrans (Retina, 4K, Dual-Theme).

### Piège 13.6 : Le Surlignage Forcé de l'Index 0 (`idx === 0`)
- **Symptôme** : Le premier résultat de recherche restait perpétuellement surligné en bleu, même lorsque l'utilisateur cliquait sur un autre résultat.
- **Cause racine** : La boucle de rendu des résultats appliquait en dur `if (idx === 0) itemClasses.push('selected');`, attribuant la classe de sélection au premier élément sans tenir compte de l'index réel actif.
- **Solution** :
  - Suppression de la condition en dur. L'élément actif reçoit `.current-result` uniquement s'il correspond à `activeSearchSession.currentIndex`.
  - La classe `.selected` est strictement réservée au curseur actif lors de la navigation au clavier (`↑` / `↓`).

### Piège 13.7 : La Sélection par Défaut & Le Modèle de Validation d'Historique en Deux Temps (`Entrée` pour Surligner/Mémoriser, Clic Direct)
- **Symptôme** : Sélectionner arbitrairement un résultat dès la frappe ou mémoriser passivement chaque caractère lors du live search polluait l'historique avec des fragments ou déclenchait des navigations involontaires dès le premier appui sur `Entrée`.
- **Règle ergonomique établie** :
  1. **Aucun résultat sélectionné par défaut** : À chaque exécution de recherche (`executeSearch`), `searchSelectedIndex` est initialisé à `-1`. Aucun élément ne porte la classe `.selected` par défaut.
  2. **Validation progressive au clavier (modèle 2 temps)** :
     - Lorsque l'utilisateur tape sa requête, l'historique n'est pas pollué en tâche de fond.
     - Un premier appui sur `Entrée` (quand `searchSelectedIndex === -1`) sélectionne le **premier résultat**, le met en évidence (`.selected`), le fait défiler dans la vue, et **mémorise la requête dans l'historique**. La modale reste ouverte pour vérification.
     - Un second appui sur `Entrée` valide et ouvre le résultat sélectionné.
  3. **Clic direct à la souris** : Si l'utilisateur clique directement sur un résultat sans avoir appuyé sur `Entrée`, la requête active est automatiquement mémorisée dans l'historique avant de charger le document.

### Piège 13.8 : La Hiérarchie Visuelle de l'Accueil IA (`Prompts` vs `Recent Searches`)
- **Symptôme** : En mode IA avec un historique présent, les recherches récentes se retrouvaient affichées au-dessus des suggestions de requêtes en langage naturel, masquant l'accès rapide aux modèles de prompts techniques.
- **Solution** :
  - Inversion de l'ordre structurel dans `index.html` : `#modal-search-prompts` est positionné en première section, immédiatement suivi de `#modal-recent-searches`.
  - Chacun des deux blocs s'ajuste harmonieusement en flexbox (`flex: 1; overflow-y: auto`), offrant les requêtes d'inspiration en haut et l'historique de travail en bas.

### Piège 13.9 : La Persistance Indésirable de Surlignage du Dernier Élément Cliqué
- **Symptôme** : Après avoir cliqué sur un résultat de recherche, lors de la réouverture ou du parcours de la liste, le dernier élément cliqué restait perpétuellement surligné avec un fond bleu (`var(--primary-light)`) et une bordure latérale (`border-left: 3px solid var(--primary)`).
- **Cause racine** :
  1. Lors du clic, `selectSearchResult` affectait `searchSelectedIndex = options.index;`, et la boucle de rendu appliquait `.search-result-item.current-result` avec des styles forçant le fond de sélection (`!important`).
  2. En outre, `currentEl.scrollIntoView()` recentrait automatiquement la vue sur l'élément cliqué au lieu de laisser la liste propre en position initiale.
- **Solution** :
  - Dans `selectSearchResult` : `searchSelectedIndex` est systématiquement remis à `-1`.
  - Dans `css/style.css` : Suppression du background et de la bordure sur `.search-result-item.current-result`. Seule la coche SVG discrète (`.viewed`) atteste qu'un élément a déjà été consulté au cours de la session.
  - La mise en évidence bleue/sélectionnée est strictement réservée au curseur actif du clavier (`↑` / `↓` ou premier `Entrée`).

### Piège 13.10 : Disparition de l'Historique en Mode IA
- **Symptôme** : Lors du passage en mode IA, la section d'historique disparaissait complètement.
- **Cause racine** :
  1. Si l'historique était vide, `renderRecentSearches` basculait `modalRecentSearches.style.display = 'none'`, ce qui faisait disparaître l'ensemble de la section et ne laissait que les prompts sans aucun indicateur d'historique.
  2. Lors de la saisie d'une question IA, l'exécution sémantique étant asynchrone (~1-2s), `items.length` valait 0 au moment où l'utilisateur appuyait sur `Entrée`. La condition `if (items.length > 0)` sautait silencieusement et `saveRecentSearch` n'était jamais appelée !
  3. De plus, les 15 suggestions de prompts en `flex: 1` sans `max-height` écrasaient visuellement la zone inférieure.
- **Solution** :
  - En mode IA, la section d'historique reste toujours visible sous les prompts. Si l'historique est vide, un état neutre et épuré s'affiche (`"Aucune recherche récente. Vos requêtes s'afficheront ici."`).
  - L'appui sur `Entrée` valide et mémorise immédiatement la requête (`saveRecentSearch(val, 'ai')`), déclenchant la recherche sémantique sans attendre.
  - `.modal-search-prompts` est équilibré avec `max-height: 420px; min-height: 180px; flex: 1 1 auto;`, offrant un espace généreux et confortable pour afficher plusieurs rangées de suggestions de requêtes sans écraser la section d'historique en dessous.








