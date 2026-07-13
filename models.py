from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, first_name, last_name, user_tag, password_hash, role, contributor):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self._user_tag = user_tag
        self.password_hash = password_hash
        self.role = role
        self.contributor = bool(contributor)

    @property
    def user_tag(self):
        return f'@{self._user_tag}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_contributing(self):
        return self.contributor

    @classmethod
    def from_row(cls, row):
        return cls(
            row['id'], row['first_name'], row['last_name'], row['user_tag'],
            row['password_hash'], row['role'], row['contributor'],
        )
