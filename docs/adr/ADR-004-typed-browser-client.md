# ADR-004 - Client TypeScript browser fondé sur l'OpenAPI réel

- Date : 2026-11-19
- Statut : accepté, implémenté via PR #10 fusionnée ; CI définitive réussie
- Dépend : ADR-002 (UUID + username), ADR-003 (browser-only Headless et snapshot réel)
- Couvre : ROADMAP G0 / IDR-004 ; G1 à G5 demeurent des gates indépendants

## Contexte et contrainte majeure

Notre backend expose le contrat OpenAPI de django-allauth 65.22.1 sous 22 chemins navigateur. Ce schéma documente la **forme** des réponses mais non l'activation effective de tous les parcours (signup désactivé, MFA et OAuth non configurés).

Les réponses `401` peuvent représenter plusieurs étapes d'authentification ; `data.user` peut exister dans une étape partielle. Un client qui déduit `authenticated` du seul HTTP 200 ou de la présence de `user` serait vulnérable à des erreurs d'autorisation.

## Décisions

1. `openapi-typescript==7.13.0` génère, depuis notre JSON **committé**, `frontend/src/features/auth/api/generated/allauth.d.ts`. L'exécution exige `pnpm-lock.yaml` et la CI échoue si le snapshot typé change sans commit. Aucun type de réponse authentification n'est réinventé à côté.
2. `ENDPOINTS` est vérifié à la compilation via `satisfies Record<string, keyof paths>`. Seuls `GET session`, `DELETE session`, `POST login` et `GET config` sont exposés au transport. Aucune URL absolue ou fournie par un appelant.
3. Le client browser utilise `credentials:"same-origin"`, `mode:"same-origin"`, `cache:"no-store"` et `redirect:"error"`. Il ne stocke aucune session ni aucun credential en JavaScript.
4. **Fail-closed CSRF** : toute mutation est refusée localement si le cookie `csrftoken` manque. Il n'y a aucun bootstrap factice. Le bootstrap réel, la rotation des tokens, les cookies sécurisés et les preuves cross-browser appartiennent à IDR-005/006.
5. La connexion prend `username` et `password`, conformément à `ACCOUNT_LOGIN_METHODS={"username"}`. Aucun endpoint signup public dans le client.
6. Un mapper **pur et testé** extrait les transitions depuis `httpStatus`, `meta.is_authenticated` et `data.flows`. `authenticated` exige conjointement HTTP 200, `meta.is_authenticated=true` et un `user.id` non vide. Les données partielles ou inconnues ne donnent jamais cet état.
7. Les états `anonymous`, `pending-email`, `pending-mfa`, `reauth-required`, `invalid-input`, `forbidden`, `conflict`, `rate-limited` et `unavailable` sont explicites. `409` indique un besoin de relecture de session mais ne provoque **aucune** mutation en boucle ou retry automatique.
8. `AuthClientError` expose des codes stables pour absence CSRF, transport, annulation, réponse non JSON ou enveloppe invalide. Pas de journalisation des mots de passe, cookies ou payloads.
9. Les types OpenAPI constituent des contrats **à la compilation**. Le transport n'effectue qu'une validation runtime minimale du statut et de la nature JSON ; la validation runtime approfondie, les tests navigateur CSRF et les écrans relèvent des incréments suivants.

## Critères de preuve

- Génération reproducible de `allauth.d.ts` et comparaison stricte en CI.
- Tests Node isolés du navigateur, sans appel à une instance Django, pour les états 200/401/403/409/410/429, protocol errors, CSRF absent, rotation relue au moment de chaque mutation, absence de retry, non JSON et abort.
- `pnpm test`, `pnpm typecheck`, `pnpm build` au vert sur le SHA de PR.
- Le backend IDR-003 et ses 18 tests restent verts.

## Limites

Pas de login utilisateur complet tant que le proxy même origine et le bootstrap CSRF ne sont pas démontrés. Ne jamais considérer `HEADLESS_ONLY` ou l'OpenAPI comme des preuves de conformité production.

## Preuves enregistrées

- [PR #10 - Implémentation et fusion IDR-004](https://github.com/tawounfouet/identity-reference-poc/pull/10)
- [CI finale : Django, frontend, 12 tests auth, typecheck, build et diff typegen](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607781264)
- [Génération initiale verrouillée et tests frontend](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607410924)
- Workflow `contents:write` supprimé avant la fusion.

## Références

- https://openapi-ts.dev/introduction
- https://openapi-ts.dev/cli
- https://docs.allauth.org/en/latest/headless/openapi-specification/
- docs/references/R1_DJANGO_ALLAUTH_HEADLESS_REACT_REFERENCE_IMPLEMENTATION_AND_CONTRACTS.md (sections 06 à 08)
