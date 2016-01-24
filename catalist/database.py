from catalist import app, db
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required
import flask.ext.security as flask_security


# **********************************************************
# Flask-Security and MongoEngine Setup
# **********************************************************


# Maximum lengths for different things.
key_max_len = 32
val_max_len = 1024
entry_title_max_len = 128
list_title_max_len = 128


class Role(db.Document, RoleMixin):
    """ A class for user roles (e.g. user, admin, ...) """
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    """ A class for users. Can have any/none of these attributes. """
    firstname = db.StringField(max_length=40)
    lastname = db.StringField(max_length=40)
    email = db.StringField(max_length=100, unique=True)
    uid = db.StringField(max_length=40, unique=True)
    password = db.StringField(max_length=255)  # because this is a hash
    active = db.BooleanField(default=True)  # set False for user confirmation
    confirmed_at = db.DateTimeField()
    preferred_theme = db.IntField(maximum=10, required=True, default=0)

    # we want to remove long-inactive users
    last_active = db.DateTimeField(required=True)

    # users the current user has somehow interacted with
    acquaintances = db.ListField(db.ReferenceField('self'), default=[])

    # my lists
    my_custom_lists = db.ListField(db.ReferenceField('Catalist'), default=[])
    anti_my_lists = db.ListField(db.ReferenceField('Catalist'), default=[])

    roles = db.ListField(db.ReferenceField(Role), default=[])


class CatalistKVP(db.EmbeddedDocument):
    """ A class for individual key-value pairs in our Catalist entries """
    # id is implicit in mongoengine, but we want to
    # share kvpid's across (CatalistEntry)s
    kvpid = db.StringField(max_length=40)
    key = db.StringField(max_length=key_max_len, default="")
    value = db.StringField(max_length=val_max_len, default="")


class CatalistEntry(db.EmbeddedDocument):
    """ A class for the entries in our Catalists """
    title = db.StringField(max_length=entry_title_max_len, default="")
    contents = db.EmbeddedDocumentListField(CatalistKVP, default=[])
    score = db.IntField(default=0)
    upvoters = db.ListField(db.ReferenceField(User), default=[])
    downvoters = db.ListField(db.ReferenceField(User), default=[])


class Catalist(db.Document):
    """ A class for our lists (Catalists :P) """

    # METADATA

    listid = db.StringField(max_length=40, unique=True)
    created = db.DateTimeField(required=True)  # when list was created

    # should be implemented as RefField(User)
    creator = db.StringField(max_length=40)

    # this is actually "last modified", but name persists for backwards-compat
    last_visited = db.DateTimeField(required=True)

    # CONTENTS

    title = db.StringField(max_length=list_title_max_len,
                           default="untitled list")
    contents = db.EmbeddedDocumentListField(CatalistEntry, default=[])

    # PERMISSIONS

    # the permission the public has with the list
    public_level = db.StringField(choices=["edit", "view", "none"],
                                  default="edit")

    # people with own/edit/view permission
    owners = db.ListField(db.ReferenceField(User))
    editors = db.ListField(db.ReferenceField(User))
    viewers = db.ListField(db.ReferenceField(User))

    # people who manually add the list to "my lists"
    # pls don't judge my name choice
    mylisters = db.ListField(db.ReferenceField(User))


# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)
