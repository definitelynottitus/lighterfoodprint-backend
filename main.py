import requests, pprint, json, google.auth, os, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
today = datetime.date.today().strftime("%s")
yesturday = datetime.date.today() - datetime.timedelta(1)
yesturday = yesturday.strftime("%s")
email_address = os.getenv('email_address')

# Google sheet authentication set up
# Please refer to https://developers.google.com/sheets/api/quickstart/python
# for more details how to set up
credentials, project = google.auth.default(scopes = ['https://www.googleapis.com/auth/spreadsheets'])
sheet_id = os.getenv('GOOGLE_SHEET_ID')
range_name = 'fb_ig_insights!A:F'

# Facebook Graph API set up
# get your access setup here:
# https://developers.facebook.com/docs/graph-api/
access_token = os.getenv('ACCESS_TOKEN')
page_access_token = os.getenv('PAGE_ACCESS_TOKEN')
ins_id = os.getenv('INS_ID')
facebook_page_id = os.getenv('FB_PAGE_ID')
base_url = 'https://graph.facebook.com/v13.0/'

def sendAlertEmail(email, error):
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')    
    message = Mail(
            from_email='alert@titusl.com',
            to_emails = email,
            subject='Facebook Graph API Error',
            plain_text_content='Encounter error: ' + pprint.pformat(error,indent=2)
            )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
    except Exception as e:
        print(e)

def getFollowerCount(social_media_ID: str):
    """
    get follower counts from either facebook or instagram given page id
    
    :param str social_meida_ID: facebook page or instagram user id
    """
    response = requests.get(f'{base_url}{social_media_ID}?fields=followers_count&access_token={access_token}').json()
    try:
        return(response['followers_count'])
    except KeyError:
        pprint.pprint(response["error"],indent=2)
        sendAlertEmail(email_address, json.dumps(response["error"]))
    return response

def getInsights(metric:str, period:str, since=yesturday, until=today, useFBInsight=False):
    """
    get insigts from Facebook Page or Instagram user, refer to
    Instagram or Facebook Graph API for more info
    
    :param str metric: check https://developers.facebook.com/docs/graph-api/reference/v2.5/insights#Reading
                       for more details on metric
    :param str period: check https://developers.facebook.com/docs/graph-api/reference/v2.5/insights#Reading
                       for more details on period                
    :param bool useFBInsight: get Insight from Facebook Page instead of Instagram, is set to False by default
    :param unixtime since: Used in conjunction with {until} to define a Range. 
                           If you omit since and until, the API defaults to a 2 day range: yesterday through today.
    """
    if useFBInsight:
        insights = requests.get(f'{base_url}{facebook_page_id}/insights?metric={metric}&period={period}&since={since}&until={until}&access_token={page_access_token}').json()
    else:
        insights = requests.get(f'{base_url}{ins_id}/insights?metric={metric}&period={period}&since={since}&until={until}&access_token={access_token}').json()
    try:
        return(insights['data'][0]['values'])
    except KeyError:
        pprint.pprint(insights["error"],indent=2)
        sendAlertEmail(email_address, insights["error"])
    return insights
        

def main():
    try:
        service = build('sheets','v4', credentials=credentials)
        sheet = service.spreadsheets()
        time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        values = [[time,
                   getInsights('reach','week')[1]['value'],
                   getInsights('impressions','week')[1]['value'],
                   getInsights('page_engaged_users','week',useFBInsight=True)[0]['value'],
                   getInsights('page_impressions','week',useFBInsight=True)[0]['value'],
                   getInsights('page_views_total','week',useFBInsight=True)[0]['value']]]
        
        resource = {
            "majorDimension": "ROWS",
            "values": values
        }
        result = sheet.values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            body=resource,
            valueInputOption="USER_ENTERED"
        ).execute()
        
        pprint.pprint(result,indent=2)

        
    except HttpError as e:
        print(e)
    
    

if __name__ == '__main__':
    main()




    


