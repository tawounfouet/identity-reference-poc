# identity-reference-poc

POC de référence Django + django-allauth Headless + Next.js.

**Statut : IDR-001 à IDR-004 livrés ; G0 PASSED pour le socle local ; IDR-005 P1/P2 livré en PR #15 ; G1, staging HTTPS et production non validés.**

## Historique des livraisons

- IDR-001 : bootstrap du monorepo, lockfiles, CI ([PR #2](https://github.com/tawounfouet/identity-reference-poc/pull/2)).
- IDR-002 : identité UUID et migration initiale ([PR #4](https://github.com/tawounfouet/identity-reference-poc/pull/4)).
- IDR-003 : django-allauth Headless browser et OpenAPI réelle ([PR #7](https://github.com/tawounfouet/identity-reference-poc/pull/7)).
- IDR-004 : client TypeScript généré depuis OpenAPI, machine d'états et 12 tests ([PR #10](https://github.com/tawounfouet/identity-reference-poc/pull/10)).

## Périmètre du bootstrap

IDR-001 crée le monorepo, la configuration des outils, la base Django, le squelette Next.js, les lockfiles et la CI. Il **n'active pas** les parcours d'authentification et ne définit pas encore le modèle utilisateur.

- `IDR-002` : définir `identities.User` avant la première migration Django.
- `IDR-003` : installer les apps allauth Headless, exposer les routes et exporter l'OpenAPI issue du backend réel.
- `G1` : prouver les sessions, cookies sécurisés, le routage même origine et le CSRF.

Lire [l'audit final G0](docs/gates/G0_FINAL_ACCEPTANCE_AUDIT.md), [ADR-005](docs/adr/ADR-005-local-openapi-contract-and-version-policy.md), [ROADMAP.md](ROADMAP.md) et le [document de référence R1](docs/references/R1_DJANGO_ALLAUTH_HEADLESS_REACT_REFERENCE_IMPLEMENTATION_AND_CONTRACTS.md).

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

**Historique d'IDR-001 :** G0 n'était alors pas validé. Le GO limité au socle local a depuis été enregistré dans [l'audit final G0](docs/gates/G0_FINAL_ACCEPTANCE_AUDIT.md).

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

## IDR-004 - Client TypeScript contractuel

L'API browser est construite **uniquement** à partir des routes validées par le schéma de `docs/api/allauth-browser-openapi.json`. Le client est un module indépendant de la page de connexion, qui ne sera ajoutée qu'après la validation de G1.

```sh
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm types:generate
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
```

- `src/features/auth/api/generated/allauth.d.ts` est **généré**, non modifié à la main.
- `BrowserAuthClient` expose `loadSession`, `login(username,password)`, `logout` et `loadConfiguration`.
- `mapAuthEnvelope` distingue login initial, vérification email, MFA, réauthentification, conflit, refus et disponibilité à partir du HTTP, de `meta` et de `data.flows`.
- Sur toute mutation (POST/DELETE), le transport exige un cookie CSRF lisible ; **en son absence, aucune requête ne part**. G1 doit implémenter le vrai bootstrap et la topologie même origine avant un vrai login navigateur.
- Aucun secret dans `localStorage`, aucun token JWT, aucun replay automatique ou URL arbitraire.
- Le code génère `AuthClientError` pour les réponses non JSON / réseau / statut incohérent ; les consommateurs doivent traiter ces erreurs sans révéler leurs détails.

Voir [ADR-004](docs/adr/ADR-004-typed-browser-client.md) et [l'état des preuves G0](docs/gates/G0_FOUNDATIONS_STATUS_REVIEW.md). La CI compare le fichier régénéré à la version commitée pour détecter toute dérive du contrat.

## IDR-005 - Fondations locales P1/P2 (livraison partielle, non finale)

Le plan de topologie est versionné dans [docs/plans/IDR_005_SAME_ORIGIN_TOPOLOGY_IMPLEMENTATION_PLAN.md](docs/plans/IDR_005_SAME_ORIGIN_TOPOLOGY_IMPLEMENTATION_PLAN.md). Une configuration **exclusivement locale** de Next.js est ajoutée pour démarrer l'intégration du proxy par chemins. Cela ne valide **ni HTTPS staging, ni les cookies, ni le cycle CSRF**.

Démarrer Django dans un premier terminal :

```sh
cd backend
uv sync --locked --group dev
uv run --locked python manage.py migrate --noinput
uv run --locked python manage.py runserver 127.0.0.1:8000
```

Démarrer Next.js dans un second terminal :

```sh
cd frontend
corepack pnpm install --frozen-lockfile
DJANGO_PROXY_ORIGIN=http://127.0.0.1:8000 corepack pnpm dev --hostname 127.0.0.1
```

Les endpoints `http://127.0.0.1:3000/health`, `http://127.0.0.1:3000/_allauth/browser/v1/auth/session` et `http://127.0.0.1:3000/_allauth/browser/v1/config` transitent alors par le proxy Next.js vers Django. `/health/` peut retourner un 308 de canonicalisation Next.js vers `/health`, puis un 200 en suivant la redirection. Les pages et les assets sont rendus par Next.js. Les règles ne sont installées **qu'en mode development**, quand `DJANGO_PROXY_ORIGIN` est un véritable `http://localhost:<port>` ou `http://127.0.0.1:<port>` sans chemin, identifiants ni paramètres. Cette variable n'a pas de préfixe `NEXT_PUBLIC_`.

L'origine staging, son reverse proxy de confiance, TLS, cookies host-only et la gestion `X-Forwarded-*` sont **encore à sélectionner et démontrer**. Ne pas activer `SECURE_PROXY_SSL_HEADER` pour masquer une absence de TLS.

**Preuve de routage P1 local :** [IDR005_LOCAL_PROXY_DECISION_AND_EVIDENCE.md](docs/architecture/IDR005_LOCAL_PROXY_DECISION_AND_EVIDENCE.md) et [CI HTTP réelle](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44617239754). Cette étape n'autorise pas encore le déploiement de staging.

### IDR-005 P2 : cookies, Host et limites

Les settings Django déclarent explicitement `sessionid` comme cookie HttpOnly, `csrftoken` comme cookie lisible par le client JavaScript, tous deux `SameSite=Lax` et host-only. Les cookies sont non Secure **uniquement dans les profils locaux/tests HTTP**. Staging exige une origine HTTPS exacte, un `DJANGO_ALLOWED_HOSTS` correspondant, et émet les deux cookies avec `Secure=True`.

La validation `ALLOWED_HOSTS` s'exécute désormais pour chaque requête, même sur `/health/`. Aucun en-tête `X-Forwarded-*` n'est implicitement approuvé en P2 ; définir un proxy TLS de confiance et inspecter les cookies réellement reçus sur HTTPS restent P3. La création de l'endpoint CSRF et la rotation après login restent IDR-006.

### Acceptation et reprise d'IDR-005 après PR #15

La [PR #15](https://github.com/tawounfouet/identity-reference-poc/pull/15) est volontairement **limitée aux fondations P1/P2** : proxy local loopback, politique de cookies et de Host, tests et CI. Son intégration dans `main` **ne clôture pas** [l'issue IDR-005 #14](https://github.com/tawounfouet/identity-reference-poc/issues/14), qui demeure ouverte pour la sélection de l'infrastructure HTTPS et les contrôles P3/P5.

Lire la [revue d'acceptation P1/P2](docs/reviews/IDR_005_P1_P2_ACCEPTANCE_AND_HANDOFF.md) pour le détail des preuves et des travaux restants. Les rewrites sont inactives dans les builds de production et aucun certificat, domaine, routage CDN ou bootstrap CSRF réel n'a été provisionné ici.
