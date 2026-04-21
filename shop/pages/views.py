from django.views.generic import TemplateView


class About(TemplateView):
    """Представление для страницы про магазин."""

    template_name = 'pages/about.html'


class LoyaltyProgram(TemplateView):
    """Представление для страницы про програму лояльности."""

    template_name = 'pages/loyalty_program.html'
