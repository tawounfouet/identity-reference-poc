# ADR-001 - Toolchain et frontières du bootstrap

- Statut : proposé, à valider par la CI de la PR IDR-001
- Date : 2026-11-19
- Portée : ticket IDR-001, non une approbation de G0

## Décision

1. Python 3.13 + `uv` 0.10.0 ; backend Django 5.2.19 LTS.
2. `django-allauth[headless]` 65.22.1 et Django REST Framework 3.18.3 sont référencés dans la résolution, mais non configurés avant IDR-003.
3. Node.js 22 + `pnpm` 11.28.12 ; Next.js 16.4.6, React/React-DOM 19.3.1, TypeScript 5.9.3.
4. Monorepo `backend/` + `frontend/` ; CI séparées en jobs Python/TypeScript.
5. Dépendances verrouillées via `backend/uv.lock` et `frontend/pnpm-lock.yaml`, générées automatiquement sur la branche de bootstrap et relues avant fusion.
6. La CI ne crée **aucune migration**. Le custom User `identities.User` appartient à IDR-002.
7. Staging, Cloudflare, Vercel, Neon, reverse proxy, CSRF, providers OAuth, Redis, authentification et autorisations restent hors du ticket.

## Justification

Privilégier une LTS Django dont le correctif de sécurité du 03/11/2026 est disponible ; conserver un noyau Django minimal et empêcher les migrations prématurées. Les versions React/Next sont choisies après les correctifs de sécurité connus d'octobre 2026. Une nouvelle revue d'advisories sera requise à chaque mise à jour.

## Risques et exigences de preuve

- La construction n'est pas déclarée reproductible sans lockfiles réellement générés.
- Les workflows CI doivent réussir sur le SHA de PR, sans clés réelles.
- Les installations sous `--locked` / `--frozen-lockfile` doivent échouer si un manifeste et son lock sont désynchronisés.
- Le mode local est strictement réservé au développement.

## Sources

- https://www.djangoproject.com/weblog/2026/nov/03/security-releases/
- https://docs.allauth.org/en/latest/release-notes/recent.html
- https://docs.allauth.org/en/latest/headless/installation.html
- https://nextjs.org/support-policy
- https://www.npmjs.com/package/next
