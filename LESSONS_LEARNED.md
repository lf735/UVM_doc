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


