from .models import Permission

def best_scope(user, resource: str, action: str) -> str | None:
    if not user.is_authenticated:
        return None
    qs = Permission.objects.filter(
        permission_roles__role__role_users__user=user,
        resource=resource,
        action=action,
    ).values_list("scope", flat=True).distinct()
    scopes = set(qs)
    if "ALL" in scopes:
        return "ALL"
    if "OWN" in scopes:
        return "OWN"
    return None
