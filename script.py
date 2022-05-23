from __future__ import print_function

from typing import Union, List, Any, Tuple

import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import os.path
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError


load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = os.environ.get('SAMPLE_SPREADSHEET_ID')
SAMPLE_RANGE_NAME = os.environ.get('SAMPLE_RANGE_NAME')
TOKEN_JSON = os.environ.get('TOKEN_JSON')
CREDANTIALS_JSON = os.environ.get('CREDANTIALS_JSON')


def dollar_to_ruble(money: float) -> float:
    """Get current dollar USA (USD) course (from https://cbr/)
    return convert dollar to ruble (float)
    """
    request = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?')
    if request.status_code == 200:
        # convert XML-response(string) to ET - tree
        root = ET.fromstring(request.text)
        # find in XML dollar course
        root = root.find(".//Value/..[@ID='R01235']")
        return float(root.find('Value').text.replace(',', '.')) * money
    else:
        raise requests.exceptions.RequestException('Request is not correct')


def enable_sheets_connection(token: str, credentials: str) -> Resource:
    """Connect client to Google Sheet.
    Args:
        token(str): path to .json file with token
        credentials(str): path to .json file with credentials

    Returns:
        googleapiclient.discovery.Resource: Google Sheet object

    Raises:
        HttpError: If response invalid or nor response.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        return sheet
    except HttpError as err:
        print(err)


def get_all_table(sheet: Resource, sample_spreadsheet_id: str, sample_range_name: str) -> list:
    """get all values from Google Sheet.
    Args:
        sheet(googleapiclient.discovery.Resource): path to .json file with token
        sample_spreadsheet_id(str): get this id from url your Google Sheet
        sample_range_name(str): scope list and diapason of scope sheet

    Returns:
        googleapiclient.discovery.Resource: Google Sheet object

    Raises:
        HttpError: If response invalid or nor response.
    """

    result = sheet.values().get(spreadsheetId=sample_spreadsheet_id,
                                range=sample_range_name).execute()
    values = result.get('values', [])
    if not values:
        raise ValueError('No data found.')

    # replace number of row to id (for db work)
    for row in range(len(values)):
        values[row][0] = row

    return values


def update_data_table(pre_data: list, sheet: Resource, sample_spreadsheet_id: str, sample_range_name: str) -> Union[
    list[Any], tuple[Any, list[Any]]]:
    """get all values from Google Sheet.
    Args:
        pre_data(list): data from table from last iteration
        sheet(googleapiclient.discovery.Resource): path to .json file with token
        sample_spreadsheet_id(str): get this id from url your Google Sheet
        sample_range_name(str): scope list and diapason of scope sheet

    Returns:
        list: new Google Sheet values
        list: updated values

    Raises:
        HttpError: If response invalid or nor response.
    """
    time.sleep(4)
    updated = []
    # get data from Google
    result = sheet.values().get(spreadsheetId=sample_spreadsheet_id,
                                range=sample_range_name).execute()
    # convert type(result) to list
    values = result.get('values', [])
    # check response from Google Sheets
    if not values:
        print('No data found.')
        return []

    for row in range(len(values)):
        try:
            # replace number of row to id (for db work)
            values[row][0] = row
        except IndexError:
            # set id to empty list (if row was deleted)
            values[row].append(row)
        try:

            if str(pre_data[row]) != str(values[row]):
                # print(pre_data[row])
                # print(values[row])
                updated.append(values[row])
            elif not (values[row]):
                # checking on delete of last element
                updated.append(values[row])
        except IndexError:
            updated.append(values[row])

    # if pre_data longer than values, then some last rows was deleted
    if len(pre_data) > len(values):
        for i in range(len(values), len(pre_data)):
            updated.append([i])

    return values, updated


def main():
    print('\033[32mScript started...\033[0m')
    sheet = enable_sheets_connection(TOKEN_JSON, CREDANTIALS_JSON)
    values = get_all_table(sheet, SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
    while True:
        values, updated = update_data_table(values, sheet, SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
        if updated:
            print('updated:', updated)
        # print('values', values)


if __name__ == '__main__':
    main()
