# ADR-005 - Contrat OpenAPI local, génération TypeScript et politique de compatibilité

- Date : 2026-11-19
- Statut : **ACCEPTÉ sous réserve des contrôles CI de la PR G0**
- Gate : G0 Foundations
- Correspondances : DEC-03 (uv), DEC-04 (pnpm), IDR-003 et IDR-004
- Source de vérité : `docs/api/allauth-browser-openapi.json`

## Contexte

Le backend utilise Django 5.2.19, django-allauth 65.22.1 en mode Headless `browser`, et un modèle `identities.User` à PK UUID. Next.js 16.4.6 exploite les routes depuis TypeScript. Une documentation publique ou un type écrit à la main ne représente pas nécessairement les réponses de la version/configuration réellement installées. Le schéma upstream peut décrire des opérations désactivées à l'exécution (signup, providers, MFA).

## Décision

1. **Une seule source de vérité du contrat** : exporter la réponse réelle de `/_allauth/openapi.json` sur le profil temporaire `config.settings.spec`, depuis les dépendances `backend/uv.lock` verrouillées. Cette route n'est pas disponible dans les autres profils.
2. **Snapshot versionné** : enregistrer `docs/api/allauth-browser-openapi.json` dans Git. Cette baseline contient actuellement 22 chemins `/_allauth/browser/v1/*` et aucun chemin `app`.
3. **Normalisation limitée et documentée** : tri des clés et remplacement déterministe des seuls UUID4 aléatoires d'exemples produits par allauth. Interdiction de changer artificiellement la structure des schémas, les chemins ou les codes HTTP pour satisfaire la CI.
4. **Génération de types** : produire `frontend/src/features/auth/api/generated/allauth.d.ts` depuis le JSON versionné avec `openapi-typescript==7.13.0` et le lockfile `frontend/pnpm-lock.yaml` ; ne pas modifier le résultat à la main.
5. **Détection de dérive en CI** : exécuter `uv run --locked python tools/export_headless_openapi.py --check` puis `pnpm types:generate` et `git diff --exit-code`. La CI bloque si le backend et le snapshot ou le snapshot et les types ne coïncident plus.
6. **Compatibilité comportementale** : les tests de `BrowserAuthClient` et `mapAuthEnvelope` protègent la sémantique de `status`, `meta.is_authenticated`, `data.flows`, du mode `same-origin`, du login username et du refus des mutations sans CSRF.
7. **Changement contrôlé** : toute montée de version Django/allauth, ajout d'app allauth ou activation d'un flow requiert une PR contenant une régénération de schéma, une revue explicite du diff, des tests de contrat et un examen des avis de sécurité. Un chemin OpenAPI documenté ne prouve pas son activation.
8. **Frontières** : l'authentification et la session restent gérées par Django ; pas de JWT persistant, pas de login DRF parallèle, pas de session pseudo-authentifiée par la seule présence de `data.user`. Le CSRF E2E et le proxy même origine sont livrés en G1.

## Politique de changements du contrat

| Changement | Classe indicative | Obligation |
|---|---|---|
| Changement d'exemple sans effet sémantique | Documentation | Vérifier la normalisation |
| Ajout d'un endpoint facultatif et désactivé | Extension | Tests de routes et permissions |
| Ajout d'un champ facultatif dans une réponse | Généralement compatible | Typegen + tests des consommateurs |
| Suppression/renommage de champ, route, statut ou flow | Potentiellement cassant | Revue d'impact frontend et stratégie de migration |
| Activation de signup, social, MFA ou email-only | Sécurité + comportement | ADR spécifique, tests positifs/négatifs avant activation |
| Modification des cookies/CSRF/origine | Sécurité critique | Revue G1 et essais sur origine réelle |

Ne pas attribuer automatiquement une version SemVer au seul snapshot OpenAPI d'allauth : le contrat applicatif complet comprend configuration et comportement.

## Alternatives écartées

- Types TypeScript maintenus manuellement, sans comparaison avec Django.
- Génération contre une OpenAPI distante non verrouillée.
- Contrôle de types seul, sans tests de transitions `flows/meta`.
- Export OpenAPI accessible publiquement en permanence.
- Introduction d'un nouveau service d'identité parallèle à django-allauth.

## Conséquences, limites et sûreté

- Deux chaînes de génération doivent rester cohérentes : backend -> snapshot JSON -> types TS.
- Les réponses de génération peuvent contenir des identifiants factices ; aucun token, cookie ou secret réel ne doit être loggé dans les artefacts.
- La validation des types est statique ; le runtime a une validation partielle et les tests navigateurs restent à créer.
- Le proxy staging et le bootstrap CSRF ne sont pas certifiés par ce gate.
- Un rapport d'audit de dépendances `pip-audit`/`pnpm audit` atteste uniquement l'absence **connue** d'avis signalés au moment du scan, pas l'absence intrinsèque de vulnérabilités.

## Preuves d'acceptation

- [IDR-003 / PR #7](https://github.com/tawounfouet/identity-reference-poc/pull/7) et [CI OpenAPI](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44599483827)
- [IDR-004 / PR #10](https://github.com/tawounfouet/identity-reference-poc/pull/10) et [CI typegen + 12 tests frontend](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44607781264)
- [Audit de sécurité ponctuel G0](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44615528846)
- [Audit G0 détaillé](../gates/G0_FINAL_ACCEPTANCE_AUDIT.md)

## Remarque sur la numérotation ADR

Le tableau thématique du `ROADMAP.md` §16 est un **plan de thèmes**, pas la nomenclature effective des quatre ADR déjà livrées. La correspondance exacte, sans renommer rétroactivement ADR-001 à ADR-004, est inscrite dans l'audit G0. Une ADR distincte sur le proxy même origine sera créée pendant G1/IDR-005.

## Références

- https://docs.allauth.org/en/latest/headless/openapi-specification/
- https://openapi-ts.dev/introduction
- https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
