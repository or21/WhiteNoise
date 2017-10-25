from server import db
from .application import Keywords


def write_keyword_to_db(kw_data, campaign_name, date):
    kw_to_insert = Keywords(kw_id=kw_data.id, kw_name=kw_data.name, last_change=date, campaign_name=campaign_name)
    db.session.merge(kw_to_insert)
    db.session.commit()


def select_keywords_from_db(keyword_id):
    kw_result = Keywords.query.filter_by(kw_id=keyword_id).first()
    return kw_result
