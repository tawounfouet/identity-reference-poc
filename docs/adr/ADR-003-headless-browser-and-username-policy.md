# ADR-003 - Headless navigateur, politique username et snapshot OpenAPI

- Date : 19 novembre 2026
- Statut : accepté et implémenté, PR #7 fusionnée et CI verte
- Dépendances : ADR-002, R1 §05, ROADMAP gate G0

## Décisions

1. `django-allauth` 65.22.1 avec `allauth.account`, `allauth.headless` et `allauth.socialaccount` (aucun provider OAuth activé).
2. `HEADLESS_ONLY=True` pour ne pas exposer les vues HTML traditionnelles. `accounts/` reste enregistré pour de futurs callbacks OAuth ; `_allauth/` sert les APIs.
3. `HEADLESS_CLIENTS=("browser",)` uniquement. Le navigateur utilisera les sessions Django côté serveur. Pas de JWT ni de CORS cross-origin activé dans ce ticket.
4. `ACCOUNT_LOGIN_METHODS={"username"}` et `ACCOUNT_SIGNUP_ENABLED=False`. Aucun mécanisme email-only sur `AbstractUser.email` non unique. `ACCOUNT_EMAIL_VERIFICATION="mandatory"` prépare le parcours après décision métier. Aucun signup public en IDR-003.
5. `ACCOUNT_SIGNUP_FIELDS` contient les champs username/email/password requis pour une future activation, pas une autorisation actuelle de créer des comptes.
6. Pas de `ModelBackend` supplémentaire qui contournerait les politiques allauth. Pas d'admin Django connecté. La stratégie d'accès admin sera revérifiée plus tard.
7. `HEADLESS_SERVE_SPECIFICATION=False` par défaut, `True` dans le seul profil de génération `config.settings.spec`. Installer `django-allauth[headless-spec]` uniquement dans le groupe de développement.
8. Produire `docs/api/allauth-browser-openapi.json` depuis `/_allauth/openapi.json` avec `Client`, normaliser le JSON et vérifier la dérive en CI. Les UUID4 générés aléatoirement pour les exemples de compte sont remplacés par des UUID de démonstration stables, sans modifier les chemins ni le modèle contractuel. La version 65.22.1 fournit **22 chemins navigateur** dans ce profil, sans chemins app. Ne pas considérer la spec comme une API inventée.
9. Les URLs frontend sont paramétrées par `FRONTEND_ORIGIN`, en HTTPS obligatoire pour staging. Aucun serveur Next.js n'est relié à Django à ce stade.

## Sécurité, limites

- `username` est unique au niveau Django ; `email` reste non unique en base. Le futur login email-only exigerait un ADR et la revue des données/contraintes.
- Les règles d'unicité et d'énumération allauth doivent être testées avant activation du signup (IDR-008). La documentation upstream OpenAPI décrit aussi les endpoints non disponibles avec notre configuration (signup désactivé, MFA/providers non activés) : l'existence d'un chemin documenté ne vaut pas autorisation fonctionnelle.
- Toute requête browser mutative devra être protégée par le CSRF dans G1.
- Le port 3000 et le port 8000 sont **deux origines différentes** en développement ; aucune promesse d'authentification de bout en bout avant le proxy même origine de G1.
- Aucun provider social n'est configuré. L'app socialaccount seule n'implique pas de Google OAuth fonctionnel.
- `config.settings.spec` ne doit pas être configuré sur un serveur public ; publier le schéma complet de production n'est pas une exigence.

## Preuves attendues

- `uv sync --locked --group dev`, `makemigrations --check --dry-run`, `migrate`, `manage.py check`
- Tests enregistrant les URLs, la politique username, l'absence de client app et la désactivation de signup
- Export OpenAPI réel et comparaison byte-for-byte dans GitHub Actions
- Aucune clé OAuth ou secret de production dans Git

## Preuves d'acceptation

- [PR #7 - Fusion IDR-003](https://github.com/tawounfouet/identity-reference-poc/pull/7)
- [CI finale - 18 tests et OpenAPI sans dérive](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44599483827)
- [Génération de l'OpenAPI](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44598118591)
- Workflow éphémère `contents:write` supprimé après exécution.

## Références officielles

- https://docs.allauth.org/en/latest/headless/installation.html
- https://docs.allauth.org/en/latest/headless/configuration.html
- https://docs.allauth.org/en/latest/installation/quickstart.html
- https://docs.allauth.org/en/latest/account/configuration.html
