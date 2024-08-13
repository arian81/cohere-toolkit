import base64
import os.path
from pprint import pprint
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

LABEL_IDS = ["STARRED"]
# LABEL_IDS = ["IMPORTANT", "STARRED"]
# https://developers.google.com/gmail/api/reference/rest/v1/Format
EMAIL_FORMAT = "full"
MAX_RESULTS = 3


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
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=53091)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        # labels = service.users().labels().list(userId="me").execute()
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=MAX_RESULTS, labelIds=LABEL_IDS)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            print("No messages found.")
            return

        docs: List[GmailDocument] = [
            process_message(message, service) for message in messages
        ]

    except HttpError as error:
        print(f"An error occurred: {error}")


class GmailDocument(BaseModel):
    title: str
    content: str
    metadata: Dict[str, Any] = {}


def process_message(message: Dict[str, Any], service: Any) -> List[GmailDocument]:
    message_id = message["id"]
    email = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format=EMAIL_FORMAT)
        .execute()
    )
    important_headers = process_email_headers(email["payload"]["headers"])
    title = f"""
    Subject:{important_headers['Subject']}
    From:{important_headers['From']}
    Date:{important_headers['Date']}
    Snippet:{email['snippet']}"""

    # parallelize this
    all_parts = process_email_payload(email["payload"])
    content = "\n".join(all_parts)
    metadata = {
        "message_id": message_id,
    }
    print("====================================")
    print("Id:", message_id)
    print("Title:", title)
    print("Content\n", content)
    return GmailDocument(title=title, content=content, metadata=metadata)


def decode_base64(data: bytes) -> str:
    return base64.urlsafe_b64decode(data).decode("utf-8")


def process_email_raw(bs: bytes) -> str:
    return decode_base64(bs)


def process_email_headers(headers: List[dict]) -> dict:
    important_headers = ["From", "To", "Subject", "Date"]
    return {
        header["name"]: header["value"]
        for header in headers
        if header["name"] in important_headers
    }


# if not "raw" in message["payload"]:
def process_email_payload(payload: Any) -> List[str]:
    all_parts = []
    match payload["mimeType"]:
        case "text/plain":
            text_b64 = payload.get("body", {}).get("data", None)
            all_parts.append(decode_base64(text_b64)) if text_b64 else None
        # TODO, what to do with images?
        case "image/jpeg":
            pass
        case "text/html":
            html_content_b64 = payload.get("body", {}).get("data", None)
            if html_content_b64:
                soup = BeautifulSoup(decode_base64(html_content_b64), "html.parser")
                text = soup.get_text(separator="\n")
                # remove redundant newlines
                text = re.sub(r"\n+", "\n", text)
                all_parts.append(text)
        case "multipart/alternative" | "multipart/related":
            for p in payload.get("parts", []):
                inner_parts = process_email_payload(p)
                all_parts.extend(inner_parts)
        case _:
            pass
    cleaned_parts = [p for p in all_parts if p]
    return cleaned_parts


if __name__ == "__main__":
    main()
