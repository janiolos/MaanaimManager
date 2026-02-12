from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import AuditLog
from .utils import get_evento_atual


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_log(request):
            self._log_request(request, response)
        return response

    def _should_log(self, request):
        path = request.path
        return not path.startswith(("/static/", "/media/"))

    def _log_request(self, request, response):
        try:
            user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
            view_name = ""
            resolver_match = getattr(request, "resolver_match", None)
            if resolver_match:
                view_name = resolver_match.view_name or ""
            ip_address = self._get_client_ip(request)
            AuditLog.objects.create(
                user=user,
                method=request.method,
                path=request.get_full_path(),
                view_name=view_name,
                status_code=response.status_code,
                ip_address=ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except Exception:
            # Avoid breaking the request flow if logging fails.
            return

    def _get_client_ip(self, request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class EventoSelecionadoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            if not self._is_public_path(path):
                if get_evento_atual(request) is None:
                    return redirect(reverse("core:selecionar_evento"))
        return self.get_response(request)

    def _is_public_path(self, path):
        public_prefixes = [
            "/login/",
            "/logout/",
            "/admin/",
            "/core/evento/",
            "/api/v1/",
            "/static/",
            "/media/",
        ]
        return any(path.startswith(prefix) for prefix in public_prefixes)


class InatividadeLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout_seconds = getattr(settings, "INACTIVITY_TIMEOUT_SECONDS", 30 * 60)

    def __call__(self, request):
        if request.user.is_authenticated:
            if not self._is_public_path(request.path):
                now_ts = int(timezone.now().timestamp())
                last_activity_ts = request.session.get("last_activity_ts")
                if last_activity_ts is not None:
                    if now_ts - last_activity_ts > self.timeout_seconds:
                        logout(request)
                        messages.info(
                            request,
                            "Sua sessao expirou por inatividade. Faca login novamente.",
                        )
                        return redirect(settings.LOGIN_URL)
                request.session["last_activity_ts"] = now_ts
        return self.get_response(request)

    def _is_public_path(self, path):
        public_prefixes = [
            "/login/",
            "/logout/",
            "/admin/",
            "/core/evento/",
            "/api/v1/",
            "/static/",
            "/media/",
        ]
        return any(path.startswith(prefix) for prefix in public_prefixes)
