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
