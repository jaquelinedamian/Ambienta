# middleware.py - Middleware para forçar HTTP em desenvolvimento

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponse

class ForceHTTPMiddleware:
    """
    Middleware para forçar HTTP em desenvolvimento e evitar upgrade para HTTPS
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Em desenvolvimento, intercepta tentativas HTTPS
        if settings.DEBUG:
            # Se a requisição chegar como HTTPS, redireciona para HTTP
            if request.is_secure():
                http_url = request.build_absolute_uri().replace('https://', 'http://').replace(':8000', ':8080')
                return HttpResponsePermanentRedirect(http_url)
            
            # Adiciona cabeçalhos que forçam HTTP desde o início
            request.META['wsgi.url_scheme'] = 'http'
            if 'HTTP_X_FORWARDED_PROTO' in request.META:
                request.META['HTTP_X_FORWARDED_PROTO'] = 'http'
                
        response = self.get_response(request)
        
        # Apenas em modo DEBUG - adiciona cabeçalhos de resposta
        if settings.DEBUG:
            # Remove todos os cabeçalhos relacionados a HTTPS
            response['Strict-Transport-Security'] = 'max-age=0; includeSubDomains; preload'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            
            # Evita upgrade para HTTPS
            if 'Upgrade-Insecure-Requests' in response:
                del response['Upgrade-Insecure-Requests']
                
            # Remove qualquer política que force HTTPS
            if 'Content-Security-Policy' in response:
                csp = response['Content-Security-Policy']
                if 'upgrade-insecure-requests' in csp:
                    response['Content-Security-Policy'] = csp.replace('upgrade-insecure-requests;', '').replace('upgrade-insecure-requests', '')
                
        return response