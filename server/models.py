from .application import db


class Keywords(db.Model):
    __tablename__ = 'keywords'

    kw_id = db.Column(db.String, primary_key=True)
    kw_name = db.Column(db.String)
    last_change = db.Column(db.Date)
    campaign_name = db.Column(db.String)
