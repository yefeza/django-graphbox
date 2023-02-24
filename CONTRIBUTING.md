# Contributing to Django Graphbox

There are many ways to contribute to Django Graphbox. Here are some of them:

- [Contributing to Django Graphbox](#contributing-to-django-graphbox)
  - [Clone the repository](#clone-the-repository)
  - [Create a virtual environment](#create-a-virtual-environment)
  - [Activate the virtual environment](#activate-the-virtual-environment)
  - [Install the dependencies](#install-the-dependencies)
  - [Create a Django example project](#create-a-django-example-project)
  - [Add Django Graphbox to the path](#add-django-graphbox-to-the-path)
  - [Add Graphene Django to the installed apps](#add-graphene-django-to-the-installed-apps)
- [Documentation style](#documentation-style)
- [Gitflow Workflow](#gitflow-workflow)
- [Reporting Bugs](#reporting-bugs)
- [Writing Documentation](#writing-documentation)
- [Writing Code](#writing-code)
- [Writing Tests](#writing-tests)
- [Submitting Patches](#submitting-patches)
- [Submitting Feedback](#submitting-feedback)
- [License](#license)
- [Code of Conduct](#code-of-conduct)
- [Credits](#credits)

## Clone the repository

```bash
git clone https://github.com/yefeza/django-graphbox.git && cd django-graphbox
```

## Create a virtual environment

```bash
python -m venv env
```

## Activate the virtual environment

```bash
source env/bin/activate
```

## Install the dependencies

```bash
pip install -r requirements.txt
```

## Create a Django example project

```bash
django-admin startproject example-local
```
Note that the project name must be `example-local` because the `example` project is already in the repository and `example-local` is in the `.gitignore` file.

## Add Django Graphbox to the path

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

## Add Graphene Django to the installed apps

```python
# example/example/settings.py
INSTALLED_APPS = [
    ...
    'graphene_django',
]
```
Use the quickstart guide to get started with Django Graphbox.

# Documentation style

Django Graphbox uses docstrings to document the code. The docstrings are written in [Google Style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). The documentation is generated using [Sphinx](https://www.sphinx-doc.org/en/master/).

# Gitflow Workflow

Django Graphbox uses the [Gitflow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow). This means that all development happens in the `develop` branch. The `main` branch only accepts merges from the `release` branch. Hotfixes are merged directly into `main` and `develop`.

The `develop` branch is the default branch. When you submit a pull request, please make sure that you are submitting it against the `develop` branch.

The `main` branch only accepts merges from the `release` branch. Hotfixes are merged directly into `main` and `develop`. Only maintainers can merge into the `main` branch. If you would like to submit a hotfix, please [submit a pull request](#submitting-patches) with your changes and it will be reviewed and merged by a maintainer.

# Reporting Bugs

Before reporting a bug, please check the [issue tracker](
    [github.com/yefeza/](https://github.com/yefeza/django-graphbox/issues)) to see if it has already been reported. If it has, please add a comment to the existing issue instead of creating a new one.

If you are unable to find an existing issue, please [create a new one](
    [github.com/yefeza/](https://github.com/yefeza/django-graphbox/issues/new/)) Please include as much information as possible. Ideally, you should include a [minimal, complete, and verifiable example.](http://stackoverflow.com/help/mcve)
    
# Writing Documentation

Documentation is an important part of any project. If you find a typo or an error in the documentation, please [submit a pull request](#submitting-patches) to fix it.

# Writing Code

If you would like to contribute code to Django Graphbox, please [submit a pull request](#submitting-patches) with your changes. Please make sure that your code is well tested and documented.

Code can be classified into this categories:

- Bug fixes
- Functional new features
- GUI new features
- Documentation
- Tests

Please include the appropriate label in your pull request.

# Writing Tests

Tests are an important part of any project. If you would like to contribute tests to Django Graphbox, please [submit a pull request](#submitting-patches) with your changes. Please make sure that your code is well tested and documented.

# Submitting Patches

If you would like to contribute code to Django Graphbox, please [submit a pull request](#submitting-patches) with your changes. Please make sure that your code is well tested and documented and use the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

# Submitting Feedback

If you have any feedback, please [submit a new issue](
    [github.com/yefeza/](https://github.com/yefeza/django-graphbox/issues/new/)).

# License

Django Graphbox is licensed under the [MIT License](LICENSE).

# Code of Conduct

Everyone interacting in the Django Graphbox project’s codebases, issue trackers, chat rooms and mailing lists is expected to follow the [code of conduct](CODE_OF_CONDUCT.md).

# Credits

Django Graphbox was created by [Yeison M. Fernandez Zarate](
    [github.com/yefeza/](https://github.com/yefeza/)).

[//]: # (This README was helpfully generated by GitHub Copilot) 
[//]: # (https://copilot.github.com)
