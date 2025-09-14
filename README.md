# Content Idea Hub

Content Idea Hub est une application web permettant de centraliser, organiser et gérer vos idées de contenu (posts, vidéos, articles, etc.). Elle est conçue pour les créateurs, équipes marketing, et toute personne souhaitant structurer sa créativité.

---

## Fonctionnalités

- **Authentification** : Inscription, connexion, gestion sécurisée des sessions.
- **Tableau de bord** : Liste paginée de vos idées, triées par date.
- **Recherche & Filtres** : Filtre par tags pour retrouver rapidement vos idées.
- **Gestion des idées** : Ajout, modification, suppression d’idées.
- **Import/Export CSV** : Importez ou exportez vos idées au format CSV.
- **Design responsive** : Interface moderne et adaptée à tous les écrans grâce à Tailwind CSS.
- **Feedback utilisateur** : Messages flash pour les actions importantes (succès, erreurs).

---

## Installation

### Prérequis

- Python 3.10+
- Node.js & npm (pour Tailwind CSS)
- Un environnement virtuel Python recommandé

### 1. Cloner le projet

```bash
git clone https://github.com/votre-utilisateur/content-idea-hub.git
cd content-idea-hub
```

### 2. Installer les dépendances Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Installer Tailwind CSS

```bash
npm install -D tailwindcss
```

### 4. Générer le CSS Tailwind

```bash
npx tailwindcss -i app/static/css/tailwind.css -o app/static/css/output.css
```

### 5. Initialiser la base de données

```bash
flask db upgrade
```

*(ou utilisez la commande adaptée à votre gestionnaire de migrations)*

### 6. Lancer l’application

```bash
python run.py
```

---

## Structure du projet

```
content-idea-hub/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes.py
│   ├── static/
│   │   └── css/
│   │       ├── tailwind.css
│   │       └── output.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── idea_form.html
│       ├── login.html
│       ├── register.html
│       └── import.html
|       
├── run.py
└── requirements.txt
```

---

## Personnalisation

- **Design** : Modifiez `tailwind.css` et régénérez `output.css` pour adapter le style.
- **Templates** : Personnalisez les fichiers HTML dans `app/templates/`.
- **Fonctionnalités** : Ajoutez des champs, statuts ou fonctionnalités dans `models.py` et `forms.py`.

---

## Sécurité

- Authentification via Flask-Login.
- Vérification des droits sur chaque action (édition/suppression).
- Protection CSRF sur les formulaires.

---

## Contribution

Les contributions sont les bienvenues !  
Ouvrez une issue ou proposez une pull request pour toute amélioration ou correction.

---

## Licence

MIT

---

## Auteur

Développé par Ibrahima thiongane
