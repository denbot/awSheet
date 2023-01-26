import os
from dotenv import load_dotenv
from google.cloud import storage
from requests_oauthlib import OAuth2Session
import time

## WORK IN PROGRESS

load_dotenv()
client_id = os.getenv("DISCORD_CLIENT_ID")
client_secret = os.getenv("DISCORD_CLIENT_SECRET")
bucket_name = os.getenv("DISCORD_BUCKET_NAME")

storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

def get_token():
    # Try to get the access token from the GCS bucket
    try:
        blob = bucket.get_blob("access_token.txt")
        access_token = blob.download_as_string().decode()
        refresh_token = blob.metadata.get('refresh_token', None)
        expires_at = int(blob.metadata.get('expires_at', 0))
        if expires_at < time.time():
            discord = OAuth2Session(client_id, token={"refresh_token": refresh_token})
            new_token = discord.refresh_token("https://discord.com/api/oauth2/token", client_secret=client_secret)
            access_token = new_token["access_token"]
            expires_at = new_token["expires_at"]
            refresh_token = new_token["refresh_token"]
            # Write the new token to the GCS bucket
            blob = bucket.blob("access_token.txt")
            blob.metadata = {'expires_at': expires_at, 'refresh_token': refresh_token}
            blob.upload_from_string(access_token)
        return access_token
    except:
        pass
    
    # If the access token is not found in the GCS bucket, get a new one using OAuth2
    discord = OAuth2Session(client_id)
    auth_url, state = discord.authorization_url("https://discord.com/api/oauth2/authorize", scope=["identify"])
    print(f"Please go to this URL: {auth_url}")
    auth_response = input("Enter the full callback URL: ")
    discord.fetch_token("https://discord.com/api/oauth2/token", authorization_response=auth_response, client_secret=client_secret)

    access_token = discord.token["access_token"]
    expires_at = discord.token["expires_at"]
    refresh_token = discord.token["refresh_token"]
    # Write the new token to the GCS bucket
    blob = bucket.blob("access_token.txt")
    blob.metadata = {'expires_at': expires_at, 'refresh_token': refresh_token}
    blob.upload_from_string(access_token)
    return access_token

def get_user_info(access_token):
    discord = OAuth2Session(client_id, token=access_token)
    user_info = discord.get("https://discord.com/api/users/@me").json()
    return user_info