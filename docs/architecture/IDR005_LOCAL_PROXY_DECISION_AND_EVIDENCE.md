# IDR-005 - Décisions et preuves P0/P1 : proxy local same-origin

> Date : 2026-11-19
> Ticket : [IDR-005 #14](https://github.com/tawounfouet/identity-reference-poc/issues/14)
> PR : [#15 - brouillon](https://github.com/tawounfouet/identity-reference-poc/pull/15)
> État : **P1 LOCAL DEMONSTRATED, STAGING/TLS/COOKIES NOT VALIDATED**
> Gate G0 : PASSED (socle local seulement). Gate G1 : **NO-GO**, toujours en cours.

## 1. Décision P0 actée

Conserver une **origine unique vue par le navigateur** pour les pages Next.js et les endpoints Django. Pour P1, employer uniquement les rewrites côté serveur Next.js en mode `development`, avec une variable non publique `DJANGO_PROXY_ORIGIN` limitée à une origine HTTP loopback explicite. La séparation des ports reste **interne au serveur proxy**, non un choix de double origine dans le code du navigateur.

## 2. Routage opérationnel local

| Entrée visible | Responsabilité | Origine interne |
|---|---|---|
| `/`, `/account/*`, `/_next/*` | Next.js | Next.js dev server |
| `/_allauth/*` | Django / allauth Headless | `http://127.0.0.1:8000` |
| `/accounts/*` | Django / callback social futur | `http://127.0.0.1:8000` |
| `/api/*` | Django / domaine métier futur | `http://127.0.0.1:8000` |
| `/health`, `/health/` | Django | `http://127.0.0.1:8000/health/` |

Les rewrites sont **désactivées** quand `NODE_ENV` n'est pas `development` ou que la variable n'est pas définie. La destination est refusée si elle n'est pas une URL `http` loopback avec port explicite, sans chemin, login, query ou fragment. Le backend n'est jamais transmis par une variable `NEXT_PUBLIC_`.

## 3. Preuve HTTP réelle, sans simuler Django

[Exécution GitHub Actions #44617239754](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44617239754) sur commit `910c1c407092a8359ea1438693e4d656c75e839c` :

- Installation des graphes `uv.lock` / `pnpm-lock.yaml` sur runner vierge.
- Migration d'une base SQLite jetable sur `config.settings.local`.
- Démarrage de Django `127.0.0.1:8000` et Next.js `127.0.0.1:3000` dans le même environnement CI.
- `GET http://127.0.0.1:3000/health/` -> HTTP 200, corps Django JSON attendu.
- `GET http://127.0.0.1:3000/_allauth/browser/v1/config` -> HTTP 200, `status=200`, JSON.
- `GET http://127.0.0.1:3000/_allauth/browser/v1/auth/session` -> HTTP 401, `meta.is_authenticated=false` et `flows` disponibles.
- `GET http://127.0.0.1:3000/` -> HTTP 200, contenu HTML Next.js.
- **3/3 jobs verts** : backend Django, frontend Next.js et smoke HTTP réel.

La preuve est limitée au **routage et au contenu HTTP local sur protocole HTTP**. Elle ne contient aucun secret et ne démontre pas la transmission correcte des cookies `Secure` ni des en-têtes de confiance en staging.

## 4. Décisions de staging NON prises

**Ne pas déployer ni fermer IDR-005** sans résolution des points suivants :

1. Choix explicite du domaine de staging contrôlé et des acteurs DNS/certificat TLS.
2. Hébergement et réseau du service Django, origine frontend (Vercel ou autre), isolation des origines.
3. Arbitrage proxy Cloudflare (règles/Worker selon besoin) **ou** rewrites Next.js/Vercel, et nombre de sauts de proxy.
4. Destruction des en-têtes `Forwarded`, `X-Forwarded-Host`, `X-Forwarded-Proto` fournis par l'extérieur avant de les reconstruire au dernier proxy de confiance.
5. Politique `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, cookie host-only, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`, `ALLOWED_HOSTS`, HSTS, `SECURE_PROXY_SSL_HEADER`.
6. Désactivation du cache privé et inspection de `Set-Cookie`, `Location`, `Origin`, méthodes et corps POST sur HTTPS de staging.
7. Tests adversariaux Host et headers forgés, et HAR anonymisé.
8. Passage de relais à IDR-006 (bootstrap CSRF réel, rotation et négatifs), sans activer de mutation dépourvue de CSRF.

## 5. Limites de cette PR

La PR est volontairement **draft**. Aucun GO staging, G1 ou production n'est demandé. Toute CI verte n'est pas une preuve d'un cookie sécurisé sur un domaine HTTPS inconnu.

## 6. Références

- [Plan IDR-005](../plans/IDR_005_SAME_ORIGIN_TOPOLOGY_IMPLEMENTATION_PLAN.md)
- [Audit G0 final](../gates/G0_FINAL_ACCEPTANCE_AUDIT.md)
- [ADR-003 Headless](../adr/ADR-003-headless-browser-and-username-policy.md)
- [ADR-004 Browser TS](../adr/ADR-004-typed-browser-client.md)

## 7. IDR-005/P2 - Politique Django et vérifications sans déploiement HTTPS

Le socle P2 explicite désormais dans `config.settings.base` des cookies **host-only**, `SameSite=Lax`, `HttpOnly=True` pour la session et `HttpOnly=False` pour le CSRF (le client TypeScript lit `csrftoken`). Le stockage reste `django.contrib.sessions.backends.db` et aucune exception cross-origin CSRF n'est ajoutée.

Le profil `config.settings.staging` impose `Secure=True` sur les deux cookies et exige `DJANGO_ALLOWED_HOSTS` exactement égal à l'hôte de `FRONTEND_ORIGIN=https://...`, sans wildcard ni domaine local. Le profil local/test conserve les cookies non Secure pour les essais HTTP loopback.

Le middleware `ValidateHostMiddleware` force `request.get_host()` sur **toutes les routes**, y compris `/health/`, afin que `ALLOWED_HOSTS` soit effectivement appliqué à toutes les réponses.

**Frontière de confiance volontairement non ouverte :** `SECURE_PROXY_SSL_HEADER=None`, `USE_X_FORWARDED_HOST=False`, `USE_X_FORWARDED_PORT=False`, HSTS=0 et pas de redirection TLS forcée tant que P3 n'a pas identifié et vérifié le reverse proxy réel. Activer un de ces mécanismes sur un proxy non maîtrisé pourrait créer des failles ou des boucles de redirection.

Tests backend ajoutés pour la politique, les Hosts adversariaux, les headers non approuvés et les attributs de vrais cookies Django avec paramètres Secure simulés. **Ils ne constituent pas une preuve HTTPS staging**. L'endpoint CSRF dédié et les rotations réelles demeurent IDR-006.
