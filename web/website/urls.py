"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns
from web.website.views.characters import (
    CharacterCreateView, 
    CharacterArchiveView,
    StaffCharacterListView,
    OwnerOnlyCharacterDetailView,
    OwnerOnlyCharacterUpdateView
)
from web.website.views.channels import StaffChannelListView, StaffChannelDetailView
from web.website.views.accounts import TurnstileAccountCreateView
from web.website.views.discourse_sso import discourse_sso
from web.website.views.discourse_logout import discourse_logout

# Override default character creation, account registration, and other views
urlpatterns = [
    # Discourse SSO endpoint
    path("sso/discourse/", discourse_sso, name="discourse-sso"),
    
    # Discourse logout endpoint (redirect target from Discourse logout)
    path("sso/discourse/logout/", discourse_logout, name="discourse-logout"),
    
    # Custom account registration with Cloudflare Turnstile
    path("auth/register", TurnstileAccountCreateView.as_view(), name="register"),
    
    # Custom character creation with GRIM stats
    path("characters/create/", CharacterCreateView.as_view(), name="character-create"),
    
    # Custom archive (instead of delete) - preserves Stack data
    path(
        "characters/delete/<str:slug>/<int:pk>/",
        CharacterArchiveView.as_view(),
        name="character-delete",
    ),
    
    # Owner-only character detail and update (staff can view/edit all)
    path(
        "characters/detail/<str:slug>/<int:pk>/",
        OwnerOnlyCharacterDetailView.as_view(),
        name="character-detail",
    ),
    path(
        "characters/update/<str:slug>/<int:pk>/",
        OwnerOnlyCharacterUpdateView.as_view(),
        name="character-update",
    ),
    
    # Staff-only character list (replaces default)
    path("characters/", StaffCharacterListView.as_view(), name="characters"),
    
    # Staff-only channel views (replaces defaults)
    path("channels/", StaffChannelListView.as_view(), name="channels"),
    path("channels/<str:slug>/", StaffChannelDetailView.as_view(), name="channel-detail"),
]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns
