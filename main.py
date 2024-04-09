import requests
from time import sleep
import json
import re
from html.parser import HTMLParser
import sys

WEBHOOK_PROFILES_STANDARD = {
    "cmPitToDriver2": (
        "Oscar's Engineer",
        "https://cdn-1.motorsport.com/images/mgl/0rGy3eG2/s1200/the-mclaren-pit-wall-1.webp",
    ),
    "cmPitToDriver1": (
        "Lando's Engineer",
        "https://cdn-1.motorsport.com/images/mgl/0rGy3eG2/s1200/the-mclaren-pit-wall-1.webp",
    ),
    "cmDriver2ToPit": (
        "Oscar Piastri",
        "https://mclaren.bloomreach.io/cdn-cgi/image/width=400,height=400,fit=crop/delivery/resources/content/gallery/mclaren-racing/team-members/oscar-piastri-team-landing-page-hero-2024.jpg",
    ),
    "cmDriver1ToPit": (
        "Lando Norris",
        "https://mclaren.bloomreach.io/cdn-cgi/image/width=400,height=400,fit=crop/delivery/resources/content/gallery/mclaren-racing/team-members/lando-norris-team-landing-page-hero-2024.jpg",
    ),
}

WEBHOOK_PROFILES_OTHER = {
    "mclaren": "https://pbs.twimg.com/ext_tw_video_thumb/1446191112947970054/pu/img/o0FYOlkp44Q770aT.jpg",
    "pit": "https://cdn-1.motorsport.com/images/mgl/0rGy3eG2/s1200/the-mclaren-pit-wall-1.webp",
}

# Note: This is just a placeholder, and should be replaced with your own webhook URL. It is not a real webhook URL.
WEBHOOK_URL = "https://discord.com/api/webhooks/1028562194780131338/T_nRqLvcdLgZzyXJv8zdm54oWvd6M2N-GwOXPeYP0QiO3wifzsCZtNwLMCT76xxypAh4"


# File to store seen timestamps
SEEN_TIMESTAMPS_FILE = "seen_timestamps.json"


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data


f = HTMLFilter()


def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return None


def load_seen_timestamps():
    try:
        with open(SEEN_TIMESTAMPS_FILE, "r") as file:
            seen_ids = json.load(file)
    except FileNotFoundError:
        seen_ids = []
    return seen_ids


def save_seen_timestamps(seen_timestamps):
    with open(SEEN_TIMESTAMPS_FILE, "w") as file:
        json.dump(seen_timestamps, file)


def process_index(data):
    if not data:
        return

    # Load seen timestamps from file
    seen_timestamps = load_seen_timestamps()

    # Match all timestamps in the form 20240302t145307706z in the whole JSON using a regular expression and save them in a list
    timestamps = re.findall(r"\d{8}t\d{9}z", json.dumps(data))

    # Filter out the timestamps that have already been seen
    new_timestamps = list(
        set(timestamp for timestamp in timestamps if timestamp not in seen_timestamps)
    )

    # Add the new timestamps to the list of seen IDs
    seen_timestamps.extend(new_timestamps)

    # Save the updated list of seen IDs
    save_seen_timestamps(seen_timestamps)

    # return any new timestamps
    return new_timestamps


def process_new(new_timestamps):
    if not new_timestamps:
        return

    # Sort the new timestamps in ascending order
    new_timestamps.sort()

    for timestamp in new_timestamps:
        process_timestamp(timestamp)
        sleep(0.15)


def process_timestamp(timestamp):
    # Fetch the data for the given timestamp
    data = fetch_data(API_URL + timestamp)

    if not data:
        return

    # Get the ref from the document
    ref = data["document"]["$ref"].split("/")[-1]

    if not ref:
        return

    # Get the selectionValues from the commentTemplate
    source = data["page"][ref]["data"]["commentTemplate"]["selectionValues"][0]
    source_id = source["key"]
    source_name = source["label"]

    user = source_name
    profile = WEBHOOK_PROFILES_OTHER["mclaren"]

    # Convert the source ID to the source name
    if source_id in WEBHOOK_PROFILES_STANDARD:
        user = WEBHOOK_PROFILES_STANDARD[source_id][0]
        profile = WEBHOOK_PROFILES_STANDARD[source_id][1]
    elif "pit" in source_id.lower() or "pit" in source_name.lower():
        profile = WEBHOOK_PROFILES_OTHER["pit"]

    # Get the comment body
    comment_body = data["page"][ref]["data"]["commentBody"]["value"]

    # Clean the comment body
    f = HTMLFilter()
    f.feed(comment_body)
    cleaned_content = f.text

    # Send the webhook
    send_webhook(user, profile, cleaned_content)

    # Print the data to the console
    print(f"User: {user}")
    print(f"Cleaned Content: {cleaned_content}")


def send_webhook(user, profile, content):
    data = {"username": user, "content": content, "avatar_url": profile}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print(f"Failed to send webhook, status code: {response.status_code}")


def main():

    if len(sys.argv) < 3:
        print("Usage: python main.py <country> <session> <optional: webhook URL>")
        print("Example: python main.py bahrain 4")
        return

    country = sys.argv[1]

    session = sys.argv[2]

    if len(sys.argv) == 4:
        global WEBHOOK_URL
        WEBHOOK_URL = sys.argv[3]

    api_url = f"https://mclaren.bloomreach.io/delivery/site/v1/channels/mclaren-racing-en/pages/c08GetCommentary/racing/formula-1/2024/{country}-grand-prix/s{session}/cm/"

    while True:
        index_data = fetch_data(api_url)

        new_timestamps = process_index(index_data)

        process_new(new_timestamps)

        sleep(5)


if __name__ == "__main__":
    main()
