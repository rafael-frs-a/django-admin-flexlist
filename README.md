# Django Admin FlexList

[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-admin-flexlist/)


A Django package that enables users to customize the admin list view, app index, and dashboard by adding an "Edit layout" button to the page. When clicked, it opens a dialog form that allows users to:

- Toggle the visibility of columns, models, or app sections
- Change their order
- Save their preferred layout for future use

![demo](https://github.com/user-attachments/assets/a98a7fd7-a971-43b0-8811-22f62a4cfe14)

## Setup

### 1. Install the package

To install the package, run:

```shell
$ pip install django-admin-flexlist
```

### 2. Install the app

Add `"django_admin_flexlist"` to `INSTALLED_APPS` in your project's `settings.py` file:

```python
INSTALLED_APPS = [
    # ...
    "django_admin_flexlist",
    # ...
]
```

This allows Django to find the package's migrations and templates.

### 3. Apply migrations

Django Admin FlexList stores each user's layout preferences in the database. To create the necessary table, run:

```shell
$ python manage.py migrate
```

### 4. Include URLs

The package adds endpoints so the JavaScript on the custom template can load the user's preferences into the dialog form and then save the changes to the DB model. To enable those, add the following to your project's `urls.py` file:

```python
urlpatterns = [
    # ...
    path("", include("django_admin_flexlist.urls")),
    # ...
]
```

### 5. Integrate functionality

The package supports customizing two types of Django admin pages: list views and index pages. Index pages include both the main dashboard (showing apps and models) and app-specific dashboards (showing models from a selected app). You can choose to integrate either or both.

#### 5.1 Integrate list view functionality

The customization functionality is introduced by the `FlexListAdmin` class. It mainly implements two changes:

1. Intercepts the `get_list_display` method to apply the user's custom changes
2. Uses a custom change list template that allows the user to change the layout

To use it, extend your admin class as follows:

```python
from django_admin_flexlist import FlexListAdmin

class YourAdmin(FlexListAdmin):
    pass
```

Notice that you can replace `admin.ModelAdmin` with the `FlexListAdmin` class, since the latter already extends that Django class.

You don't need to implement the `get_list_display` method for this feature to work. If you do override it, the customization should still work without any additional changes.

In case your admin class overrides `change_list_template`, you can keep the "Edit layout" feature by extending your custom template as follows:

```html
{% extends "django_admin_flexlist/change_list.html" %}
```

In case your custom template already extends a template other than `"admin/change_list.html"`, you can still keep the feature by adding the following blocks to your file:

```html
{% block extrahead %}
{{ block.super }}
{% include "django_admin_flexlist/change_list_head.html" %}
{% endblock %}

{% block object-tools-items %}
{% include "django_admin_flexlist/change_list_actions.html" %}
{{ block.super }}
{% endblock %}

{% block content %}
{{ block.super }}
{% include "django_admin_flexlist/change_list_content.html" %}
{% endblock %}
```

#### 5.2 Integrate index page functionality

To enable customization on index pages, replace `"django.contrib.admin"` in `settings.py` as follows:

```python
INSTALLED_APPS = [
    # ...
    "django_admin_flexlist.FlexListAdminConfig",  # replaces "django.contrib.admin"
    # ...
]
```

This swaps Django's default admin site class with one from the package, adding an "Edit layout" button and support for customizing the app and model lists. All other admin features remain unchanged.

If you're already using a custom admin site class, extend it like this:

```python
from django_admin_flexlist import FlexListAdminSite

class YourAdminSite(FlexListAdminSite):
    pass
```

If you're overriding `"admin/index.html"` or `"admin/app_index.html"`, you can keep this feature by including the following blocks:

- In your custom index template:

```html
{% block extrastyle %}
{{ block.super }}
{% include "django_admin_flexlist/index_head.html" %}
{% endblock %}

{% block content %}
{{ block.super }}
{% include "django_admin_flexlist/index_actions.html" %}
{% include "django_admin_flexlist/index_content.html" %}
{% endblock %}
```

- In your custom app index template:

```html
{% block extrastyle %}
{{ block.super }}
{% include "django_admin_flexlist/app_index_head.html" %}
{% endblock %}

{% block content %}
{{ block.super }}
{% include "django_admin_flexlist/app_index_actions.html" %}
{% include "django_admin_flexlist/app_index_content.html" %}
{% endblock %}
```

### 6. Custom styling (optional)

The colors used by the components are defined in `django_admin_flexlist/css/colors.css`. You can override those values with your own, as seen in the demo project's `base/static/base/css/colors.css` file, and adjust your templates to use your custom CSS file, as seen in `templates/admin/base_site.html`.

## Limitations

For list views, the implementation expects fields defined in `list_display` or `get_list_display` to be a list or tuple of strings. This simplifies serializing and deserializing changes saved to the DB model. As a result, the following Django implementation of a field isn't supported:

```python
@admin.display(description="Name")
def upper_case_name(obj):
    return f"{obj.first_name} {obj.last_name}".upper()

class PersonAdmin(admin.ModelAdmin):
    list_display = [upper_case_name]
```

# Demo project

To try out the package, you can run the included demo project. Make sure you have [tox](https://tox.wiki/) installed. Then:

1. Clone this repository
2. Run the demo project with:
   ```shell
   $ tox -e py310-django42 -- runserver
   ```
   (Replace `py310-django42` with your desired Python and Django versions - see `tox.ini` for supported combinations)

This will:
- Spin up a Django app with the specified version
- Create a new SQLite database
- Populate it with two demo users:
  - Username: "jon.doe", Password: "jon.doe"
  - Username: "jane.doe", Password: "jane.doe"

The supported Python and Django versions can be found in the `tox.ini` file.
