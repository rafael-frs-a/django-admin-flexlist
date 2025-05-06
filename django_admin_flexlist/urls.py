from django.urls import path

from . import views

urlpatterns = [
    path(
        "daf/apps/<str:app_label>/models/<str:model_name>/list_display/",
        views.AppModelListDisplayView.as_view(),
        name="daf_app_model_list_display",
    ),
    path(
        "daf/app_list/",
        views.AppListView.as_view(),
        name="daf_app_list",
    ),
    path(
        "daf/apps/<str:app_label>/model_list/",
        views.AppModelListView.as_view(),
        name="daf_app_model_list",
    ),
]
