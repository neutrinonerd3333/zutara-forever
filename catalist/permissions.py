from flask import Flask, render_template, jsonify, \
    request, redirect, url_for, make_response
import flask.ext.security as flask_security

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
admin_unames = ['rmwu', 'txz']


def cmp_permission(perm1, perm2):
    """ Return a positive/0/negative integer when perm1 >/=/< perm2 """
    return perm_list.index(perm1) - perm_list.index(perm2)


def query_permission(user, catalist):
    """
    Gives the permission level a user has for a list.
    "None" represents an anonymous user.
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
    """ Finds the permission the current user has for list *catalist* """
    return query_permission(flask_security.core.current_user, catalist)