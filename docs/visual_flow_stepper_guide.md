# Interactive Execution Progression (Visual Flow Stepper)
## Guide Utilisateur et Spécifications Pédagogiques

---

### 1. Présentation Générale

Le **Test Scenario Walkthrough** (anciennement *Visual Flow Stepper*) est un simulateur pédagogique pas-à-pas situé en fin de page des exemples majeurs UVM 1.2 du site documentaire.

Contrairement à la lecture statique de code SystemVerilog ou à l'inspection d'un journal de simulation brut (*simulation log*), il permet de **visualiser l'intention réelle et l'état dynamique du test**, étape par étape, grâce à des **animations visuelles conceptuelles dédiées** et une synchronisation bidirectionnelle entre :
1. **La carte d'étape & l'animation visuelle** (Timeline, badge d'état dynamique `.scenario-state-pill` et schémas animés en direct).
2. **La topologie active des composants UVM** (Glow lumineux et badge de rôle).
3. **Le fichier source et la ligne exacte exécutée** (Code Studio + bouton `Jump to Code`).
4. **La ligne correspondante dans le log de simulation** (Console interactive + surbrillance `.term-line-highlight` + bouton `Jump to Terminal Log`).

---

### 2. Les 4 Vues Synchronisées en Temps Réel

À chaque changement d'étape (manuellement ou en mode *Lecture automatique*), 4 composants de l'interface se mettent à jour simultanément :

```
+------------------------------------------------------------------------------------+
|  1. Timeline & Stepper Cards (Étape N / Total, description didactique, badges)      |
+------------------------------------------------------------------------------------+
|  2. Topology Viewer (UVM Component Tree avec halo bleu/vert sur le composant actif)|
+-----------------------------------------+------------------------------------------+
|  3. Code Studio (Onglet + Ligne active) |  4. Terminal Simulator (Trace UVM_INFO)  |
|  - Basculement automatique d'onglet     |  - Défilement automatique vers le        |
|  - Focus et surbrillance de la ligne    |    message exact généré à cette étape    |
|  - Défilement interne SANS saut d'écran |  - Filtres Questa / VCS / Xcelium        |
+-----------------------------------------+------------------------------------------+
```

#### A. Timeline & Cartes d'Étapes
- Située en haut du studio interactif, elle présente le fil directeur de l'exécution.
- Chaque étape affiche son numéro (ex: `1/7`), son titre, le composant émetteur, et une explication claire du mécanisme UVM sous-jacent.
- Vous pouvez cliquer directement sur n'importe quelle puce d'étape pour naviguer instantanément.

#### B. Diagramme de Topologie Dynamique (Topology Tree)
- Met en évidence visuelle le composant UVM actuellement en train d'exécuter l'action (ex: `uvm_test_top.env.agent.driver`).
- Un contour phosphorescent animé attire l'œil sur l'instance active dans la hiérarchie.

#### C. Code Studio avec Navigation et Auto-Scroll Isolé
- Si l'étape courante concerne un fichier différent (ex: passage du `driver` au `scoreboard` ou de la `sequence` au `reg_block`), le Code Studio **active automatiquement le bon onglet de fichier**.
- La ligne de code SystemVerilog exécutée est surlignée avec une puce indicatrice bleue (`line-stepper-active`).
- **Défilement isolé** : Le conteneur de code défile en douceur (*smooth internal scroll*) pour centrer la ligne, **sans jamais faire sauter la page principale de votre navigateur**.

#### D. Console de Simulation Synchronisée
- La console de simulation (juste au-dessus du Walkthrough) affiche les logs réels segmentés ligne par ligne (`.term-line`) avec coloration syntaxique UVM (`UVM_INFO`, `UVM_WARNING`, `UVM_ERROR`, `UVM_FATAL`).
- Lors du passage d'une étape, la console repère automatiquement la ligne de journal associée, la centre et lui applique une surbrillance persistante animée (`.term-line-highlight`).
- Les boutons **`Jump to Code`** et **`Jump to Terminal Log`** permettent d'aller immédiatement inspecter la ligne correspondante dans l'un ou l'autre des panneaux.

---

### 3. Les 5 Exemples Majeurs Équipés (Pillar Examples)

Le Test Scenario Walkthrough est déployé sur les 5 concepts clés fondamentaux de la méthodologie UVM, chacun doté de son animation interactive sur mesure :

| Exemple | Emplacement | Étapes | Animation Visuelle & Concepts Calibrés |
| :--- | :--- | :---: | :--- |
| **Phasing Lifecycle** | `examples_view/phasing/basic.html` | 5 | Arbre hiérarchique animé (`top` / `a1,a2` / `b1,d1`) illustrant en direct les phases descendantes (*Top-Down*, ex. `build_phase`) vs ascendantes (*Bottom-Up*, ex. `connect_phase`, `report_phase`). |
| **Objections & Drain Time** | `examples_view/phasing/objections.html` | 5 | Diagramme de Gantt temporel avec 4 threads concurrents et barre d'extension dynamique pour la fenêtre de `drain_time` (`#10` après `all_dropped`). |
| **TLM-1 FIFO Communication** | `examples_view/tlm-1/fifo.html` | 5 | Jauge FIFO à 10 emplacements avec indicateurs `Producer`/`Consumer`, saturation (`10/10 [BLOCKED]`) et déblocage sur `get()`. |
| **TLM-2 4-Phase Non-Blocking** | `examples_view/tlm-2/nonblocking_simple.html` | 4 | Navette bidirectionnelle (`Initiator` ↔ `Device`) montrant les transitions `BEGIN_REQ`, `END_REQ`, `BEGIN_RESP` et `END_RESP` sur `nb_transport_fw` / `bw`. |
| **Register Primer & Adapter** | `examples_view/registers/primer.html` | 4 | Pipeline RAL temps réel : `Sequence (write/read)` → `Adapter (reg2bus)` → `APB Bus` → `DUT Memory` → `RAL Mirror` (`desired` vs `mirrored`). |

---

### 4. Guide des Commandes et de Navigation

#### Commandes du Stepper
- **Bouton `◀ Précédent`** : Revient à l'étape précédente.
- **Bouton `Lecture / Pause ▶` (Autoplay)** : Lance la progression automatique avec un intervalle régulier (2,5 secondes). Cliquez à nouveau pour mettre en pause.
- **Bouton `Suivant ▶`** : Avance à l'étape suivante.
- **Clic sur une pastille d'étape** : Saute directement à l'étape désirée.

#### Commandes des Onglets Multi-Fichiers (Code Studio)
Pour les projets contenant de nombreux fichiers (ex: `ubus` avec 26 fichiers, `vertical_reuse` avec 21 fichiers, `primer` avec 12 fichiers) :
- **Sélecteur déroulant rapide (`Select file...`)** : Situé à droite de la barre d'onglets, il liste l'intégralité des fichiers avec leur numéro d'index. Sélectionner un fichier ouvre immédiatement son code.
- **Boutons de défilement horizontal (`◀` et `▶`)** : Permettent de faire glisser la barre d'onglets vers la gauche ou vers la droite sans utiliser la molette.
- **Molette de souris** : Placer le curseur sur la barre d'onglets et utiliser la molette fait défiler les onglets horizontalement.

#### Accès Direct aux Sources et APIs UVM
- **Pastilles `Key UVM APIs`** : Chaque exemple affiche dans sa bannière les classes UVM principales (ex: `uvm_reg_block`, `uvm_objection`). Un clic ouvre le fichier source UVM correspondant dans le panneau de documentation / mode Split View.
- **Badge `Source Specification & Design Notes`** : Cliquer sur le badge `Source: <fichier>` en haut de la section d'architecture bascule automatiquement le Code Studio sur le fichier correspondant et fait défiler la vue vers `#doc-nav-studio`.
- **Positionnement pédagogique** : Le *Test Scenario Walkthrough* est placé en fin de page afin de permettre d'assimiler d'abord la spécification source, la topologie et le code avant de rejouer le scénario étape par étape.

---

### 5. Dépannage et Résolution des Problèmes Fréquents

> [!NOTE]
> **Pourquoi le défilement de ma page ne saute plus ?**
> Dans la version précédente, l'instruction `scrollIntoView()` faisait sauter l'ensemble de la page HTML du navigateur vers le code, masquant les contrôles de progression. Ce comportement a été corrigé : le défilement est désormais confiné à l'intérieur du conteneur `#studio-code-container`. La page reste stable et les boutons de navigation restent toujours visibles.

> [!TIP]
> **Comment retrouver un exemple depuis la recherche globale ou la recherche sémantique (RAG) ?**
> Tous les 39 exemples et leurs étapes de simulation sont indexés dans la base sémantique RAG (`rag_chunks.json` et embeddings vectoriels). Vous pouvez taper des requêtes comme :
> - *"How do objections control the phase drain time?"*
> - *"Show TLM-2 non-blocking 4-phase example"*
> - *"Ubus bus master driver implementation"*
> Les résultats proposeront directement l'ouverture de l'exemple en mode plein écran ou en Split View.

