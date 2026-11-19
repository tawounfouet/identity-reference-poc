# G0_FINAL_ACCEPTANCE_AUDIT - Revue finale Foundations

> Projet : `identity-reference-poc`  
> Date de revue : **19 novembre 2026**  
> Baseline de départ : `63e62d567b1a8b58bd6380f59009ec3a487a0c10` (`main` avant cette PR)  
> Gate : G0 - Foundations / contrats locaux  
> **Décision : GO G0 limité au socle local et à l'ouverture de G1, sous condition de CI verte et fusion de la PR d'acceptation.**  
> **Production : NO-GO. G1 : NON VALIDÉ.**  
> Dossier de suivi : [issue #12](https://github.com/tawounfouet/identity-reference-poc/issues/12)

## 1. Périmètre de la décision

G0 valide l'existence d'une baseline technique **locale, documentée, testée et reproductible**. Il ne valide ni une origine publique HTTPS, ni la topologie reverse proxy, ni le fonctionnement d'un login complet depuis Next.js, ni la sécurité CSRF E2E, ni MFA/OAuth, ni l'isolation des organisations, ni un déploiement de production.

Le GO ici signifie uniquement : **autoriser l'ingénierie G1 dans une branche isolée**, avec exposition minimale et sans activation d'un service d'authentification public.

## 2. Matrice d'acceptation ROADMAP §04.A

| # | Exigence | Constat et preuve | Verdict |
|---|---|---|---|
| A01 | Monorepo, docs, CI | PR [#2](https://github.com/tawounfouet/identity-reference-poc/pull/2), `backend/`, `frontend/`, `.github/workflows/ci.yml` | PASS |
| A02 | Versions et avis de sécurité | Manifestes et lockfiles, scan détaillé ci-dessous, notes de release Django/allauth/Next | PASS ponctuel |
| A03 | Lockfiles et installation à froid | CI `uv sync --locked`, `pnpm install --frozen-lockfile` et builds sur runner vierge | PASS |
| A04 | Custom User avant migration | PR [#4](https://github.com/tawounfouet/identity-reference-poc/pull/4), `identities/0001_initial.py`, PK UUID4 ; 7 tests du modèle | PASS |
| A05 | Auth/allauth et middleware | PR [#7](https://github.com/tawounfouet/identity-reference-poc/pull/7), settings, URLConf, migrations `account` et `socialaccount` | PASS |
| A06 | Configuration Headless navigateur | `HEADLESS_ONLY=True`, `HEADLESS_CLIENTS=("browser",)`, URLs de retour par profil | PASS |
| A07 | `accounts/` et `_allauth/` | `backend/config/urls.py` + tests de résolution de routes | PASS |
| A08 | DB test et séparation de secrets | `config.settings.test` avec base de test Django, `local` distinct de `staging` et clés réelles absentes des manifests | PASS périmètre Git |
| A09 | OpenAPI réel et contrôlé | [CI PR #7](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44599483827), 22 chemins browser, profil `spec` isolé | PASS |
| A10 | Génération TS du schéma local | `openapi-typescript`, `allauth.d.ts` et diff CI [PR #10](https://github.com/tawounfouet/identity-reference-poc/pull/10) | PASS |
| A11 | Healthcheck, migrations, routes | 18 tests Django, `makemigrations --check`, migrations sur DB vierge en CI | PASS |
| A12 | ADR-001 à ADR-005, DEC-01 à DEC-05 | ADR-001 à 004 préexistantes ; **ADR-005 créée dans cette PR** ; table de correspondance §4 | PASS à fusion |

## 3. Matrice de sortie ROADMAP §04.B

| Exigence | Preuve | Décision |
|---|---|---|
| Clone vierge installe et démarre les stacks | CI backend/frontend ; tests de healthcheck et build ; journaux locaux utilisateur | PASS pour les composants testés |
| Pas de migration User destructrice initiale | Initial migration `identities/0001_initial.py` sur base CI fraîche, `makemigrations --check` | PASS pour une base neuve, hors migration de données existantes |
| Snapshot identique à l'allauth réellement verrouillé | `uv run --locked python tools/export_headless_openapi.py --check` + 22 chemins | PASS |
| Secrets hors Git, `.env.example` sans donnée sensible | `.gitignore`, `.env.example` avec `DJANGO_SECRET_KEY=`, valeurs test/local explicitement non productives | PASS sur l'arbre suivi ; **historique Git complet non audité** |
| CI backend, frontend et contrats verte | [CI SHA IDR-004](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607781264) et [CI clôture](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44608443565) | PASS |

## 4. Gouvernance : DEC-01..05 et nomenclature ADR

### Décisions DEC-01 à DEC-05

| Décision | Application constatée |
|---|---|
| DEC-01 - Modèle User | `AbstractUser` custom, PK UUID v4, username conservé |
| DEC-02 - Identification | `ACCOUNT_LOGIN_METHODS={"username"}`, email **non unique**, signup désactivé |
| DEC-03 - Python | Python 3.13, uv 0.10.0, `backend/uv.lock` |
| DEC-04 - Frontend | Node 22, pnpm 11.28.12, `frontend/pnpm-lock.yaml` |
| DEC-05 - Environnements | Profils `local`, `test`, `staging` et `spec`, aucun déploiement prod revendiqué |

### IMPORTANT : thèmes ADR de §16 vs fichiers existants

La liste §16 de la ROADMAP associe des thèmes idéaux aux numéros ADR-001 à ADR-010. Les ADR effectivement créées sous IDR-001 à IDR-004 ont reçu des titres adaptés au déroulement réel, **sans correspondance numérique un-à-un**. On ne modifie pas l'histoire des décisions et on ne prétend pas que G1 est déjà implémenté :

| ADR existante | Sujet effectif | Thèmes de référence couverts |
|---|---|---|
| `ADR-001-bootstrap-toolchain.md` | Toolchain, versions, frontières bootstrap | DEC-03, DEC-04, configuration baseline |
| `ADR-002-identity-user-model.md` | Modèle User et username / email | DEC-01, DEC-02, modèle authentifié |
| `ADR-003-headless-browser-and-username-policy.md` | allauth, sessions browser, routes, profil OpenAPI | Propriété de l'identité, session, pas de login DRF parallèle |
| `ADR-004-typed-browser-client.md` | Client TS, machine d'état et CSRF fail-closed | Contrats browser et contrôle des états |
| `ADR-005-local-openapi-contract-and-version-policy.md` | OpenAPI réelle, génération et compatibilité | Thème `OpenAPI locale et compatibilité contractuelle` du §16 |

**Thèmes réservés à G1** : topologie same-origin réellement prouvée, protection CSRF E2E et rotation, politique proxy, headers/cookies sécurisés. Une future décision autonome de G1 traitera la topologie ; aucune réécriture silencieuse d'ADR-003.

## 5. Contrôle de sécurité et compatibilité daté

### Graphe Python

- Manifestes : Django 5.2.19, django-allauth 65.22.1, DRF 3.18.3 et dépendances de `backend/uv.lock`.
- [Publication de sécurité Django 5.2.19 du 03/11/2026](https://www.djangoproject.com/weblog/2026/nov/03/security-releases/) et [notes allauth 65.22.1](https://docs.allauth.org/en/latest/release-notes/recent.html) vérifiées le 19/11/2026.
- Exécution GitHub Actions `uv export --locked --all-groups --format requirements-txt --no-hashes` suivie de `uvx --from pip-audit pip-audit --disable-pip --no-deps`.
- Résultat effectivement observé : **No known vulnerabilities found** ; job `Python locked-dependency advisory check` réussi.

### Graphe JavaScript

- Manifestes : Next.js 16.4.6, React 19.3.1, TypeScript 5.9.3 et dépendances de `frontend/pnpm-lock.yaml`.
- Les correctifs critiques et de novembre de la branche Next.js 16.x sont publiés avant la version 16.4.6 ; voir [advisory officiel Next](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw) et [correctifs du 03/11/2026](https://nextjs.org/blog/november-2026-security-release).
- Exécution réelle `pnpm audit --audit-level high`.
- Résultat effectivement observé : **No known vulnerabilities found** ; job `Node locked-dependency advisory check` réussi.

**Source primaire du scan** : [workflow G0 du 19/11/2026](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44615528846), commit de contrôle `3dd3f97c0c6734fb672e6d1b6013e992498eda29`. Le workflow à permissions `contents:read` a été retiré de la branche après l'exécution. Les audits sont ponctuels, fondés sur les bases d'avis accessibles lors du scan et ne remplacent ni SAST, ni revue humaine, ni veille et mises à jour continues. `pnpm audit --audit-level high` ne constitue **pas** une preuve d'absence des avis de sévérité inférieure à ce seuil.

## 6. Invariants de sécurité conservés

- Authentification dans Django/allauth, pas de duplicata DRF/Next.js.
- `identities.User` UUID ; pas d'email-only sans contrainte métier et tests.
- Session Django côté serveur ; aucun jeton de session en localStorage.
- Signup public désactivé ; MFA, OAuth social, organisations non activés.
- Mutations TypeScript bloquées sans cookie CSRF : **la protection navigateur complète ne sera prouvée qu'en G1**.
- Le contrat OpenAPI contient des routes documentées parfois inactives à l'exécution.
- Aucune modification de données existantes, aucune base de staging ni hébergement externe provisionné.

## 7. Risques résiduels, propriétaires et suivi

| Risque / lacune | Gate | Traitement exigé |
|---|---|---|
| Topologie same-origin et TLS non vérifiés | G1 / IDR-005 | Routage local + staging HTTPS, preuve DNS/proxy/cookies |
| En-têtes proxy forgés et mauvaise interprétation TLS | G1 / IDR-005 | Contrat de confiance proxy, tests Host/X-Forwarded |
| Cookies host-only/Secure/HttpOnly/SameSite non attestés en staging | G1 / IDR-005 | Inspection navigateur et tests de non-diffusion |
| CSRF bootstrap et rotation sans preuve réelle | G1 / IDR-006 | Endpoint réel, essais positifs/négatifs, rotation post-login |
| Scans avis de sécurité non continus | Suivi transversal | Réévaluer sur tout changement de lockfile et avant exposition staging |
| Propriété DNS/hébergeur Django et gestion des secrets non fixées | G1 / IDR-005 | Décision d'architecture, revue de déploiement |
| Pas de démonstration complète des comptes | G2+ | Login, verify, logout, sessions, API `me` et droits |

## 8. Décision motivée et GO/NO-GO

**GO G0 (baseline locale et contractualisation), conditionné au succès de la CI et à la fusion de cette PR.** Les douze tâches du §04.A et les cinq critères du §04.B ont des preuves explicites. Les deux audits de dépendances n'ont signalé aucune vulnérabilité connue au seuil évalué. Les ADR-001 à 005 sont documentées sans masquer le décalage de numérotation.

**NO-GO production, NO-GO G1 et NO-GO usage public de la connexion** : aucun mécanisme non testé d'origine, de CSRF, de proxy ou de cookies ne doit être exposé à des utilisateurs réels.

**Conditions de réouverture du gate G0** : échec CI final, modification des lockfiles, écart OpenAPI/types, audit de dépendances révélant une vulnérabilité critique/élevée pertinente, ou changement du modèle User avant données réelles.

## 9. Liens et traçabilité

- [ROADMAP.md](../../ROADMAP.md), §04, §16 et §17
- [Rapport intermédiaire G0](G0_FOUNDATIONS_STATUS_REVIEW.md)
- [ADR-005](../adr/ADR-005-local-openapi-contract-and-version-policy.md)
- [PR #2](https://github.com/tawounfouet/identity-reference-poc/pull/2), [PR #4](https://github.com/tawounfouet/identity-reference-poc/pull/4), [PR #7](https://github.com/tawounfouet/identity-reference-poc/pull/7), [PR #10](https://github.com/tawounfouet/identity-reference-poc/pull/10)
- [CI G0 baseline](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44608443565)
- [Audit des dépendances G0](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44615528846)
