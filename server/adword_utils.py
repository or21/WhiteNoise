import suds
import logging
from googleads import adwords


adwords_client = adwords.AdWordsClient.LoadFromStorage("./googleads.yaml")
label_service = adwords_client.GetService('LabelService', version='v201708')
report_downloader = adwords_client.GetReportDownloader(version='v201708')
ad_group_criterion_service = adwords_client.GetService('AdGroupCriterionService', version='v201708')


def get_report(report_type, campaign_name, date_range, fields):
    report = {
        'reportName': "{} {}".format(date_range, report_type),
        'dateRangeType': date_range,
        'reportType': report_type,
        'downloadFormat': 'CSV',
        'selector': {
            'fields': fields,
            'predicates': {
                'field': 'CampaignName',
                'operator': 'EQUALS',
                'values': [campaign_name]
            }
        }
    }

    report = report_downloader.DownloadReportAsString(
        report, skip_report_header=True, skip_column_header=False,
        skip_report_summary=True, include_zero_impressions=True)

    return report


def get_keywords_report(campaign_name, date_range):
    fields = ['CampaignId', 'CampaignName', 'AdGroupId', 'AdGroupName', 'Id', 'CpcBid', 'KeywordMatchType',
              'Criteria', 'AveragePosition', 'Cost', 'AllConversionValue', 'Impressions']

    return get_report('KEYWORDS_PERFORMANCE_REPORT', campaign_name, date_range, fields)


def get_campaign_report(campaign_name, date_range, fields):
    return get_report('CAMPAIGN_PERFORMANCE_REPORT', campaign_name, date_range, fields)


def add_label_to_keyword(kw, label_text):
    logger = logging.getLogger(__name__)
    operations = [
        {
            'operator': 'ADD',
            'operand': {
                'xsi_type': 'TextLabel',
                'name': label_text
            }
        }
    ]

    try:
        label_id = label_service.mutate(operations)['value'][0]['id']
    except:
        message = "Label '{}' exists, looking for it's ID".format(label_text)
        logger.info(message)
        service_selector = {
            'fields': ['LabelId'],
            'predicates': {
                'field': 'LabelName',
                'operator': 'EQUALS',
                'values': label_text}
            }
        label_id = label_service.get(service_selector)['entries'][-1]['id']

    op = [{
        'xsi_type': "AdGroupCriterionLabelOperation",
        'operator': 'ADD',
        'operand': {
            'adGroupId': kw.ad_group_id,
            'criterionId': kw.id,
            'labelId': str(label_id)
        }
    }]

    try:
        ad_group_criterion_service.mutateLabel(op)
        message = "Label {} was added to keyword {} on ad group {}".format(label_text, kw.name, kw.ad_group).encode('utf-8')
        logger.debug(message)
    except suds.WebFault as detail:
        logger.error(detail)
