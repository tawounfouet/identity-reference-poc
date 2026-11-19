# IDR-005 - Revue finale et acceptation partielle P1/P2

> Date de décision : 19 novembre 2026  
> Suivi : [Issue IDR-005 #14](https://github.com/tawounfouet/identity-reference-poc/issues/14)  
> Livraison partielle : [PR #15](https://github.com/tawounfouet/identity-reference-poc/pull/15)  
> Gate G0 : PASSED pour la baseline locale, selon [l'audit G0](../gates/G0_FINAL_ACCEPTANCE_AUDIT.md)  
> **Décision : GO pour intégrer P1/P2 dans `main` sous réserve de CI verte sur le SHA final.**  
> **Décision IDR-005 complet : NON CLÔTURÉ. Gate G1 : NO-GO. Staging/production : NO-GO.**

## 1. Périmètre réellement accepté

La PR #15 ne livre **ni staging HTTPS ni CSRF E2E**. Elle est une livraison incrémentale réutilisable avec les mécanismes de sécurité fail-closed suivants :

| Incrément | Contrôle / preuve | Acceptation |
|---|---|---|
| P1 | `rewrites()` Next.js uniquement en `development` si `DJANGO_PROXY_ORIGIN` HTTP loopback explicite | GO local |
| P1 | Préfixes `/_allauth/*`, `/accounts/*`, `/api/*` vers Django ; `/` et `/_next/*` restent Next.js | GO local |
| P1 | Smoke **HTTP réel** avec Django et Next.js lancés sur runner GitHub : `/health/` 200 après redirection éventuelle, config 200, session anonyme 401, page 200 | GO local |
| P1 | Unit tests refusant schémas non HTTP, hôtes non-loopback, chemins, credentials, query et fragments | GO local |
| P2 | Cookies host-only, `SameSite=Lax`, `Secure=True` par défaut | GO configuration |
| P2 | Session `HttpOnly=True`, CSRF `HttpOnly=False` pour client IDR-004 | GO configuration |
| P2 | `local`/`test` sont les seules exceptions explicites `Secure=False` pour loopback HTTP | GO configuration |
| P2 | `ValidateHostMiddleware` impose `request.get_host()` ; mauvais Host rejeté sur `/health/` | GO tests backend |
| P2 | Profil `staging` refuse origin non-HTTPS, Host wildcard/mismatched et defaults localhost | GO tests configuration |
| P2 | `SECURE_PROXY_SSL_HEADER=None`, `USE_X_FORWARDED_HOST=False` tant que la chaîne TLS du proxy n'est pas prouvée | GO fail-closed |
| Transverse | 33 tests backend, 16 tests frontend, migration, lint, typegen et build, smoke HTTP, 3 jobs CI | GO, à reconfirmer au dernier SHA |

**Limite volontaire :** la simulation des attributs `Secure` sous le client de test Django ne prouve pas leur transmission via un edge HTTPS. Les cookies de session ne sont pas mis en production. L'absence de règle de production dans `next.config.ts` signifie que le proxy staging **n'existe pas encore**.

## 2. Revue sécurité et analyse du diff

- Aucune dépendance runtime ni migration Django ajoutée dans cette PR.
- Aucun fournisseur OAuth/MFA/signup activé, aucune exemption CSRF et aucun JWT/localStorage introduit.
- Pas de nouveaux secrets réels ou fichiers `.env` versionnés ; `DJANGO_PROXY_ORIGIN` reste une variable côté serveur, jamais `NEXT_PUBLIC_*`.
- Le proxy local est désactivé hors `NODE_ENV=development` ; aucune prétention de couverture staging.
- `CSRF_TRUSTED_ORIGINS=[]` : pas de dérogation trans-origine inventée.
- La validité d'une URL `FRONTEND_ORIGIN` non canonique est testée par le profil staging ; une **topologie véritable** devra définir les hôtes et le traitement du forwarding en P3.
- Le comportement observé `GET /health/` -> 308 -> `/health` -> 200 est une canonicalisation Next.js, documentée et testée localement.
- Le code de sécurité a été relu en regard des critères P1/P2 et des preuves CI. Cette revue ne constitue ni un pentest indépendant ni une certification.

## 3. Preuves archivées

- [CI finale P1/P2 avant clôture documentaire](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44622123295), sur commit `2034c5b541fc09b3924e29fcbf381f8b72fb969c` : 3/3 jobs réussis, 33 tests Django et 16 tests frontend.
- [Smoke HTTP réel](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44617239754), backend et Next.js exécutés sur le même runner.
- [État P1/P2 documenté](../architecture/IDR005_LOCAL_PROXY_DECISION_AND_EVIDENCE.md).
- **La CI après la présente mise à jour documentaire doit être verte avant fusion.**

## 4. Restent impérativement dans l'issue #14 (P3/P5)

- [ ] Choisir le domaine de staging réellement contrôlé, le DNS, le certificat HTTPS et le point d'entrée public.
- [ ] Choisir le frontend (Vercel ou autre), l'hébergement Django et la frontière privée des origines.
- [ ] Formaliser une **ADR de topologie G1 distincte de l'ADR-005 de G0** et le contrat de nettoyage des headers forwarding.
- [ ] Implémenter le routage edge/rewrite de staging et la politique de cache privée `no-store` sur réponses auth.
- [ ] Prouver depuis HTTPS les chemins, méthodes, query/body, `Set-Cookie` multiples et `Location` sans fuite d'origine backend.
- [ ] Tester l'absence de bypass direct du backend et le rejet des `Host`, `Origin` et `X-Forwarded-*` falsifiés.
- [ ] Inspecter les cookies session/CSRF sur navigateur HTTPS réel, y compris leurs attributs.
- [ ] Tester la séparation entre deux sessions et l'absence de cache partagé sur les données privées.
- [ ] Rédiger la revue sécurité staging avec HAR anonymisé, runbook de rollback, CI et décision GO/NO-GO IDR-005.
- [ ] Transférer ensuite vers IDR-006 (bootstrap CSRF réel, tests négatifs et rotation après login).

Il est interdit de transformer la fusion de P1/P2 en **DONE** pour IDR-005 ou en **PASSED** pour G1. Aucune PR P3/P5 n'est créée par cette revue ; elle sera une livraison séparée après décision de topologie.

## 5. Stratégie de rollback et post-merge

La fusion est additive et localisée ; elle n'altère pas le schéma de la base. En cas de régression locale, arrêter les serveurs, retirer la variable `DJANGO_PROXY_ORIGIN` pour désactiver les rewrites, ou revertir le commit de merge dans une PR de réparation. Ne pas utiliser un rollback de production non éprouvé comme preuve P3/P5.

Après fusion, mettre à jour `main` en fast-forward et **laisser l'issue #14 ouverte**. La prochaine PR sera basée sur `main` et non sur une branche fermée sans ses contrôles.

## 6. Décision finale de revue

- **GO PR #15 / P1-P2** : si tous les jobs GitHub Actions sur le dernier commit réussissent et qu'aucun fichier n'a changé après revue.
- **NO-GO IDR-005 complet** : pas de DNS/proxy/HTTPS staging ni preuves cache/cookies réelles.
- **NO-GO G1** : IDR-006 est un autre ticket, qui reste non implémenté.
