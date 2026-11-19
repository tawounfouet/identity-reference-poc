# Contrat OpenAPI django-allauth Headless

Le fichier [allauth-browser-openapi.json](allauth-browser-openapi.json) est issu de l'instance Django de ce POC (`django-allauth==65.22.1`).

- 22 chemins browser, aucun chemin app ; l'API serveur est montée sur `/_allauth/`.
- Source : réponse HTTP de `/_allauth/openapi.json` dans `config.settings.spec`.
- Seule normalisation : tri déterministe des clés et remplacement des UUID4 aléatoires figurant dans les exemples, en conservant les relations entre les références.
- Contrôle CI : `cd backend && uv run --locked python tools/export_headless_openapi.py --check`.
- Régénération explicite : `cd backend && uv run --locked python tools/export_headless_openapi.py`.
- L'endpoint de spécification est désactivé dans les profils ordinaires.
- Attention : le schéma upstream documente des opérations qui peuvent être **désactivées par politique** en runtime (ex. signup), ou dépendre d'apps/options non activées (MFA et providers). Ne pas déduire les fonctionnalités activées des seuls chemins OpenAPI.

Voir `docs/adr/ADR-003-headless-browser-and-username-policy.md`.

## Génération du client TypeScript (IDR-004)

La source de vérité reste le JSON issu de notre version verrouillée de django-allauth, et **non** une description API manuelle. Les types frontend sont produits par `openapi-typescript` à partir de ce fichier, puis versionnés dans `frontend/src/features/auth/api/generated/allauth.d.ts`.

```sh
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm types:generate
corepack pnpm test
corepack pnpm typecheck
```

La CI relance exactement le générateur verrouillé, refuse toute différence Git et exécute les tests de mapping `flows/meta`. L'OpenAPI peut documenter certains endpoints non activés par la configuration du backend. IDR-004 ne prétend pas que signup, MFA ou OAuth sont fonctionnels.

Les exports `ENDPOINTS` et `BrowserAuthClient` ne couvrent volontairement que session, login username et configuration. Le navigateur doit encore passer par G1 pour la remise du token CSRF et le proxy même origine.

## État de livraison IDR-004

- Code et types générés : [PR #10 fusionnée](https://github.com/tawounfouet/identity-reference-poc/pull/10)
- [CI de PR entièrement verte](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607781264)
- 12 tests frontend et 18 tests Django. Les types sont régénérés puis comparés en CI avec le fichier versionné.
- La génération de types ne crée pas de requêtes HTTP vers l'instance Django en CI ; elle consomme l'artefact OpenAPI de IDR-003.
