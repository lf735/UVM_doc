# Interactive Execution Progression (Visual Flow Stepper)
## Guide Utilisateur et Spécifications Pédagogiques

---

### 1. Présentation Générale

L'**Interactive Execution Progression** (ou **Visual Flow Stepper**) est un simulateur pédagogique pas-à-pas intégré aux exemples UVM 1.2 du site documentaire.

Contrairement à la lecture statique de code SystemVerilog ou à l'inspection d'un journal de simulation brut (*simulation log*), le Visual Flow Stepper permet de **visualiser le déroulement dynamique d'une simulation UVM**, étape par étape, avec une synchronisation visuelle immédiate entre :
1. **L'étape temporelle et le descriptif conceptuel** (Timeline & Step Cards).
2. **La topologie active des composants UVM** (Glow lumineux et badge de rôle).
3. **Le fichier source et la ligne exacte exécutée** (Code Studio).
4. **La ligne correspondante dans le log de simulation** (Console interactive).

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
- La console de simulation (en bas de page) affiche les logs réels formatés avec la coloration syntaxique UVM (`UVM_INFO`, `UVM_WARNING`, `UVM_ERROR`, `UVM_FATAL`).
- Lors du passage d'une étape, la console repère la ligne de journal associée et la fait défiler au centre de l'affichage avec un effet de surbrillance temporaire.

---

### 3. Les 5 Exemples Majeurs Équipés (Pillar Examples)

Le Stepper est déployé sur les 5 concepts clés fondamentaux de la méthodologie UVM :

| Exemple | Emplacement | Nombre d'étapes | Concepts clés illustrés |
| :--- | :--- | :---: | :--- |
| **Phasing Lifecycle** | `examples_view/phasing/basic.html` | 12 | Déroulement séquentiel des 12 phases UVM (`build`, `connect`, `end_of_elaboration`, `start_of_simulation`, `run_phase`, `extract`, `check`, `report`, `final`), ordre top-down vs bottom-up. |
| **Objections & Drain Time** | `examples_view/phasing/objections.html` | 7 | Mécanisme `raise_objection` et `drop_objection`, calcul du zéro objection (`all_dropped`), application du `set_drain_time()`, terminaison propre du test. |
| **TLM-1 FIFO Communication** | `examples_view/tlm-1/fifo.html` | 6 | Ports et exports TLM-1, opération `put()` bloquante du producteur, mise en attente dans `uvm_tlm_fifo`, opération `get()` du consommateur. |
| **TLM-2 4-Phase Non-Blocking** | `examples_view/tlm-2/nonblocking_simple.html` | 8 | Protocole de transport non-bloquant TLM-2 (`nb_transport_fw` / `nb_transport_bw`), phases `BEGIN_REQ`, `END_REQ`, `BEGIN_RESP`, `END_RESP` et synchronisation temporelle. |
| **Register Primer & Adapter** | `examples_view/registers/primer.html` | 8 | Abstraction RAL (`uvm_reg_block`), appel `write()` / `read()`, adaptateur `reg2bus` et `bus2reg`, mise à jour du miroir matériel (`desired` vs `mirrored`). |

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

#### Mode Split View (Vue Côte à Côte avec les Sources UVM)
- Chaque studio d'exemple dispose d'un bouton **`Split with UVM Source`** dans son en-tête.
- Un clic divise automatiquement l'écran : le volet gauche affiche l'exemple et le volet droit charge le code source officiel UVM 1.2 correspondant (ex: `uvm_reg_block.svh`, `uvm_objection.svh`, `uvm_tlm_fifo.svh`), positionné à la ligne exacte de la définition de classe.

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

