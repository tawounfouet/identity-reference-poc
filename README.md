# identity-reference-poc

POC de référence Django + django-allauth Headless + Next.js.

**Statut : IDR-001 / G0 en cours. Pas de déploiement de production.**

## Périmètre de ce ticket

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

**Ne pas lancer `migrate` avant la livraison d'IDR-002.** La configuration de bootstrap n'installe pas encore le custom User, précisément pour respecter cette contrainte.

## Frontend

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm typecheck
pnpm build
pnpm dev
# http://localhost:3000
```

Aucun écran de connexion fonctionnel n'est annoncé pendant IDR-001.

## Verrouillage et CI

Les fichiers `backend/uv.lock` et `frontend/pnpm-lock.yaml` sont générés depuis des registres de paquets par le workflow [bootstrap-lockfiles](.github/workflows/bootstrap-lockfiles.yml), puis committés sur la branche de ticket. La CI de PR refuse toute installation non verrouillée et exécute les vérifications de chaque stack.

Les versions de première sélection sont documentées dans [ADR-001](docs/adr/ADR-001-bootstrap-toolchain.md). Aucune clé ou donnée personnelle ne doit être committée.

## Sécurité et limites

Les `.env` ne sont pas versionnés. Le mode `local` contient uniquement une clé de développement explicitement non sécurisée. Les environnements staging et production exigeront une clé fournie par l'environnement. Le frontend ne conserve ni mots de passe ni tokens dans `localStorage`.

**G0 reste NON VALIDÉ** tant que les lockfiles, les tests et les journaux GitHub Actions n'ont pas été vérifiés.
