from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Default home -> redirect to dashboard
    path('', RedirectView.as_view(url='/accounts/dashboard/', permanent=False)),

    # App routes
    path('accounts/', include('apps.accounts.urls')),
    path('classroom/', include('apps.classroom.urls')),
    path('quizes/', include('apps.quizes.urls')),
]

# Serve media + static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
