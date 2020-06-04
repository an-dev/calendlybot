from django.conf.urls import url
from django.contrib import admin, sitemaps
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, reverse
from django.views.generic import TemplateView

from web.core.urls import core_map_paths


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return core_map_paths

    def location(self, item):
        return reverse(item)


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('cp/', admin.site.urls),
    path('', include('web.core.urls')),
    path('blog/', include('web.blog.urls')),
    path('subscribe/', include('web.payments.urls'), name='subscribe'),
    url(r'^markdownx/', include('markdownx.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),),
]
