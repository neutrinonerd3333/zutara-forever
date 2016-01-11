class UserManager():
    def __init__(self):
        with app.app_context():
            self._users = mongo.db.users
    def get_user(self, uid):
        user = self._users.find_one({'uid': unicode(uid)})
        if not (user == None):
            salt = user['salt']
            return User(uid, salt)
        else:
            return None
    def set_pw(self, uid, newPW):
        user = self._users.find_one({'uid': unicode(uid)})
        if(user != ''):
            salt = os.urandom(32).encode('hex')
            pw = hashlib.sha512(salt + newPW).hexdigest()
            users.update_one({'uid': uid},
                             {'$set':{'pw': pw},
                             '$set':{'salt': salt}})
            return True
        return False
    # verify password for authentication
    # return if the hashes are the same
    def validate_pw(self, uid, pw):
        user = self._users.find_one({'uid': unicode(uid)})
        print ("Finding user...")
        if not(user == None):
            salt = user['salt']
            actual_hash = user['pw']
            test_hash = hashlib.sha512(salt + pw).hexdigest()
            return test_hash == actual_hash
        else:
            return False
    # allows creation of user document with uid and pw in db
    # return: inserted_id of new document
    def create_user(self, uid, pw):
        time = str(datetime.datetime.utcnow())
        salt = os.urandom(32).encode('hex')
        hash = hashlib.sha512(salt + pw).hexdigest()
        user = {'uid': unicode(uid),
            'salt': salt,
            'pw': hash,
            'time': time}
        return self._users.insert_one(user).inserted_id