from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    """Представление для страницы про магазин."""

    template_name = 'pages/about.html'


class LoyaltyProgram(TemplateView):
    """Представление для страницы про програму лояльности."""

    template_name = 'pages/loyalty_program.html'


def page_not_found(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request):
    return render(request, 'pages/500.html', status=500)
