from django.urls import path

from . import views

urlpatterns = [
    path(
        "daf/apps/<str:app_label>/models/<str:model_name>/list_display/",
        views.AppModelListDisplayView.as_view(),
        name="daf_app_model_list_display",
    ),
]
