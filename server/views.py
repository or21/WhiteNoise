from flask_apispec import MethodResource, use_kwargs, marshal_with
from flask import make_response, render_template, request
import psycopg2
from googleads import adwords
import os
import csv
import datetime
from dateutil.relativedelta import relativedelta


def db_connect():
    try:
        conn_string = "host='localhost' dbname='WhiteNoise' user='postgres' password='Aa123456' port=5000"
        print("Connecting to database\n	{}".format(conn_string))
        return psycopg2.connect(conn_string)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


conn = db_connect()
PAGE_SIZE = 100
kws = []
kws_to_change = []
input_from_user = {
    'campaign_name': "[S] Shares - NL",
    'target_roi': 150,
    'target_position': 2.0,
    'kw_min_spent': 1,
    'delicate_mode_bid_adj': "7, 15",
    'aggressive_mode_caps': "15, 30",
    'avg_cpa': 3,
    'output_type': "",
    'account': "",
    'report_frequency': ""
}
db_dependency = {
    'above': [],
    'below': []
}
campaign_avg_position = ""


class Keyword:
    def __init__(self, ad_group, name, kw_id, cost, avg_position, max_cpc, match_type, all_conv, impressions):
        self.ad_group = ad_group
        self.name = name
        self.id = kw_id
        self.cost = cost
        self.avg_position = avg_position
        self.max_cpc = max_cpc
        self.match_type = match_type
        self.all_conv_value = all_conv
        self.impressions = impressions
        self.roi = ""
        self.bid_change = ""


class WhiteNoise(MethodResource):
    def get(self):
        return make_response(render_template("WhiteNoise.html"))


def select_from_db(keyword_id):
    command = "SELECT * FROM keywords where kw_id = '{}'".format(keyword_id)
    db_cursor = conn.cursor()
    db_cursor.execute(command)
    rows = db_cursor.fetchall()
    return rows


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
                     kw_all['Impressions'])
        if kw.cost and kw.cost.isdigit() and float(kw.cost) != 0 and kw.avg_position and kw.max_cpc:
            kw.cost = float(kw.cost)
            kw.avg_position = float(kw.avg_position)
            kw.max_cpc = float(kw.max_cpc)
            kw.roi = float(kw.all_conv_value) / (kw.cost / 1000000)
            roi_min = input_from_user['target_roi'] - input_from_user['target_roi'] * 0.1
            roi_max = input_from_user['target_roi'] + input_from_user['target_roi'] * 0.1
            if roi_max > kw.roi > roi_min:
                continue
            if (kw.cost / 1000000) < input_from_user['kw_min_spent']:
                continue
            if 1.5 > kw.avg_position > 1.0 and kw.roi > input_from_user['target_roi']:
                continue

            if kw.cost > (3 * input_from_user['avg_cpa']):
                selected_mode = "aggressive"
            else:
                selected_mode = "delicate"

            kw.bid_change = float(calc_bid_change(selected_mode, kw.roi, kw.avg_position))
            kws_to_change.append(kw)
        else:
            kw_db_data = select_from_db(kw.id)
            if len(kw_db_data) > 0:
                kw_db_time = datetime.datetime.combine(kw_db_data[0][1], datetime.time.min)
                now = datetime.datetime.now()
                date_1 = datetime.datetime.strptime(now.strftime("%m/%d/%y"), "%m/%d/%y")
                if input_from_user['report_frequency'] == 'daily':
                    end_date = date_1 + datetime.timedelta(days=-1)
                elif input_from_user['report_frequency'] == 'weekly':
                    end_date = date_1 + datetime.timedelta(days=-7)
                else:
                    end_date = date_1 + relativedelta(months=-1)

                if kw_db_time < end_date:
                    if kw.avg_position < campaign_avg_position:
                        db_dependency['below'].append(kw)
                    else:
                        db_dependency['above'].append(kw)

    for location, kws in db_dependency.items():
        all_cost = sum([kw.cost for kw in kws])
        if all_cost > 0:
            all_kw_roi = sum([kw.all_conv_value for kw in kws]) / all_cost
        else:
            all_kw_roi = 0
        all_impressions = sum([kw.impression for kw in kws])
        if all_impressions > 0:
            all_position = sum([kw.impressions * kw.avg_position for kw in kws])
        else:
            all_position = 0
        if all_cost > (3 * input_from_user['avg_cpa']):
            selected_mode = "aggressive"
        else:
            selected_mode = "delicate"
        group_bid_change = calc_bid_change(selected_mode, all_kw_roi, all_position)
        for kw in kws:
            kw.bid_change = group_bid_change


