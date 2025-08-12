from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rbac.auth_required import RequireAuthenticated401
from rbac.permissions import require_permission
from rest_framework.permissions import IsAuthenticated

# Притворимся, что это данные из БД
MOCK_ARTICLES = [
    {"id": 1, "title": "My note", "owner_id": 2},
    {"id": 2, "title": "Team doc", "owner_id": 999},
    {"id": 3, "title": "Public post", "owner_id": 42},
]

class ArticleList(APIView):
    permission_classes = [RequireAuthenticated401, require_permission("articles", "read")]
    def get(self, request):
        return Response(MOCK_ARTICLES)

class ArticleUpdate(APIView):
    permission_classes = [RequireAuthenticated401, require_permission("articles", "update")]
    def patch(self, request, article_id: int):
        # найдём «объект»
        obj = next((a for a in MOCK_ARTICLES if a["id"] == article_id), None)
        if not obj:
            return Response({"detail": "Not found"}, status=404)

        # если право только OWN — проверим владельца
        if request.rbac["scope"] == "OWN" and obj["owner_id"] != request.user.id:
            return Response({"detail": "Forbidden by scope OWN"}, status=403)

        title = request.data.get("title")
        if title:
            obj["title"] = title
        return Response({"updated": obj})
