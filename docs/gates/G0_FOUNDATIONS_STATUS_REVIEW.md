# G0 - Revue du statut Foundations après IDR-004

> Date : 19 novembre 2026
> Statut : **IN_REVIEW - GO G0 non prononcé**
> Portée : baseline contractuelle et reproductibilité, pas de certification de sécurité production.

## Réalisations et preuves

| Exigence | Preuve | Statut |
|---|---|---|
| Monorepo Django/Next.js et scripts reproductibles | PR #2, uv.lock, pnpm-lock.yaml | Livré |
| Django Custom User UUID et première migration propre | PR #4, ADR-002, CI migrations, tests UUID | Livré |
| django-allauth Headless browser, routes et sessions Django | PR #7, ADR-003, CI backend | Livré |
| Export réel OpenAPI, snapshot vérifié | docs/api/allauth-browser-openapi.json, PR #7 | Livré |
| Types TS générés depuis snapshot réel | frontend/src/features/auth/api/generated/allauth.d.ts, PR #10 | Livré |
| Mapper `meta/flows` et transport fail-closed CSRF | 12 tests auth frontend, PR #10 | Livré |
| Vérifications CI backend/frontend/contracts | [CI finale IDR-004](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607781264) | SUCCESS |

## Points avant un GO formel sur G0

1. **ADR-005** : ROADMAP §04 demande explicitement ADR-001 à ADR-005. L'ADR-005 n'est pas encore créé/accepté. Ne pas masquer cette exigence.
2. **Revue gate G0 exhaustive** : confirmer le respect de chacun des critères du §04 et des décisions DEC-01 à DEC-05, sans interpréter une CI verte comme une preuve universelle de sécurité.
3. **Registre de sécurité et compatibilité** : enregistrer l'examen final des versions figées et des avis de sécurité au SHA retenu avant décision GO/NO-GO G0.

## Ne pas confondre G0 et G1

Les contrôles de **même origine publique**, reverse proxy, cookies sécurisés, cycle complet de CSRF, tests de rotation et de rejet, parcours navigateur E2E, OAuth, MFA et isolation multi-tenant **ne sont pas démontrés**.

IDR-004 a introduit un client **fail-closed** : une mutation sans CSRF provoque une erreur locale sans requête réseau. Ce garde-fou ne fournit pas le token CSRF et ne dispense jamais d'implémenter le vrai bootstrap en IDR-005/006.

Aucune interface de login en production, aucune inscription publique et aucun GO de production ne sont autorisés sur la seule base de ce gate.

## Décisions du jour

- IDR-001, IDR-002, IDR-003, IDR-004 : **DONE**.
- G0 : **IN_REVIEW, pas de validation formelle**.
- La priorité suivante est de finaliser l'audit de sortie G0 puis d'ouvrir G1/IDR-005 (same-origin) et IDR-006 (CSRF).

## Liens

- [ROADMAP.md](../../ROADMAP.md)
- [R1 - Architecture et contrats](../references/R1_DJANGO_ALLAUTH_HEADLESS_REACT_REFERENCE_IMPLEMENTATION_AND_CONTRACTS.md)
- [PR #10](https://github.com/tawounfouet/identity-reference-poc/pull/10)
