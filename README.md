# identity-reference-poc

POC de référence Django + django-allauth Headless + Next.js.

**Statut : IDR-001 et IDR-002 livrés, G0 encore en cours. Pas de déploiement de production.**

## Historique des livraisons

- IDR-001 : bootstrap du monorepo, lockfiles, CI ([PR #2](https://github.com/tawounfouet/identity-reference-poc/pull/2)).
- IDR-002 : identité UUID et migration initiale ([PR #4](https://github.com/tawounfouet/identity-reference-poc/pull/4)).
- IDR-003 : activation allauth Headless et export OpenAPI, à venir.

## Périmètre du bootstrap

IDR-001 crée le monorepo, la configuration des outils, la base Django, le squelette Next.js, les lockfiles et la CI. Il **n'active pas** les parcours d'authentification et ne définit pas encore le modèle utilisateur.

- `IDR-002` : définir `identities.User` avant la première migration Django.
- `IDR-003` : installer les apps allauth Headless, exposer les routes et exporter l'OpenAPI issue du backend réel.
- `G1` : prouver les sessions, cookies sécurisés, le routage même origine et le CSRF.

Lire [ROADMAP.md](ROADMAP.md) et le [document de référence R1](docs/references/R1_DJANGO_ALLAUTH_HEADLESS_REACT_REFERENCE_IMPLEMENTATION_AND_CONTRACTS.md).

## Prérequis

- Python 3.13 ; `uv` 0.10.0
- Node.js 22 ; `pnpm` 11.28.12
- Le réseau est nécessaire lors de la première résolution des dépendances.

## Backend (depuis la racine)

```sh
cd backend
uv sync --locked --group dev
uv run --locked python manage.py check
uv run --locked pytest
uv run --locked ruff check .
```

Pour démarrer localement (uniquement après installation) :

```sh
cd backend
uv run --locked python manage.py runserver
# GET http://127.0.0.1:8000/health/
```

**À partir d'IDR-002,** `migrate` est autorisé sur une base neuve après vérification du modèle `identities.User`. Cette procédure ne remplace pas une migration de données sur base existante.

## Frontend

```sh
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
corepack pnpm dev
# http://localhost:3000
```

Aucun écran de connexion fonctionnel n'est annoncé pendant IDR-001.

**Important :** exécuter les commandes depuis `frontend/`. `corepack pnpm` sélectionne la version déclarée par `packageManager` ; un `pnpm` global plus ancien peut malgré tout installer avec succès, mais il ne garantit pas l'alignement du poste de travail.

## Verrouillage et CI

Les fichiers `backend/uv.lock` et `frontend/pnpm-lock.yaml` ont été générés depuis les registres de paquets, puis committés sur la branche de ticket par le [workflow de bootstrap, exécuté avec succès](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44503449515). Le workflow temporaire doté de permissions d'écriture a ensuite été retiré. La CI de PR refuse toute installation non verrouillée et exécute les vérifications de chaque stack.

Les versions de première sélection sont documentées dans [ADR-001](docs/adr/ADR-001-bootstrap-toolchain.md). Aucune clé ou donnée personnelle ne doit être committée.

## IDR-002 - Modèle User UUID (prêt à migrer sur base neuve)

L'application `apps.identities` définit désormais `AUTH_USER_MODEL = "identities.User"` dans tous les profils Django. Elle conserve `AbstractUser.username` comme identifiant unique, avec UUID v4 opaque comme clé primaire.

```sh
cd backend
uv sync --locked --group dev
uv run --locked python manage.py makemigrations --check --dry-run
uv run --locked python manage.py migrate --noinput
uv run --locked python manage.py check
uv run --locked pytest
uv run --locked ruff check .
```

**Important :** exécuter les migrations uniquement sur une base locale neuve. Si une base `bootstrap.sqlite3` préexistante contient déjà des migrations ou des données, ne pas réutiliser ou supprimer ses données sans audit. Se référer à [ADR-002](docs/adr/ADR-002-identity-user-model.md). Les parcours allauth restent hors scope d'IDR-002.

## Sécurité et limites

Les `.env` ne sont pas versionnés. Le mode `local` contient uniquement une clé de développement explicitement non sécurisée. Les environnements staging et production exigeront une clé fournie par l'environnement. Le frontend ne conserve ni mots de passe ni tokens dans `localStorage`.

**G0 reste NON VALIDÉ** tant que les lockfiles, les tests et les journaux GitHub Actions n'ont pas été vérifiés.

## IDR-003 - Activation allauth Headless et contrats

`allauth.account`, `allauth.headless` et `allauth.socialaccount` sont intégrés. Aucun provider OAuth n'est configuré et les inscriptions sont désactivées.

```sh
cd backend
uv sync --locked --group dev
uv run --locked python manage.py migrate --noinput
uv run --locked python manage.py check
uv run --locked python tools/export_headless_openapi.py --check
uv run --locked pytest
```

Routes : `GET /health/`, `/_allauth/browser/v1/` pour l'API Headless, `/accounts/` réservé aux parcours callback futurs.

Le schéma (22 chemins browser pour la version verrouillée) est exporté exclusivement depuis `config.settings.spec`, et absent des configurations ordinaires. L'export peut être régénéré avec `uv run --locked python tools/export_headless_openapi.py`. Voir [ADR-003](docs/adr/ADR-003-headless-browser-and-username-policy.md).