def get_kw_perf_report(client):
    global kws
    kws = []
    report_downloader = client.GetReportDownloader(version='v201708')
    if input_from_user['report_frequency'] == 'daily':
        date_range = "YESTERDAY"
    elif input_from_user['report_frequency'] == 'weekly':
        date_range = "LAST_7_DAYS"
    else:
        date_range = "LAST_30_DAYS"
    report = {
        'reportName': "{} KEYWORDS_PERFORMANCE_REPORT".format(date_range),
        'dateRangeType': date_range,
        'reportType': 'KEYWORDS_PERFORMANCE_REPORT',
        'downloadFormat': 'CSV',
        'selector': {
            'fields': ['CampaignId', 'CampaignName', 'AdGroupId', 'AdGroupName', 'Id', 'CpcBid', 'KeywordMatchType',
                       'Criteria', 'AveragePosition', 'Cost', 'AllConversionValue', 'Impressions'],
            'predicates': {
                'field': 'CampaignName',
                'operator': 'EQUALS',
                'values': [input_from_user['campaign_name']]
            }
        }
    }

    with open('./report.txt', mode='w', encoding='utf8') as infile:
        report_downloader.DownloadReport(
            report, infile, skip_report_header=True, skip_column_header=False,
            skip_report_summary=True, include_zero_impressions=True)
    in_txt = csv.reader(open('./report.txt'), delimiter=',')
    out_csv = csv.writer(open('./report.csv', 'w'))
    for line in in_txt:
        out_csv.writerow(line)
    with open('./report.csv', mode='r', encoding='utf8') as data:
        reader = csv.DictReader(data)
        for row in reader:
            kws.append(row)


def get_campaign_avg_position_report(client):
    report_downloader = client.GetReportDownloader(version='v201708')

    if input_from_user['report_frequency'] == 'daily':
        date_range = "YESTERDAY"
    elif input_from_user['report_frequency'] == 'weekly':
        date_range = "LAST_7_DAYS"
    else:
        date_range = "LAST_30_DAYS"
    report = {
        'reportName': "{} KEYWORDS_PERFORMANCE_REPORT".format(date_range),
        'dateRangeType': date_range,
        'reportType': 'CAMPAIGN_PERFORMANCE_REPORT',
        'downloadFormat': 'CSV',
        'selector': {
            'fields': ['AveragePosition'],
            'predicates': {
                'field': 'CampaignName',
                'operator': 'EQUALS',
                'values': [input_from_user['campaign_name']]
            }
        }
    }

    report_results = report_downloader.DownloadReportAsString(
            report, skip_report_header=True, skip_column_header=True,
            skip_report_summary=True, include_zero_impressions=True)
    return report_results


class KeywordsBidSuggestions(MethodResource):
    def post(self):
        global input_from_user, campaign_avg_position
        for key in request.values.keys():
            if key in input_from_user.keys() and request.values[key] != "":
                input_from_user[key] = request.values[key]
        adwords_client = adwords.AdWordsClient.LoadFromStorage("./googleads.yaml")
        get_kw_perf_report(adwords_client)
        campaign_avg_position = get_campaign_avg_position_report(adwords_client).split('\n')[0]
        create_keywords_report_data()
        os.remove('./report.txt')
        os.remove('./report.csv')
        db_cursor = conn.cursor()
        now = datetime.datetime.now()
        return_data = []
        for kw_data in kws_to_change + db_dependency['above'] + db_dependency['below']:
            command = "INSERT INTO keywords(kw_id, kw_name, campaign_name, last_change) " \
                      "VALUES('{}', '{}', '{}', '{}') " \
                      "ON CONFLICT (kw_id) DO UPDATE SET last_change = excluded.last_change"\
                .format(kw_data.id, kw_data.name, input_from_user['campaign_name'], now.strftime("%m/%d/%y"))
            db_cursor.execute(command)
            conn.commit()
            return_data.append([input_from_user['campaign_name'], kw_data.ad_group, kw_data.name, kw_data.id,
                                kw_data.match_type, kw_data.cost / 1000000, kw_data.avg_position, kw_data.roi,
                                input_from_user['target_roi'], round((kw_data.max_cpc / 1000000), 2), kw_data.bid_change,
                                round(((kw_data.max_cpc / 1000000) + (kw_data.max_cpc / 1000000) * (round(kw_data.bid_change, 2) / 100)), 2)])
        return make_response(render_template("Keywords_data_output.html", kws_to_change=return_data))
