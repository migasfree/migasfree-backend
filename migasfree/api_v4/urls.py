# -*- coding: utf-8 *-*

from django.urls import re_path

from .views import (
    api_v4, computer_label, ServerInfoView, RepositoriesUrlTemplateView,
    get_key_repositories, get_computer_info,
)


urlpatterns = [
    re_path(r'^api/$', api_v4, name='api_v4'),
    re_path(
        r'^computer/(?P<uuid>.+)/label/$',
        computer_label,
        name='computer_label',
    ),
    re_path(
        r'^get_key_repositories/$',
        get_key_repositories,
        name='get_key_repositories'
    ),
    re_path(
        r'^get_computer_info/$',
        get_computer_info,
        name='get_computer_info'
    ),
    re_path(r'^api/v1/public/repository-url-template/', RepositoriesUrlTemplateView.as_view()),
    re_path(r'^api/v1/public/server/info/', ServerInfoView.as_view()),
]
