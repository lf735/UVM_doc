# UVM Documentation Site

Site de documentation statique pour **UVM (Universal Verification Methodology)**, prêt pour un déploiement continu sur **GitHub Pages**.

## 🚀 Fonctionnalités du site

- **Design moderne & responsive** : Interface claire et ergonomique sur desktop et mobile.
- **Mode Sombre / Clair** : Basculement automatique avec sauvegarde des préférences locales (`localStorage`).
- **Filtrage / Recherche instantanée** : Champ de recherche en direct dans la barre latérale.
- **Snippets de code SystemVerilog** : Blocs préformatés avec bouton de copie en un clic.
- **Déploiement GitHub Actions** : Workflow automatisé prêt à l'emploi (`.github/workflows/deploy.yml`).

---

## 📁 Structure du projet

```text
UVM_doc/
├── .github/
│   └── workflows/
│       └── deploy.yml      # Workflow GitHub Actions pour le déploiement sur Pages
├── css/
│   └── style.css           # Feuilles de style (variables CSS, thèmes, mise en page)
├── js/
│   └── main.js             # Interactions (mode nuit, menu mobile, recherche, copie)
├── index.html              # Page principale de documentation
├── .gitignore              # Fichiers à ignorer par git
└── README.md               # Documentation du dépôt
```

---

## 💻 Visualisation en local

Vous pouvez prévisualiser le site immédiatement de deux manières :

### Option 1 : Serveur local Python (recommandé)
```bash
python -m http.server 8000
```
Puis ouvrez votre navigateur sur [http://localhost:8000](http://localhost:8000).

### Option 2 : Ouverture directe
Ouvrez directement le fichier `index.html` dans n'importe quel navigateur web.

---

## 🌐 Déploiement sur GitHub Pages

1. **Liez votre dépôt distant sur GitHub** :
   ```bash
   git remote add origin https://github.com/<votre-utilisateur>/<nom-du-repo>.git
   git push -u origin main
   ```

2. **Activez GitHub Pages dans les paramètres du dépôt GitHub** :
   - Rendez-vous sur votre dépôt GitHub : **Settings** > **Pages**.
   - Sous **Build and deployment** > **Source**, choisissez **GitHub Actions**.
   - À chaque `git push` sur la branche `main`, le workflow déploiera automatiquement le site.
