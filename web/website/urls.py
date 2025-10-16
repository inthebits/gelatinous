"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns
from web.website.views.characters import CharacterCreateView, CharacterArchiveView

# Override default character creation and deletion with custom versions
urlpatterns = [
    # Custom character creation with GRIM stats
    path("characters/create/", CharacterCreateView.as_view(), name="character-create"),
    
    # Custom archive (instead of delete) - preserves Stack data
    path(
        "characters/delete/<str:slug>/<int:pk>/",
        CharacterArchiveView.as_view(),
        name="character-delete",
    ),
]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns
