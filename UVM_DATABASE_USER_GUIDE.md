# Guide Utilisateur & Manuel de Référence : Base de Données des Sources UVM 1.2

Bienvenue dans le guide d'utilisation de la **Base de Données et Explorateur des Sources UVM 1.2**.

Ce guide vous accompagne pour naviguer, interroger et exploiter la base de données extraite directement des sources de référence UVM 1.2 (`uvm-1.2/src`), que ce soit en ligne de commande (CLI), via l'interface web interactive ou par requêtes SQL.

---

## 1. Vue d'Ensemble des Outils et Fichiers

| Fichier | Format | Rôle & Usage |
| :--- | :--- | :--- |
| **[uvm_database_explorer.html](file:///c:/Dev/UVM_doc/uvm_database_explorer.html)** | HTML / SPA | **Explorateur Web interactif autonome** : navigation dans l'arbre d'héritage, matrice des méthodes redéfinies, dictionnaire de macros et liaisons DPI. Double-cliquable sous `file://`. |
| **[scripts/query_uvm_db.py](file:///c:/Dev/UVM_doc/scripts/query_uvm_db.py)** | Script Python | **Outil CLI d'interrogation du terminal** : recherche instantanée de classes, méthodes, redéfinitions, macros, fichiers et liaisons DPI. |
| **[scripts/build_uvm_source_db.py](file:///c:/Dev/UVM_doc/scripts/build_uvm_source_db.py)** | Script Python | **Générateur / Parseur de la base** : analyse les 155 sources et reconstruit l'ensemble des bases de données JSON, SQLite et JS. |
| **[data/uvm_source_database.json](file:///c:/Dev/UVM_doc/data/uvm_source_database.json)** | JSON (5.55 Mo) | **Base de données principale** : hiérarchique, bidirectionnelle et indexée, idéale pour l'intégration dans des scripts Python/JS ou des pipelines RAG. |
| **[data/uvm_source_database.sqlite](file:///c:/Dev/UVM_doc/data/uvm_source_database.sqlite)** | SQLite (2.11 Mo) | **Base relationnelle normalisée** : idéale pour les requêtes SQL analytiques, les jointures complexes et les audits de code. |
| **[data/uvm_source_database.js](file:///c:/Dev/UVM_doc/data/uvm_source_database.js)** | JS (5.59 Mo) | **Bundle JavaScript** pour l'exécution locale 100% hors-ligne dans un navigateur web sans contrainte CORS. |
| **[data/uvm_dpi_database.json](file:///c:/Dev/UVM_doc/data/uvm_dpi_database.json)** | JSON (24 Ko) | **Sous-base DPI** reliant chaque import SystemVerilog aux implémentations C des simulateurs (Questa, VCS, Incisive). |

---

## 2. Guide de l'Outil CLI (`scripts/query_uvm_db.py`)

L'outil CLI permet d'inspecter les sources directement depuis votre terminal sans ouvrir de navigateur. Il s'exécute avec Python 3 (`py -3` ou `python3`).

### 2.1 Synthèse Générale : `stats`
Affiche le tableau de bord métrique de la bibliothèque UVM 1.2 :
```powershell
py -3 scripts/query_uvm_db.py stats
```
*Exemple de résultat :*
```
=================================================================
  UVM 1.2 Source Code Database Statistics
=================================================================
Total Source Files      : 155 (145 SV/SVH, 10 C/DPI)
Total Classes Indexed   : 325
Total Macros Indexed    : 373 (excluding include guards)
Total Class Methods     : 2130
Total Method Overrides  : 507
Total Indexed Symbols   : 2828
DPI SV Imports          : 15
DPI C/C++ Functions     : 62
-----------------------------------------------------------------
Files by Subsystem:
  - base        :  47 files
  - reg         :  26 files
  - comps       :  14 files
  - dpi         :  13 files
  ...
```

---

### 2.2 Fiche Complète d'une Classe : `class <NomClasse>`
Affiche le fichier, les lignes exactes de déclaration, la chaîne d'héritage, le résumé de documentation, ainsi que la séparation stricte entre **méthodes définies dans la classe** et **méthodes redéfinies (*overridden*)** :
```powershell
py -3 scripts/query_uvm_db.py class uvm_driver
```
*Exemple de résultat :*
```
======================================================================
CLASS: uvm_driver
======================================================================
Location    : comps/uvm_driver.svh (Lines 44 - 87)
Parameters  : #(type REQ=uvm_sequence_item, type RSP=REQ)
Extends     : uvm_component
Depth       : 4
Ancestors   : uvm_component -> uvm_report_object -> uvm_object -> uvm_void
Direct Child: None (Leaf class)

Description:
  The base class for drivers that initiate requests for new transactions via a uvm_seq_item_pull_port.

--- Methods Defined in uvm_driver (0) ---

--- Methods Overridden from Ancestors (2) ---
  function virtual string get_type_name()  (overrides uvm_object) [inline]
  function void new(string name, uvm_component parent)  (overrides uvm_component) [inline]
======================================================================
```

---

### 2.3 Arbre Visuel d'Héritage : `hierarchy <NomClasse>`
Affiche l'arbre généalogique ascendant (parents) et descendant (enfants) avec indentation :
```powershell
py -3 scripts/query_uvm_db.py hierarchy uvm_component
```
*Exemple de résultat :*
```
--- Ascendance (Parents) ---
▲ uvm_void
  ▲ uvm_object
    ▲ uvm_report_object
      ● uvm_component (Current Class, Depth 3)

--- Descendance (Children) ---
  ▼ uvm_agent
  ▼ uvm_algorithmic_comparator
  ▼ uvm_driver
  ▼ uvm_env
  ▼ uvm_in_order_comparator
  ▼ uvm_monitor
  ▼ uvm_push_driver
  ▼ uvm_root
  ▼ uvm_scoreboard
  ▼ uvm_sequencer_base
  ▼ uvm_subscriber
  ▼ uvm_test
  ▼ uvm_tlm_fifo_base
```

---

### 2.4 Matrice Inverse des Redéfinitions : `overrides <NomMethode>`
Permet de répondre immédiatement à la question : *"Quelles sont toutes les classes qui redéfinissent cette méthode ?"* :
```powershell
py -3 scripts/query_uvm_db.py overrides build_phase
```
*Exemple de résultat :*
```
======================================================================
Method Override Analysis for: 'build_phase'
======================================================================
Originally Introduced in:
  - uvm_component  (base/uvm_component.svh#L211)

Overridden in 6 Derived Classes:
  - uvm_agent                      (overridden from uvm_component       ) at comps/uvm_agent.svh#L58
  - uvm_port_component_base        (overridden from uvm_component       ) at base/uvm_port_base.svh#L90
  - uvm_root                       (overridden from uvm_component       ) at base/uvm_root.svh#L228
  - uvm_sequencer_base             (overridden from uvm_component       ) at seq/uvm_sequencer_base.svh#L404
  - uvm_sequencer_param_base       (overridden from uvm_sequencer_base  ) at seq/uvm_sequencer_param_base.svh#L258
  - uvm_tlm_fifo_base              (overridden from uvm_component       ) at tlm1/uvm_tlm_fifo_base.svh#L166
======================================================================
```

---

### 2.5 Détail d'une Macro : `macro <NomMacro>`
Affiche le fichier, les lignes exactes, la catégorie, les arguments, la documentation et le code nettoyé de la macro :
```powershell
py -3 scripts/query_uvm_db.py macro uvm_info
```

---

### 2.6 Cartographie DPI : `dpi`
Affiche tous les `import "DPI-C"` SystemVerilog avec les fonctions C d'implémentation associées pour chaque simulateur :
```powershell
py -3 scripts/query_uvm_db.py dpi
```

---

### 2.7 Recherche Plein Texte : `search <Texte>`
Recherche instantanément dans les 2 828 symboles de la bibliothèque :
```powershell
py -3 scripts/query_uvm_db.py search objection
```

---

## 3. Guide de l'Explorateur Web (`uvm_database_explorer.html`)

L'application [uvm_database_explorer.html](file:///c:/Dev/UVM_doc/uvm_database_explorer.html) est une interface Web Single Page Application (SPA) moderne et autonome conçue selon les directives Material Design / Google Developers.

### 3.1 Comment l'Ouvrir ?
1. **Mode Local Direct (`file://`)** :
   Double-cliquez simplement sur [uvm_database_explorer.html](file:///c:/Dev/UVM_doc/uvm_database_explorer.html) dans l'explorateur Windows ou ouvrez-le dans Chrome, Edge ou Opera. Grâce au bundle synchrone `data/uvm_source_database.js`, aucune restriction CORS ne bloque le chargement.
2. **Mode Serveur Web Local (`http://`)** :
   Si vous disposez d'un serveur local :
   ```powershell
   py -3 -m http.server 8000
   ```
   Puis rendez-vous sur `http://localhost:8000/uvm_database_explorer.html`.

---

### 3.2 Les 5 Onglets d'Exploration

#### 🏛 1. Classes & Hierarchy (Arborescence & Méthodes)
- **Volet Gauche (Tree View)** :
  - Arborescence pliable de toutes les 325 classes UVM, organisée par racine d'héritage (`uvm_void`, `uvm_comparer`, `uvm_factory`...).
  - Boutons **Expand** et **Collapse** pour déplier ou replier d'un clic tout l'arbre.
  - Champ de filtre rapide (raccourci clavier <kbd>/</kbd>) pour filtrer les classes en temps réel.
  - Badges numériques indiquant le nombre total de méthodes de chaque classe.
- **Volet Droit (Inspecteur de Classe)** :
  - Titre avec badge `class` ou `virtual class` et badge `Deprecated` le cas échéant.
  - Liens directs cliquables vers le fichier source exact dans `src_view` (ex. `comps/uvm_driver.svh#L44-L87`).
  - Fil d'Ariane de la chaîne d'héritage (chaque classe ancêtre est cliquable).
  - Liste des sous-classes directes cliquables.
  - Bloc de description issu des commentaires *NaturalDocs*.
  - **Tableau des Méthodes avec 3 filtres** :
    - `All` : Toutes les méthodes de la classe.
    - `Defined` : Méthodes introduites directement par cette classe.
    - `Overridden` : Méthodes surchargées depuis un parent (avec badge vert `overrides <Parent>` et badge rouge `implements pure` si applicable).
  - Chaque méthode propose des liens distincts vers sa **déclaration interne** (`decl Lxx`) et son **implémentation externe** (`impl Lxx`).

#### 🔄 2. Method Overrides Matrix (Matrice des Redéfinitions)
- Moteur de recherche dédié aux méthodes surchargées.
- Tapez un nom de méthode (ex. `build_phase`, `run_phase`, `do_copy`, `get_type_name`, `create`).
- Une carte s'affiche pour chaque méthode présentant la classe d'introduction racine et la liste exhaustive des classes dérivées qui la surchargent avec leurs numéros de lignes sources.

#### ⚡ 3. Macro Catalog (Dictionnaire des Macros)
- Filtrage par pilules de catégories : `Reporting`, `Object Utils`, `Field Automation`, `Sequence`, `TLM`, `Callbacks`, `Reg`, `Version`, `Deprecated`, `Misc`.
- Recherche en temps réel par mot-clé.
- Carte détaillée avec arguments, position, documentation et extrait de code.

#### 📁 4. Files & Includes (Fichiers & Graphe d'Inclusion)
- Tableau des 155 fichiers avec métriques de lignes (code, commentaires, lignes blanches).
- Graphe des inclusions : nombre de fichiers inclus (`includes out`) et nombre de fichiers qui incluent ce fichier (`included in`).
- Liste des classes et macros déclarées dans chaque fichier.

#### 🔌 5. DPI-C Interfaces (Catalogue DPI)
- Vue comparative présentant chaque `import "DPI-C"` SystemVerilog en regard de ses implémentations C pour Questa, VCS et Incisive.

---

## 4. Livre de Recettes SQL (*SQL Cookbook*)

La base [data/uvm_source_database.sqlite](file:///c:/Dev/UVM_doc/data/uvm_source_database.sqlite) peut être interrogée via n'importe quel client SQLite (DBeaver, DB Browser for SQLite, extension VS Code SQLite, ou script Python).

### 4.1 Connexion Rapide en Python
```python
import sqlite3

conn = sqlite3.connect("data/uvm_source_database.sqlite")
cur = conn.cursor()
```

---

### 4.2 Recettes de Requêtes Utiles

#### 🔹 Recette 1 : Trouver toutes les classes dérivant directement ou indirectement de `uvm_component`
```sql
SELECT name, file, depth, parent 
FROM classes 
WHERE ancestors_json LIKE '%"uvm_component"%' 
ORDER BY depth, name;
```

#### 🔹 Recette 2 : Trouver toutes les classes qui redéfinissent `run_phase`
```sql
SELECT 
    cm.class_name, 
    cm.overridden_from, 
    cm.decl_file, 
    cm.decl_start_line, 
    cm.impl_start_line,
    cm.calls_super
FROM class_methods cm
WHERE cm.name = 'run_phase' AND cm.overrides = 1
ORDER BY cm.class_name;
```

#### 🔹 Recette 3 : Trouver les 10 classes ayant le plus de méthodes redéfinies
```sql
SELECT 
    class_name, 
    COUNT(*) AS override_count
FROM class_methods
WHERE overrides = 1
GROUP BY class_name
ORDER BY override_count DESC
LIMIT 10;
```

#### 🔹 Recette 4 : Lister toutes les méthodes `pure virtual` et vérifier qui les implémente
```sql
-- 1. Déclarations pure virtual
SELECT class_name, name, return_type, decl_file, decl_start_line
FROM class_methods
WHERE is_pure_virtual = 1;

-- 2. Classes implémentant ces contrats
SELECT 
    mo.method_name, 
    mo.ancestor_class AS interface_class, 
    mo.child_class AS implementing_class,
    mo.decl_file,
    mo.decl_line
FROM method_overrides mo
JOIN class_methods cm 
  ON cm.class_name = mo.ancestor_class 
 AND cm.name = mo.method_name
WHERE cm.is_pure_virtual = 1
ORDER BY mo.method_name, mo.child_class;
```

#### 🔹 Recette 5 : Rechercher les macros de Reporting avec leurs arguments
```sql
SELECT name, parameters_raw, file, start_line, doc_summary 
FROM macros 
WHERE category = 'reporting' 
ORDER BY name;
```

#### 🔹 Recette 6 : Analyser les ratios Code / Commentaires par sous-système
```sql
SELECT 
    subsystem,
    COUNT(*) AS total_files,
    SUM(lines_code) AS total_code_lines,
    SUM(lines_comment) AS total_comment_lines,
    ROUND(CAST(SUM(lines_comment) AS FLOAT) / SUM(lines_total) * 100, 1) AS comment_percentage
FROM files
GROUP BY subsystem
ORDER BY total_code_lines DESC;
```

---

## 5. Guide de Régénération de la Base

Si vous modifiez ou patchez les fichiers sources UVM dans `uvm-1.2/src`, vous pouvez régénérer l'ensemble des bases de données en une seule commande :

```powershell
py -3 scripts/build_uvm_source_db.py
```

### Que fait ce script ?
1. Parcourt les 155 fichiers sources.
2. Détecte et exclut les gardes anti-double inclusion.
3. Extrait les classes, méthodes, paramètres, modificateurs et commentaires.
4. Rapproche les implémentations hors-classe (`ClassName::MethodName`).
5. Résout l'arbre généalogique complet et calcule la matrice des redéfinitions.
6. Associe le code C DPI aux imports SystemVerilog.
7. Écrit automatiquement :
   - `data/uvm_source_database.json`
   - `data/uvm_source_database.sqlite`
   - `data/uvm_source_database.js`
   - `data/uvm_dpi_database.json`
8. Affiche un rapport complet de synthèse dans la console.

