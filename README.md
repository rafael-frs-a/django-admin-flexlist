# Django Admin FlexList

A Django package that enhances the admin interface by providing customizable list views. This package enables users to customize the Django admin list view by adding an "Edit layout" button to the page. When clicked, it opens a dialog form that allows users to:

- Toggle the visibility of list columns
- Change the order of columns
- Save their preferred layout for future use

![demo](https://github.com/user-attachments/assets/f0fcac7f-543f-4dc5-9c56-975f494a155f)

## Setup

### 1. Installation

To install the package, run:

```shell
$ pip install django-admin-flexlist
```

### 2. Install app

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

### 5. Extend the admin class

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

## Limitations

The implementation expects fields defined in `list_display` or `get_list_display` to be a list or tuple of strings. This simplifies serializing and deserializing changes saved to the DB model. As a result, the following Django implementation of a field isn't supported:

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
