# Guide Utilisateur : Recherche Sémantique & Langage Naturel UVM 1.2

Bienvenue dans le guide d'utilisation de la **Recherche en Langage Naturel & IA Locale** du portail documentaire UVM 1.2.

Cette fonctionnalité vous permet de formuler vos questions comme vous les poseriez à un expert UVM, de rechercher par concepts ou par cas d'usage réels, plutôt que de devoir connaître par cœur le nom exact d'une classe ou d'une méthode.

---

## 1. Pourquoi utiliser la recherche en langage naturel ?

| Recherche Classique (Symbolique) | Recherche Sémantique IA (✨) |
| :--- | :--- |
| Conçue pour chercher des noms exacts : `uvm_driver`, `set_drain_time`, `UVM_MEDIUM`. | Conçue pour comprendre vos intentions et questions d'ingénierie. |
| Échoue si vous ne connaissez pas le nom technique IEEE de la classe. | Fait le lien avec le vocabulaire réel du terrain (`vif`, `virtual interface`, `broadcast`, `end of test`). |
| Ne comprend pas les questions conceptuelles. | Extrait directement les phrases explicatives les plus pertinentes. |

---

## 2. Comment activer la recherche IA ?

1. Ouvrez la barre de recherche globale en appuyant sur la touche <kbd>/</kbd> ou le raccourci <kbd>Ctrl</kbd> + <kbd>K</kbd> (ou <kbd>Cmd</kbd> + <kbd>K</kbd> sur Mac).
2. Cliquez sur l'icône violette **✨ (Mode IA)** ou utilisez le raccourci clavier <kbd>Alt</kbd> + <kbd>N</kbd>.

### 🛡️ Boîte de dialogue de premier lancement
Lors de votre toute première utilisation, une fenêtre d'information s'affiche pour vous présenter le fonctionnement :
- **100% Privé & Local** : Aucun mot-clé, aucune question ni aucun code n'est envoyé sur Internet. Le modèle d'IA s'exécute directement dans votre navigateur web (via WebAssembly et ONNX Runtime).
- **Téléchargement unique** : Le modèle (~23 Mo) n'est téléchargé qu'une seule fois et reste en mémoire cache locale pour vos visites suivantes.
- **Choix du modèle** : Vous pouvez choisir parmi 3 modèles optimisés (notés de 1 à 5 étoiles sur la vitesse, la précision et la légèreté). Le modèle recommandé par défaut est **MiniLM-L6**.
- Cliquez sur **Activer la recherche IA** pour commencer.

---

## 3. Comment formuler vos questions ?

Vous pouvez saisir des questions complètes en anglais technique ou en français.

### Exemples de questions types par domaine :

#### 🔹 Configuration & Interfaces Virtuelles (VIF)
- *"how to pass a virtual interface using uvm_config_db"*
- *"how to retrieve config db parameters in build phase"*
- *"difference between uvm_config_db and uvm_resource_db"*

#### 🔹 Objections & Fin de Simulation
- *"how do objections work and how to control simulation end"*
- *"how to set drain time before dropping objection"*
- *"how to prevent phase from ending prematurely"*

#### 🔹 Factory & Overrides
- *"difference between create and new in factory"*
- *"how to override a component type using factory"*
- *"how to substitute transaction with extended class"*

#### 🔹 Synchronisation & Séquences
- *"how to synchronize sequences with a barrier"*
- *"how to trigger and wait for uvm_event"*
- *"how to start virtual sequence on multiple sequencers"*

#### 🔹 Ports TLM & Scoreboard
- *"how to connect monitor to scoreboard with analysis port"*
- *"how to broadcast transactions to multiple subscribers"*
- *"difference between put, get and transport ports"*

#### 🔹 RAL (Register Abstraction Layer)
- *"how does reg2bus adapter work"*
- *"difference between frontdoor and backdoor register access"*
- *"how to predict register value from bus monitor"*

#### 🔹 Options de Ligne de Commande & Tests
- *"how to run a specific test with +UVM_TESTNAME"*
- *"how to increase verbosity with +UVM_VERBOSITY"*

> [!TIP]
> **Suggestions rapides (*Prompt Chips*)** : Lorsque la barre de recherche est vide en mode IA, une série de 15 questions fréquentes s'affiche sous forme de pastilles cliquables. Cliquez sur l'une d'elles pour lancer instantanément la recherche correspondante.

---

## 4. Comprendre les Résultats

