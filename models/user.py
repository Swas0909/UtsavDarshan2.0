from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_json):
        self.user_json = user_json

    def get_id(self):
        return str(self.user_json.get('_id'))
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    @property
    def name(self):
        return self.user_json.get('name')
    
    @property
    def email(self):
        return self.user_json.get('email')
    
    @property
    def profile_pic(self):
        return self.user_json.get('profile_pic')
