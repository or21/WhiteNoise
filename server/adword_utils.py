from googleads import adwords

adwords_client = adwords.AdWordsClient.LoadFromStorage("./googleads.yaml")


def get_keywords_report(campaign_name, date_range):
    report_downloader = adwords_client.GetReportDownloader(version='v201708')
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
                'values': [campaign_name]
            }
        }
    }

    report = report_downloader.DownloadReportAsString(
        report, skip_report_header=True, skip_column_header=False,
        skip_report_summary=True, include_zero_impressions=True)

    return report


def get_campaign_report(campaign_name, date_range, fields):
    report_downloader = adwords_client.GetReportDownloader(version='v201708')
    report = {
        'reportName': "{} KEYWORDS_PERFORMANCE_REPORT".format(date_range),
        'dateRangeType': date_range,
        'reportType': 'CAMPAIGN_PERFORMANCE_REPORT',
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

    report_results = report_downloader.DownloadReportAsString(
            report, skip_report_header=True, skip_column_header=True,
            skip_report_summary=True, include_zero_impressions=True)
    return report_results
