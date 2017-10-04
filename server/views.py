from flask_apispec import MethodResource, use_kwargs, marshal_with
from flask import make_response, render_template, request
from pymongo import MongoClient
from googleads import adwords
import time
import sys
import csv
import json


client = MongoClient('mongodb://127.0.0.1/')
db = client.test
PAGE_SIZE = 100
campaigns = []
input_from_user = {}


class Campaign:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.adgroups = {}


class HelloWorld(MethodResource):
    def get(self):
        data = db.data.find_one({'first name': 'Or'})
        return make_response(render_template("index.html", data=data))


class WhiteNoise(MethodResource):
    def get(self):
        return make_response(render_template("WhiteNoise.html"))


def find_campaigns_data(client):
    global campaigns

    # Initialize appropriate service.
    campaign_service = client.GetService('CampaignService', version='v201708')

    # Construct selector and get all campaigns.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }

    more_pages = True
    while more_pages:
        page = campaign_service.get(selector)

        # Display results.
        if 'entries' in page:
            for campaign in page['entries']:
                campaigns.append(Campaign(campaign['name'], campaign['id']))
        else:
            print('No campaigns were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
        time.sleep(1)
    for campaign in campaigns:
        if "Stocks" in campaign.name:
            number_of_groups = 1
            campaign.adgroups = find_adgroup_by_campaign(client, campaign.id)
            for adgroup in campaign.adgroups.keys():
                if number_of_groups != 0:
                    campaign.adgroups[adgroup] = find_kw_by_adgroup_id(client, adgroup)
                    number_of_groups = number_of_groups - 1
            break


def find_adgroup_by_campaign(client, campaign_id):
    # Initialize appropriate service.
    ad_group_service = client.GetService('AdGroupService', version='v201708')
    ad_groups = {}

    # Construct selector and get all ad groups.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'CampaignId',
                'operator': 'EQUALS',
                'values': [campaign_id]
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_service.get(selector)

        # Display results.
        if 'entries' in page:
            for ad_group in page['entries']:
                ad_groups[str(ad_group['id'])] = {}
        else:
            print('No ad groups were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return ad_groups


def find_kw_by_adgroup_id(client, adgroup_id):
    # Initialize appropriate service.
    ad_group_criterion_service = client.GetService(
        'AdGroupCriterionService', version='v201708')
    kws = {}

    # Construct selector and get all ad group criteria.
    offset = 0
    selector = {
        'fields': ['Id', 'CriteriaType', 'KeywordMatchType', 'KeywordText', 'impression'],
        'predicates': [
            {
                'field': 'AdGroupId',
                'operator': 'EQUALS',
                'values': [adgroup_id]
            },
            {
                'field': 'CriteriaType',
                'operator': 'EQUALS',
                'values': ['KEYWORD']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        },
        'ordering': [{'field': 'KeywordText', 'sortOrder': 'ASCENDING'}]
    }
    more_pages = True
    while more_pages:
        page = ad_group_criterion_service.get(selector)

        # Display results.
        if 'entries' in page:
            print page
            for keyword in page['entries']:
                kws[keyword['criterion']['text']] = keyword
        else:
            print('No keywords were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return kws


def make_calculations():
    return None


def get_report(client):
    report_downloader = client.GetReportDownloader(version='v201708')

    report = {
        'reportName': 'Last 7 days CRITERIA_PERFORMANCE_REPORT',
        'dateRangeType': 'LAST_7_DAYS',
        'reportType': 'CRITERIA_PERFORMANCE_REPORT',
        'downloadFormat': 'CSV',
        'selector': {
            'fields': ['CampaignId', 'AdGroupId', 'Id', 'CriteriaType',
                       'Criteria', 'FinalUrls', 'Impressions', 'Clicks', 'Cost']
        }
    }

    # You can provide a file object to write the output to. For this demonstration
    # we use sys.stdout to write the report to the screen.
    with open('./report.txt', mode='w') as infile:
        report_downloader.DownloadReport(
            report, infile, skip_report_header=False, skip_column_header=False,
            skip_report_summary=False, include_zero_impressions=True)
    in_txt = csv.reader(open('./report.txt'), delimiter=',')
    out_csv = csv.writer(open('./report.csv', 'wb'))

    out_csv.writerows(in_txt)


def csv_to_json(csv_name):
    with open(csv_name, mode='r') as infile:
        reader = csv.reader(infile)
        with open('./report_new.csv', mode='w') as outfile:
            writer = csv.writer(outfile)
            mydict = {rows[0]: rows[1] for rows in reader}
    return mydict


class AdWords(MethodResource):
    def post(self):
        global input_from_user
        input_from_user = request.values
        adwords_client = adwords.AdWordsClient.LoadFromStorage("./googleads.yaml")
        get_report(adwords_client)
        # find_campaigns_data(adwords_client)
        # make_calculations()
        return make_response(render_template("campaigns.html", data=json.dumps(csv_to_json('./report.csv'))))


class Crud(MethodResource):
    def get(self):
        return crud_router()

    def post(self):
        return crud_router(request)


def crud_router(request_form=None):
    message = "Please fill the form"
    if request_form:
        action = request_form.form['action']
        firstname = request_form.form['firstname']
        lastname = request_form.form['lastname']
    else:
        action = ""

    if action == 'Filter':
        filtered = list(db.data.find({'last name': lastname}))
        print(filtered)
        if filtered:
            message = "Filtered by last name - " + lastname
            return make_response(render_template("actions.html", data=filtered, message=message))
        else:
            message = "Could not find instance. Reminder - you can only filter by last name"

    if action == 'Add':
        if db.data.find_one({'first name': firstname}):
            message = "There is already instance with first name  " + firstname
        else:
            message += "Inserted " + firstname + " " + lastname
            db.data.insert_one({'first name': firstname, 'last name': lastname})

    if action == 'Update':
        element = db.data.find_one({'first name': firstname})
        if list(element):
            if element['last name'] == lastname:
                message = "Nothing to update"
            else:
                message = "Updated " + firstname + " last name to: " + lastname
                db.data.update_one({'first name': firstname},
                                   {'$set': {'first name': firstname, 'last name': lastname}})
        else:
            message = "Could not update. No instance for first name " + firstname

    if action == 'Delete':
        if db.data.find_one({'first name': firstname}):
            message = "Delete where first name is " + firstname
            db.data.delete_one({'first name': firstname})
        else:
            message = "Could not delete. No instance with first name " + firstname

    data = list(db.data.find({}))
    return make_response(render_template("actions.html", data=data, message=message))
