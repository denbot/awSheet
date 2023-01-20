#!/usr/local/bin/python3

from column_width import auto_resize_columns
import datetime
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import sys
## Uncomment webbrowser for local testing
#import webbrowser

# Define the shared folder ID where attendance sheets are stored and created
SHARED_FOLDER_ID = '1WYxIIkLXa5wQNsPZDu6O0drN1FRREh-X' ## 

# Create a dictionary
badge_names = {}
# Read in badge ids and corresponding discord ids
with open("badge_names.csv", "r") as f:
    for line in f:
        # Split the line into a list of strings
        badge, name, discordid, = line.strip().split(",")
        # Add the badge to the dictionary
        badge_names[badge] = name

# read environment variables non-interactively (e.g. ./cliWrite2sheets.py <BadgeID> <in> <timestamp>)
badgeid = sys.argv[1]
inout = sys.argv[2]
tstamp = sys.argv[3]

# Convert tstamp to a datetime object
date_time_obj = datetime.datetime.strptime(tstamp, '%m-%d-%Y %H:%M:%S')
# Convert the datetime object to a string
date_time_str = date_time_obj.strftime("%Y-%m-%d %H:%M:%S")

# Get the date from tstamp and convert it to %Y-%m-%d format
sheet_date = date_time_obj.strftime("%Y-%m-%d")

# Retrieve name from badge_names dictionary, using badgeid as the default value if the key does not exist
name = badge_names.get(badgeid, badgeid)

# Create a string for the sheet name
SHEET_NAME = f'{sheet_date}_'

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def main():
    # Use google.auth.default() to get the credentials and project ID
    creds, project = google.auth.default(scopes=SCOPES)
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        # Call the Sheets API
        results = drive_service.files().list(q=f"'{SHARED_FOLDER_ID}' in parents", fields="nextPageToken, files(id, name)").execute()
        # Get the names of the files in the shared folder
        items = results.get("files", [])
        # Create a list of the names of the files in the shared folder
        file_names = [item["name"] for item in items]
        
        # Check if the sheet already exists
        if SHEET_NAME not in file_names:
            # Create new Google Sheet
            file_metadata = {
              'name': SHEET_NAME,
              'mimeType': 'application/vnd.google-apps.spreadsheet',
              'parents': [SHARED_FOLDER_ID]
          }
            file = drive_service.files().create(body=file_metadata).execute()
            file_id = file['id']
            # Write the column headers to the first row of the sheet
            result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=file_id,
                    range='Sheet1!A1:D1',
                    valueInputOption='RAW',
                    body={'values': [['Name', 'CheckinTime', 'CheckoutTime', 'Duration']]}
            ).execute()
            print(f'https://docs.google.com/spreadsheets/d/' + file_id)
            ## Uncomment webbrowser.open for local testing
            #webbrowser.open(f'https://docs.google.com/spreadsheets/d/' + file_id, new=2)
        else:
            # Get the ID of the existing sheet
            file_id = [item["id"] for item in items if item["name"] == SHEET_NAME][0]
    
        # Retrieve the values in the sheet using the spreadsheets().values().get() method
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=file_id,
            range='Sheet1!A1:B'  # retrieve the values in columns A and B only
        ).execute()
        # Get the values from the result
        rows = result.get('values', [])
        found_row = None
        found_row_values = None
        # Iterate over the rows in the sheet and check if the first cell in each row matches the value of 'name'
        for i, row in enumerate(rows):
            if row[0] == name:
                found_row = i
                found_row_values = row
                break
        if found_row is not None:
            # Check the value of 'inout'
            if inout == 'in':
                # Update the cell in column B of the found row
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=file_id,
                    range=f'Sheet1!B{found_row+1}',
                    valueInputOption='USER_ENTERED',
                    body={'values': [[date_time_str]]}
                ).execute()
            elif inout == 'out':
                # Update the cell in column C of the found row
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=file_id,
                    range=f'Sheet1!C{found_row+1}',
                    valueInputOption='USER_ENTERED',
                    body={'values': [[date_time_str]]}
                ).execute()
                # Update the cell in column D of the found row with the formula to calculate the duration
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=file_id,
                    range=f'Sheet1!D{found_row+1}',
                    valueInputOption='USER_ENTERED',
                    body={'values': [[f"=TEXT(C{found_row+1}-B{found_row+1},\"h:mm:ss\")"]]}
                ).execute()
                # Resize the columns
                auto_resize_columns(sheets_service, file_id, 0, 2, 3)
                auto_resize_columns(sheets_service, file_id, 0, 3, 4)
        else:
            # Append the new row to the sheet using the spreadsheets().values().append() method
            ROWS = [[name, date_time_str]]
            sheet_range = f'Sheet1!A1:D{len(ROWS)+1}'
            sheet = sheets_service.spreadsheets()
            result = sheet.values().append(
                spreadsheetId=file_id,
                range=sheet_range,
                insertDataOption='INSERT_ROWS',
                valueInputOption='USER_ENTERED',
                body={'values': ROWS}
            ).execute()
            # Resize the columns
            print(f'{result["updates"]["updatedRows"]} rows appended to sheet.')
        # Resize the columns
        auto_resize_columns(sheets_service, file_id, 0, 0, 1)
        auto_resize_columns(sheets_service, file_id, 0, 1, 2)
    except HttpError as err:
        print(f'An error occured: {err}')

if __name__ == '__main__':
    main()
