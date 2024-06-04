import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_mail_csv(service):

    # GET CAR-COPILOT LABEL MAIL LISTS
    mails_from_label = service.users().messages().list(userId="me", labelIds = ['UNREAD','Label_6410322614978152058']).execute()
    
    # AVOID ERROR IF NO MAIL IN LABEL
    if(mails_from_label["resultSizeEstimate"] > 0) :
      
      # GET THE LAST MAIL
      mail_id = mails_from_label["messages"][0]["id"]
      specific_mail = service.users().messages().get(userId="me", id=mail_id).execute()
    
      # [FINAL] GET THE CAR NAME
      car_name = specific_mail["snippet"]
      # html_car_name = base64.b64decode(specific_mail["payload"]["parts"][0]["parts"][1]["body"]["data"], altchars=b'-_')
      # car_name = html_car_name.decode('utf-8') #.split("<")[2].split(">")[1]
      
      # [FINAL] GET THE EXPEDITOR
      headers = specific_mail["payload"]["headers"]
      mail_sender = "Unknown"
      for k in headers :
        if (k["name"] == 'Return-Path') :
          mail_sender = k["value"]
      
      # GET THE CSV DATA
      att_id = specific_mail["payload"]["parts"][1]["body"]["attachmentId"]
      csv_file = service.users().messages().attachments().get(userId="me", messageId=mail_id, id=att_id).execute()
      csv_data = base64.b64decode(csv_file["data"], altchars=b'-_')
      
      # WRITE THE CSV DATA IN LOCAL CSV
      f = open("influx_data.csv", "w")
      f.write(csv_data.decode('utf-8'))
      f.close()

      return (car_name, mail_sender)
    
    return ("No unread mails in 'car-copilot' label")


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    mail_info = get_mail_csv(service)
    
    print(mail_info)

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()