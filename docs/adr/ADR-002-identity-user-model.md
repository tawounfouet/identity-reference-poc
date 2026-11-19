# ADR-002 - Modèle User custom et politique d'identification initiale

- Date : 2026-11-19
- Statut : accepté et implémenté (PR #4 fusionnée, CI du SHA de PR verte)
- Source : R1 §05.2, ROADMAP §04, DEC-01/DEC-02
- Décision : **conserver les champs AbstractUser, changer seulement la PK en UUID**.

## Contexte

Django exige que le modèle référencé par `AUTH_USER_MODEL` soit créé dans la première migration de son application. Changer de modèle après des migrations opérationnelles entraîne des risques de données, de références et de dépendances. Aucun `migrate` n'avait été lancé lors d'IDR-001.

## Décisions

1. Domaine `apps.identities`, label Django stable `identities` et contrat `AUTH_USER_MODEL = "identities.User"`.
2. `User(AbstractUser)` avec `id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`. Ne pas réutiliser l'email ou le username comme identifiant permanent.
3. **Username unique reste `USERNAME_FIELD`** : pas d'email-only implicite. Le `UserManager` standard de Django est conservé, car les champs structurants d'`AbstractUser` restent inchangés.
4. **Email non unique (hérité d'`AbstractUser`)** pendant ce ticket. La politique d'unicité/normalisation case-insensitive et la connexion par email nécessitent un ADR et des tests dédiés lors d'IDR-003, avant création de données métier. Ne jamais fusionner/associer automatiquement deux comptes sur la seule égalité d'une adresse non vérifiée.
5. Conserver `is_staff`, `is_superuser`, `is_active`, groupes et permissions Django standard. Aucune permission de tenant automatique ; Organizations/Authorization est un domaine séparé.
6. Les références inter-applications utiliseront `settings.AUTH_USER_MODEL` ou `get_user_model()`, jamais `django.contrib.auth.models.User`.
7. Première migration `identities/0001_initial.py` produite par Django, exécutée seulement après activation de `AUTH_USER_MODEL` sur une base vierge.

## Contrats testables

- `get_user_model()._meta.label == "identities.User"`
- UUID4 opaque généré et non éditable ; username unique
- Passwords hachés via `set_password` et `create_user`
- Superuser avec `is_staff=True` et `is_superuser=True`
- `makemigrations --check --dry-run` ne détecte aucune différence
- `migrate --noinput` passe sur base vierge et teste le vrai modèle

## Hors périmètre

- Aucun flux login/signup/verify-email, OAuth, MFA, passkeys ou endpoint REST ; traités par IDR-003 et suivants.
- Aucun changement de base de données vers Neon/PostgreSQL, pas de tenant ni d'identifiant email unique.
- Aucun retrofit de données : ce ticket n'a accès à aucune donnée utilisateur existante.

## Réversibilité

Changer le modèle User après migration n'est pas une opération anodine. Cette décision doit être revue **avant** l'ouverture des données réelles. Toute évolution email-only exigera une migration et un protocole explicites.

## Preuves de validation

- [PR #4 fusionnée](https://github.com/tawounfouet/identity-reference-poc/pull/4)
- [CI initiale de validation du modèle UUID](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44590615891)
- [CI finale avec migration figée et détection de dérive](https://github.com/tawounfouet/identity-reference-poc/actions/runs/44590731215)

## Références

- https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
- https://docs.djangoproject.com/en/5.2/ref/contrib/auth/
