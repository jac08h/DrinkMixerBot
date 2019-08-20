from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    date_started = db.Column(db.DateTime)
    date_last_used = db.Column(db.DateTime)

    def update_time(self, time):
        self.date_last_used = time

    def __repr__(self):
        return f'User <{self.id}>'