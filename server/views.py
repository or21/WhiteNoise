import datetime
import csv
import logging
from flask_apispec import MethodResource
from flask import make_response, render_template, request
from dateutil.relativedelta import relativedelta
from server.db_utils import select_keywords_from_db, write_keyword_to_db
from server.adword_utils import get_campaign_report, get_keywords_report, add_label_to_keyword
from .utils import configure_log


logger = configure_log(logging.INFO, __name__)
kws = []
kws_to_change = []
db_dependency = {}
now = datetime.datetime.now()
campaign_avg_position = 0
date_range = 0
input_from_user = {
    'campaign_name': "",
    'target_roi': 0.0,
    'target_position': 0.0,
    'kw_min_spent': 1.0,
    'delicate_mode_bid_adj': (0.0, 0.0),
    'aggressive_mode_caps': (0.0, 0.0),
    'avg_cpa': 0.0,
    'output_type': "",
    'account': "",
    'report_frequency': ""
}


class Keyword:
    def __init__(self, ad_group, name, kw_id, cost, avg_position, max_cpc, match_type, all_conv, impressions, ad_group_id):
        self.ad_group = ad_group
        self.name = name
        self.id = kw_id
        self.cost = float(float(cost) / 1000000)
        self.avg_position = float(avg_position)
        self.max_cpc = float(float(max_cpc) / 1000000)
        self.match_type = match_type
        self.all_conv_value = float(all_conv)
        self.impressions = float(impressions)
        self.roi = 0.0
        self.bid_change = 0.0
        self.ad_group_id = ad_group_id


class WhiteNoise(MethodResource):
    def get(self):
        return make_response(render_template("WhiteNoise.html"))


# Calculating bid change according to mode and user inputs
def calc_bid_change(mode, roi, avg_position):
    values_change_to = input_from_user['delicate_mode_bid_adj']
    if mode == 'aggressive':
        calculated_change = ((roi / float(input_from_user['target_roi'])) - 1) / 1.5
        if calculated_change > float(input_from_user['aggressive_mode_caps'][0]):
            x = input_from_user['aggressive_mode_caps'][0]
        else:
            x = calculated_change
        if calculated_change > float(input_from_user['aggressive_mode_caps'][1]):
            y = input_from_user['aggressive_mode_caps'][1]
        else:
            y = calculated_change
        values_change_to = (x, y)

    if roi > input_from_user['target_roi']:
        if avg_position > input_from_user['target_position']:
            return values_change_to[0]
        else:
            return values_change_to[1]
    else:
        if avg_position > input_from_user['target_position']:
            return values_change_to[0] * -1
        else:
            return values_change_to[1] * -1


# Create the report data according to the design algorithm
def create_keywords_report_data():
    global kws_to_change, db_dependency, kws
    kws_to_change = []
    input_from_user['target_roi'] = float(input_from_user['target_roi'])
    input_from_user['target_position'] = float(input_from_user['target_position'])
    input_from_user['kw_min_spent'] = float(input_from_user['kw_min_spent'])
    input_from_user['avg_cpa'] = float(input_from_user['avg_cpa'])
    input_from_user['delicate_mode_bid_adj'] = (float(input_from_user['delicate_mode_bid_adj'].split(',')[0]),
                                                float(input_from_user['delicate_mode_bid_adj'].split(',')[1]))
    input_from_user['aggressive_mode_caps'] = (float(input_from_user['aggressive_mode_caps'].split(',')[0]),
                                               float(input_from_user['aggressive_mode_caps'].split(',')[1]))

    for kw_all in kws:
        kw = Keyword(kw_all['Ad group'], kw_all['Keyword'], kw_all['Keyword ID'], kw_all['Cost'],
                     kw_all['Avg. position'], kw_all['Max. CPC'], kw_all['Match type'], kw_all['All conv. value'],
                     kw_all['Impressions'], kw_all['Ad group ID'])
        logger.info("Starting to calculate change for {}".format(kw.name))
        kw_db_data = select_keywords_from_db(kw.id)
        kw_db_time = ""
        date_to_start_from = ""
        if len(kw_db_data) > 0:
            logger.info("Found DB record for {}".format(kw.name))
            kw_db_time = datetime.datetime.combine(kw_db_data[0][0], datetime.time.min)
            now_ptime = datetime.datetime.strptime(now.strftime("%m/%d/%y"), "%m/%d/%y")
            if input_from_user['report_frequency'] == 'daily':
                date_to_start_from = now_ptime + datetime.timedelta(days=-1)
            elif input_from_user['report_frequency'] == 'weekly':
                date_to_start_from = now_ptime + datetime.timedelta(days=-7)
            else:
                date_to_start_from = now_ptime + relativedelta(months=-1)

        if len(kw_db_data) == 0 or kw_db_time < date_to_start_from:
            if kw.avg_position < campaign_avg_position:
                db_dependency['below'].append(kw)
            else:
                db_dependency['above'].append(kw)
            logger.info("{} kw will be calculated in batch mode".format(kw.name))
        else:
            if kw.cost < input_from_user['kw_min_spent']:
                continue
            kw.roi = kw.all_conv_value / kw.cost
            roi_min = input_from_user['target_roi'] - input_from_user['target_roi'] * 0.1
            roi_max = input_from_user['target_roi'] + input_from_user['target_roi'] * 0.1
            if float(roi_max) > float(kw.roi) > float(roi_min):
                continue
            if 1.5 > kw.avg_position > 1.0 and kw.roi > input_from_user['target_roi']:
                continue

            if kw.cost > (3 * input_from_user['avg_cpa']):
                selected_mode = "aggressive"
            else:
                selected_mode = "delicate"

            kw.bid_change = float(calc_bid_change(selected_mode, kw.roi, kw.avg_position))
            kws_to_change.append(kw)
            logger.info("{} kw was calculated as '{}' mode".format(kw.name, selected_mode))

    for location, keywords in db_dependency.items():
        all_cost = sum([kw.cost for kw in keywords])
        if all_cost > 0:
            all_kw_roi = sum([kw.all_conv_value for kw in keywords]) / all_cost
        else:
            all_kw_roi = 0
        all_impressions = sum([kw.impressions for kw in keywords])
        if all_impressions > 0:
            all_position = sum([kw.impressions * kw.avg_position for kw in keywords]) / all_impressions
        else:
            all_position = 0
        if all_cost > (3 * input_from_user['avg_cpa']):
            selected_mode = "aggressive"
        else:
            selected_mode = "delicate"
        group_bid_change = calc_bid_change(selected_mode, all_kw_roi, all_position)
        for kw in keywords:
            kw.bid_change = group_bid_change
            logger.info("{} kw was calculated as '{}' mode as part of batch calculation".format(kw.name, selected_mode))


class KeywordsBidSuggestions(MethodResource):
    def post(self):
        global input_from_user, campaign_avg_position, date_range, kws, db_dependency
        kws = []
        db_dependency = {
            'above': [],
            'below': []
        }
        for key in request.values.keys():
            if key in input_from_user.keys() and request.values[key] != "":
                input_from_user[key] = request.values[key]
        if input_from_user['report_frequency'] == 'daily':
            date_range = "YESTERDAY"
        elif input_from_user['report_frequency'] == 'weekly':
            date_range = "LAST_7_DAYS"
        else:
            date_range = "LAST_30_DAYS"

        report = get_keywords_report(input_from_user['campaign_name'], date_range)
        report_as_dict = csv.DictReader(report.split('\n'))
        for row in report_as_dict:
            kws.append(row)

        if len(kws) == 0:
            response = make_response(render_template("campaign_not_found.html"))
            response.status_code = 404
            return response

        campaign_avg_position = float(get_campaign_report(input_from_user['campaign_name'], date_range, ['AveragePosition']).split('\n')[1])
        create_keywords_report_data()
        return_data = []

        for kw_data in kws_to_change + db_dependency['above'] + db_dependency['below']:
            if 'exaction' in input_from_user['output_type']:
                if kw_data.bid_change > 0:
                    change = 'increase'
                else:
                    change = 'decrease'
                add_label_to_keyword(kw_data, change + " " + now.strftime("%m/%d"))
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
