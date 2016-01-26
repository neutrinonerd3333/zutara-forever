"""
    catalist.permissions
    ~~~~~~~~~~~~~~~~~~~~

    This module implements handy utilities for working
    with user permissions.

    :copyright: (c) 2016 Rachel Wu, Tony Zhang
    :license: lol don't steal this code pls
"""

from flask import Flask
import flask.ext.security as flask_security

# **********************************************************
# Permissions
# **********************************************************

#: A list of all permission levels, from lowest to highest.
#: The levels:
#:
#: #. none  -- no permission
#: #. view  -- permission to view a list
#: #. edit  -- permission to edit a list
#: #. own   -- permission to change permission for a list
#: #. admin -- can do anything
perm_list = ["none", "view", "edit", "own", "admin"]

#: Currently admins are determined by residency on this list.
#: Hacky, I know. .__.
admin_unames = ['zutara']


def cmp_permission(perm1, perm2):
    """ Return a positive/0/negative integer when perm1 >/=/< perm2. """
    return perm_list.index(perm1) - perm_list.index(perm2)


def query_permission(user, catalist):
    """
    Give the permission level `user` has for a list `catalist`.
    Handles anonymous users.
    """
    # handle anonymous users
    if user.is_anonymous:
        return catalist.public_level

    if user.uid in admin_unames:
        return "admin"
    elif user in catalist.owners:
        return "own"
    elif cmp_permission(catalist.public_level, "edit") >= 0 or \
            user in catalist.editors:
        return "edit"
    elif cmp_permission(catalist.public_level, "view") >= 0 or \
            user in catalist.viewers:
        return "view"
    return "none"


def query_cur_perm(catalist):
    """ Find the permission the current user has for list *catalist* """
    return query_permission(flask_security.core.current_user, catalist)