Chaque résultat de recherche est structuré pour vous faire gagner un temps précieux :

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Base > uvm_config_db   [🎯 Section: set]              [92% match] [class]│
│                                                                        │
│ uvm_config_db                                                          │
│                                                                        │
│ Create a new or update an existing configuration setting for field_name│
│ in inst_name from cntxt... Settings from hierarchically higher levels  │
│ have higher precedence.                                                │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Fil d'Ariane & Classe Parent** : Indique la catégorie (`Base`, `Comps`, `Seq`, `TLM1`, `Reg`...) et la classe principale.
2. **Badge de Section Ciblée (`🎯 Section: ...`)** : Vous indique immédiatement quelle méthode, tâche ou sous-section de la page répond précisément à votre question (ex: `🎯 Section: set`).
3. **Pourcentage de Match (`% match`)** :
   - 🟢 **$\ge 80\%$** : Forte corrélation sémantique directe.
   - 🟡 **$65\% - 79\%$** : Bonne pertinence contextuelle.
   - ⚪ **$< 65\%$** : Référence connexe ou d'arrière-plan.
4. **Smart Snippet (Extrait Intelligent)** : Extrait automatiquement les 1 à 2 phrases du document qui répondent à votre question, avec surbrillance jaune des concepts clés.
5. **Navigation au Clic** :
   - Cliquer sur un résultat ouvre la page documentaire **directement positionnée sur la méthode ciblée**.
   - En mode **Split View**, le code source SystemVerilog correspondant s'ouvre simultanément à droite à la bonne ligne de code !

---

## 5. Personnalisation & Paramètres (`⚙️`)

En cliquant sur l'icône **⚙️ (Paramètres)** en haut à droite de la modale de recherche, vous pouvez adapter le comportement à vos préférences :

### Modèle d'Embedding Actif
- **MiniLM-L6 (Recommandé)** : 23 Mo, ultra-rapide, équilibre optimal entre vitesse et précision.
- **BGE-Small-EN (Haute Précision)** : 33 Mo, modèle BAAI offrant une fidélité maximale sur les nuances techniques de l'anglais.
- **BGE-Micro (Ultra-Léger)** : 14 Mo, consommation mémoire minimale (~35 Mo RAM).

### Options de Recherche
- **Recherche Hybride (activée par défaut)** : Combine la similarité vectorielle avec la correspondance exacte des mots-clés pour ne jamais rater un symbole précis.
- **Détection Automatique Sémantique** : Active automatiquement le mode IA si votre saisie contient au moins 3 mots et débute par une question (*"how to..."*, *"what is..."*, *"comment..."*).

### Format des Résultats IA
- **Option A : Consolidé par Document / Classe (Recommandé)** : Regroupe les réponses par composant avec badge ciblé vers la méthode (`🎯 Section: ...`). Empêche d'avoir plusieurs résultats pour une même page.
- **Option B : Liste Mixte Dé-dupliquée** : Affiche directement les méthodes individuelles, tout en garantissant qu'aucun document n'apparaît deux fois dans le Top 5.

### Gestion du Cache & Mémoire
- Indique l'espace disque consommé par le modèle dans votre navigateur.
- Bouton **Vider le cache IA** : Permet de supprimer en un clic les fichiers de modèles pour libérer de l'espace disque.

---

## 6. Foire Aux Questions (FAQ)

### Mes questions ou mon code sont-ils envoyés sur un serveur distant ?
**Absolument pas.** L'ensemble des calculs vectoriels (tokenisation, embedding ONNX, produit scalaire) s'exécute à 100% sur le processeur de votre machine au sein du navigateur web. Aucune donnée ne quitte votre ordinateur.

### Cela fonctionne-t-il hors-ligne ?
**Oui.** Après le téléchargement initial du modèle lors de votre première activation, tous les fichiers sont mis en cache persistant (`Cache API`). Le moteur fonctionne ensuite sans aucune connexion Internet.

### Le modèle consomme-t-il la mémoire vive de mon navigateur en permanence ?
**Non.** Le système dispose d'une gestion hygiénique de la RAM : le modèle est automatiquement déchargé de la mémoire vive dès la fermeture de la fenêtre de recherche ou après 3 minutes d'inactivité.

### Raccourcis clavier utiles
- <kbd>/</kbd> ou <kbd>Ctrl</kbd> + <kbd>K</kbd> : Ouvrir la recherche
- <kbd>Alt</kbd> + <kbd>N</kbd> : Basculer entre le mode Symboles et le mode IA
- <kbd>Flèches Haut / Bas</kbd> : Naviguer dans les résultats
- <kbd>Entrée</kbd> : Ouvrir le résultat sélectionné
- <kbd>Échap</kbd> : Fermer la recherche

