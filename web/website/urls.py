"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns
from web.website.views import characters

# Override Evennia's default CharacterCreateView with our GRIM-enabled version
# This provides a smart single-page experience that handles both first-time
# character creation and post-death respawn/flash cloning.
urlpatterns = [
    path("characters/create/", characters.CharacterCreateView.as_view(), name="character-create"),
]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns
