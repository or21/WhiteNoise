import datetime
import logging
from server.db_utils import select_keywords_from_db
from dateutil.relativedelta import relativedelta

input_data = {}
logger = logging.getLogger(__name__)
dates_map = {
    'daily': datetime.timedelta(days=-1),
    'weekly': datetime.timedelta(days=-7),
    'monthly': relativedelta(months=-1)
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


# Calculating bid change according to mode and user inputs
def calc_bid_change(mode, roi, avg_position):
    values_change_to = input_data['delicate_mode_bid_adj']
    if mode == 'aggressive':
        calculated_change = ((roi / input_data['target_roi']) - 1) / 1.5
        if calculated_change > input_data['aggressive_mode_caps'][0]:
            x = input_data['aggressive_mode_caps'][0]
        else:
            x = calculated_change
        if calculated_change > input_data['aggressive_mode_caps'][1]:
            y = input_data['aggressive_mode_caps'][1]
        else:
            y = calculated_change
        values_change_to = (x, y)

    if roi > input_data['target_roi']:
        if avg_position > input_data['target_position']:
            return values_change_to[0]
        else:
            return values_change_to[1]
    else:
        if avg_position > input_data['target_position']:
            return values_change_to[0] * -1
        else:
            return values_change_to[1] * -1


# Create the report data according to the design algorithm
def create_keywords_report_data(kws, input_from_user, campaign_avg_position, now):
    global input_data
    input_data = input_from_user
    kws_to_change = []
    db_dependency = {
        'above': [],
        'below': []
    }

    for kw_all in kws:
        kw = Keyword(kw_all['Ad group'], kw_all['Keyword'], kw_all['Keyword ID'], kw_all['Cost'],
                     kw_all['Avg. position'], kw_all['Max. CPC'], kw_all['Match type'], kw_all['All conv. value'],
                     kw_all['Impressions'], kw_all['Ad group ID'])
        message = "Starting to calculate change for {}".format(kw.name).encode('utf-8')
        logger.info(message)
        kw_db_data = select_keywords_from_db(kw.id)
        kw_db_time = ""
        date_to_start_from = ""
        if kw_db_data:
            message = "Found DB record for {}".format(kw.name).encode('utf-8')
            logger.info(message)
            kw_db_time = datetime.datetime.combine(kw_db_data.last_change, datetime.time.min)
            now_ptime = datetime.datetime.strptime(now.strftime("%m/%d/%y"), "%m/%d/%y")
            date_to_start_from = now_ptime + dates_map[input_from_user['report_frequency']]

        if (not kw_db_data) or (kw_db_time < date_to_start_from):
            if kw.avg_position < campaign_avg_position:
                db_dependency['below'].append(kw)
            else:
                db_dependency['above'].append(kw)
            message = "{} kw will be calculated in batch mode".format(kw.name).encode('utf-8')
            logger.info(message)
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
            message = "{} kw was calculated as '{}' mode".format(kw.name, selected_mode).encode('utf-8')
            logger.info(message)

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
            message = "{} kw was calculated as '{}' mode as part of batch calculation".format(kw.name, selected_mode).encode('utf-8')
            logger.info(message)

    return kws_to_change, db_dependency

