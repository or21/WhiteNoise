import datetime
import csv
import logging
from flask_apispec import MethodResource
from flask import make_response, render_template, request
from server.db_utils import write_keyword_to_db
from server.adword_utils import get_campaign_report, get_keywords_report, add_label_to_keyword
from .utils import handle_user_input
from .bid_calculations import create_keywords_report_data


logger = logging.getLogger(__name__)
kws = []
kws_to_change = []
keywords_bids_as_group = {}
now = datetime.datetime.now()
campaign_avg_position = 0
date_range = 0
dates_map = {
    'daily': 'YESTERDAY',
    'weekly': 'LAST_7_DAYS',
    'monthly': 'LAST_30_DAYS'
}


class WhiteNoise(MethodResource):
    def get(self):
        return make_response(render_template("WhiteNoise.html"))


class KeywordsBidSuggestions(MethodResource):
    def post(self):
        global campaign_avg_position, date_range, kws, keywords_bids_as_group, kws_to_change
        kws = []
        input_from_user = handle_user_input(request)
        date_range = dates_map[input_from_user['report_frequency']]

        kws_report = get_keywords_report(input_from_user['campaign_name'], date_range)
        report_as_dict = csv.DictReader(kws_report.split('\n'))
        for row in report_as_dict:
            kws.append(row)

        if len(kws) == 0:
            response = make_response(render_template("campaign_not_found.html"))
            response.status_code = 404
            return response

        campaign_avg_position = float(get_campaign_report(input_from_user['campaign_name'], date_range, ['AveragePosition']).split('\n')[1])
        kws_to_change, keywords_bids_as_group = create_keywords_report_data(kws, input_from_user, campaign_avg_position, now)

        return_data = []
        for kw_data in kws_to_change + keywords_bids_as_group['above'] + keywords_bids_as_group['below']:
            if 'exaction' in input_from_user['output_type']:
                if kw_data.bid_change > 0:
                    change = 'increase'
                else:
                    change = 'decrease'
                add_label_to_keyword(kw_data, "{} {}".format(change, now.strftime("%m/%d")))
            write_keyword_to_db(kw_data, input_from_user['campaign_name'], now.strftime("%m/%d/%y"))
            return_data.append([input_from_user['campaign_name'],
                                kw_data.ad_group,
                                kw_data.name,
                                kw_data.id,
                                kw_data.match_type,
                                kw_data.cost,
                                kw_data.avg_position,
                                round(kw_data.roi, 2),
                                input_from_user['target_roi'],
                                round(kw_data.max_cpc, 2),
                                round(kw_data.bid_change, 2),
                                round((kw_data.max_cpc + kw_data.max_cpc * (round(kw_data.bid_change, 2) / 100)), 2)])
        return make_response(render_template("Keywords_data_output.html", kws_to_change=return_data))
