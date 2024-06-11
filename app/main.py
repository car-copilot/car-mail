import os.path
import os
import base64
import time, signal
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_now = True

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
          mail_sender = k["value"].split("<")[1].split(">")[0]

      # GET THE CSV FILE NAME
      file_name = specific_mail["payload"]["parts"][1]["filename"]

      # GET THE CSV DATA
      att_id = specific_mail["payload"]["parts"][1]["body"]["attachmentId"]
      csv_file = service.users().messages().attachments().get(userId="me", messageId=mail_id, id=att_id).execute()
      csv_data = base64.b64decode(csv_file["data"], altchars=b'-_')

      # WRITE THE CSV DATA IN LOCAL CSV
      # f = open("influx_data.csv", "w")
      # f.write(csv_data.decode('utf-8'))
      # f.close()

      # READ THE MESSAGE WHEN THREATED
      service.users().messages().modify(userId="me", id=mail_id, body={"removeLabelIds": ['UNREAD']}).execute()

      return send_infos(car_name, mail_sender, file_name, csv_data)

    return("No unread mails in 'car-copilot' label")




def send_infos(car_name, mail_sender, file_name, csv_data):

  url = os.environ["API_URL"]

  payload = {
    'car': car_name,
    'owner': mail_sender,
    'filename': file_name
  }
  files=[
    ('file',(file_name, csv_data,'text/csv'))
  ]
  headers = {}

  response = requests.request("POST", url, headers=headers, data=payload, files=files)

  print(response.text)

  return("Data sent to DB")




def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("config/token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "config/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("config/token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    killer = GracefulKiller()
    while not killer.kill_now:
      print(get_mail_csv(service))
      time.sleep(120)
    print("End of the program. I was killed gracefully")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
