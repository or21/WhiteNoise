from flask_apispec import MethodResource, use_kwargs, marshal_with
from flask import make_response, render_template, request
import psycopg2
from googleads import adwords
import os
import csv


def db_connect():
    try:
        conn_string = "host='localhost' dbname='WhiteNoise' user='postgres' password='Aa123456' port=5000"
        print("Connecting to database\n	->%s" % conn_string)
        conn = psycopg2.connect(conn_string)
        return conn

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


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


class WhiteNoise(MethodResource):
    def get(self):
        return make_response(render_template("WhiteNoise.html"))


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
    global kws_to_change
    kws_to_change = []
    input_from_user['target_roi'] = float(input_from_user['target_roi'])
    input_from_user['target_position'] = float(input_from_user['target_position'])
    input_from_user['kw_min_spent'] = float(input_from_user['kw_min_spent'])
    input_from_user['avg_cpa'] = float(input_from_user['avg_cpa'])
    input_from_user['delicate_mode_bid_adj'] = (float(input_from_user['delicate_mode_bid_adj'].split(',')[0]),
                                                float(input_from_user['delicate_mode_bid_adj'].split(',')[1]))
    input_from_user['aggressive_mode_caps'] = (float(input_from_user['aggressive_mode_caps'].split(',')[0]),
                                               float(input_from_user['aggressive_mode_caps'].split(',')[1]))

    for kw in kws:
        if kw['Cost'] and kw['Cost'].isdigit() and float(kw['Cost']) != 0:
            kw_roi = float(kw['All conv. value']) / (float(kw['Cost']) / 1000000)
            roi_min = input_from_user['target_roi'] - input_from_user['target_roi'] * 0.1
            roi_max = input_from_user['target_roi'] + input_from_user['target_roi'] * 0.1
            if roi_max > kw_roi > roi_min:
                continue
            if (float(kw['Cost']) / 1000000) < input_from_user['kw_min_spent']:
                continue
            if 1.5 > float(kw['Avg. position']) > 1 and kw_roi > input_from_user['target_roi']:
                continue

            if float(kw['Cost']) > (3 * input_from_user['avg_cpa']):
                selected_mode = "aggressive"
            else:
                selected_mode = "delicate"

            bid_change = float(calc_bid_change(selected_mode, kw_roi, float(kw['Avg. position'])))
            keyword_match_type = kw['Match type']
            kws_to_change.append([input_from_user['campaign_name'], kw['Ad group'], kw['Keyword'], kw['Keyword ID'], keyword_match_type,
                                  float(kw['Cost']) / 1000000, kw['Avg. position'], kw_roi, input_from_user['target_roi'],
                                  round((float(kw['Max. CPC']) / 1000000), 2), bid_change,
                                  round((float(kw['Max. CPC']) / 1000000) + ((float(kw['Max. CPC']) / 1000000) * (round(bid_change, 2) / 100)), 2)])


def get_report(client):
    global kws
    kws = []
    report_downloader = client.GetReportDownloader(version='v201708')

    report = {
        'reportName': 'Last 7 days KEYWORDS_PERFORMANCE_REPORT',
        'dateRangeType': 'LAST_MONTH',
        'reportType': 'KEYWORDS_PERFORMANCE_REPORT',
        'downloadFormat': 'CSV',
        'selector': {
            'fields': ['CampaignId', 'CampaignName', 'AdGroupId', 'AdGroupName', 'Id', 'CpcBid', 'KeywordMatchType',
                       'Criteria', 'AveragePosition', 'Cost', 'AllConversionValue'],
            'predicates': {
                'field': 'CampaignName',
                'operator': 'EQUALS',
                'values': [input_from_user['campaign_name']]
            }
        }
    }

    with open('./report.txt', mode='w') as infile:
        report_downloader.DownloadReport(
            report, infile, skip_report_header=True, skip_column_header=False,
            skip_report_summary=True, include_zero_impressions=True)
    in_txt = csv.reader(open('./report.txt'), delimiter=',')
    out_csv = csv.writer(open('./report.csv', 'wb'))
    out_csv.writerows(in_txt)
    with open('./report.csv', mode='r') as data:
        reader = csv.DictReader(data)
        for row in reader:
            kws.append(row)


class KeywordsBidSuggestions(MethodResource):
    def post(self):
        global input_from_user
        for key in request.values.keys():
            if key in input_from_user.keys() and request.values[key] != "":
                input_from_user[key] = request.values[key]
        adwords_client = adwords.AdWordsClient.LoadFromStorage("./googleads.yaml")
        get_report(adwords_client)
        create_keywords_report_data()
        os.remove('./report.txt')
        os.remove('./report.csv')
        conn = db_connect()
        db_cursor = conn.cursor()
        for kw in kws_to_change:
            command = "INSERT INTO keywords(kw_id, kw_name, campaign_name, last_change) VALUES('%s', '%s', '%s', '%s')" % (str(kw[3]), str(kw[2]), str(kw[0]), "2017-10-07")
            print command
            db_cursor.execute(command)
            conn.commit()
        db_cursor.close()
        return make_response(render_template("Keywords_data_output.html", kws_to_change=kws_to_change))
