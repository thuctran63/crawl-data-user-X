from datetime import datetime
import random
import threading
import time
import requests
import json
import yaml

# global variables
period_time = 0
time_sleep = 0
maximum_scroll = 0
number_of_threads = 0

def write_to_log(content):
    with open('log.txt', 'a', encoding='utf-8') as file:
        print(content)
        file.write(content + '\n')

lock = threading.Lock() 
def write_to_file(filename, content):
    with lock:
        with open(filename, 'a') as file: 
            file.write(content + '\n')

def calculate_time_difference(time_str):
    try:
        # Parse the time string and convert to timestamp
        time_format = "%a %b %d %H:%M:%S %z %Y"
        input_time = datetime.strptime(time_str, time_format)
        input_timestamp = input_time.timestamp()
        
        # Get current timestamp
        current_timestamp = datetime.now(input_time.tzinfo).timestamp()
        
        # Calculate time difference
        time_difference = current_timestamp - input_timestamp
        
        # Convert time difference to hours
        hours_difference = time_difference / 3600
        
        return abs(hours_difference)
    except ValueError as e:
        raise ValueError(f"Invalid time format: {time_str}. Error: {e}")

def delete_acc_check(acc_check):
    with lock:
        with open('acc_check.json', 'r') as file:
            data = json.load(file)
            data.remove(acc_check)
        with open('acc_check.json', 'w') as file:
            json.dump(data, file, indent=4)

def find_objects_with_cursor(data, target_key = "cursorType", target_value = "Bottom"):
    results = []
    if isinstance(data, dict):  # If the data is a dictionary
        for key, value in data.items():
            if key == target_key and value == target_value:
                results.append(data)
            else:
                results.extend(find_objects_with_cursor(value, target_key, target_value))
    elif isinstance(data, list):  # If the data is a list
        for item in data:
            results.extend(find_objects_with_cursor(item, target_key, target_value))
    return results

def load_settings_from_yml(file_path):
    global period_time, time_sleep, maximum_scroll, number_of_threads
    with open(file_path, 'r', encoding='utf-8') as file:
        settings = yaml.safe_load(file)
        # Truy cập vào mục 'setting' trong YAML
        setting = settings.get('setting', {})

        # Lấy các giá trị từ mục 'setting'
        period_time = setting.get('period_time')
        time_sleep = setting.get('time_sleep')
        maximum_scroll = setting.get('maximum_scroll')
        number_of_threads = setting.get('number_of_threads')

def get_link_post(username, id_post):
    return f"https://x.com/{username}/status/{id_post}"

def get_info_user(user_name : str, acc_check : dict):
    # Tạo header
    headers = {
                "Content-Type": "application/json",
                "Authorization": acc_check["bearer_token"],  # Bearer token từ tài khoản
                 "x-csrf-token": acc_check["csrf_token"],    # CSRF token từ tài khoản
                "Cookie": acc_check["cookie"]                # Cookie từ tài khoản
            }

    url_get_id_user = "https://x.com/i/api/graphql/QGIw94L0abhuohrr76cSbw/UserByScreenName"
    payload_get_id_user = {
        "variables": {
            "screen_name": f"{user_name}"  # Đảm bảo đúng giá trị screen_name
        },
        "features": {
            "hidden_profile_subscriptions_enabled": True,
            "profile_label_improvements_pcf_label_in_post_enabled": False,
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "subscriptions_verification_info_is_identity_verified_enabled": True,
            "subscriptions_verification_info_verified_since_enabled": True,
            "highlights_tweets_tab_ui_enabled": True,
            "responsive_web_twitter_article_notes_tab_enabled": True,
            "subscriptions_feature_can_gift_premium": True,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True
        },
        "fieldToggles": {
            "withAuxiliaryUserLabels": False
        }
    }

    # Gửi request
    response = requests.get(url_get_id_user, headers=headers, json=payload_get_id_user)    
    # Kiểm tra trạng thái phản hồi
    if response.status_code == 200:
        print("Lấy thông tin user thành công")
        response = response.json()
        user_id = response["data"]["user"]["result"]["rest_id"]
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response:", response.text)
    
    return user_id

def get_all_link_media(user_id, user_name, acc_check, number_scroll):
    # URL endpoint
    url_get_data = "https://x.com/i/api/graphql/bDGQZ9i975PnuFhihvzGug/UserTweets"
    list_link_per_user = set()
    cursor = None
    for i in range(number_scroll):
        headers = {
                "Content-Type": "application/json",
                "Authorization": acc_check["bearer_token"],  # Bearer token từ tài khoản
                "x-csrf-token": acc_check["csrf_token"],    # CSRF token từ tài khoản
                "Cookie": acc_check["cookie"],
            }
        # Payload
        payload_get_data = {
            "variables": {
                "userId": f"{user_id}",
                "count": 20,
                "includePromotedContent": True,
                "withQuickPromoteEligibilityTweetFields": True,
                "withVoice": True,
                "withV2Timeline": True
            },
            "features": {
                "profile_label_improvements_pcf_label_in_post_enabled": False,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "premium_content_api_read_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "responsive_web_grok_analyze_button_fetch_trends_enabled": True,
                "responsive_web_grok_analyze_post_followups_enabled": False,
                "responsive_web_grok_share_attachment_enabled": False,
                "articles_preview_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_enhance_cards_enabled": False
            },
            "fieldToggles": {
                "withArticlePlainText": False
            }
        }
        index = 1
        if cursor is not None:
            payload_get_data["variables"]["cursor"] = cursor
            index = 0
        try:
            response = requests.get(url_get_data, headers=headers, json=payload_get_data)
            
            # Kiểm tra trạng thái phản hồi
            if response.status_code == 200:
                print(f"Đã lấy thông tin bài viết lần thứ {i + 1} thành công!")
                # # lưu vào file
                # write_to_file('response.json', json.dumps(response.json(), indent=2))
                response = response.json()
                list_tweets = response["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"][index]["entries"]
                for tweet in list_tweets:
                    try:
                        tweet_time = calculate_time_difference(tweet["content"]["itemContent"]["tweet_results"]["result"]["legacy"]["created_at"])
                    except:
                        continue
                    if tweet_time <= period_time:
                        tweet_id = tweet["content"]["itemContent"]["tweet_results"]["result"]["rest_id"]
                        type_media = tweet["content"]["itemContent"]["tweet_results"]["result"]["source"]
                        if "Twitter for Advertisers" in type_media:
                            link_media = get_link_post(user_name, tweet_id)
                            list_link_per_user.add(link_media)
            else:
                return None
            cursor = find_objects_with_cursor(response, target_key="cursorType", target_value="Bottom")[0]["value"]
        except Exception as e:
            print("An error occurred:", e)
            return None
    return list_link_per_user

def get_all_link_media_multi_user(list_acc_check, list_user, maximum_scroll, time_sleep):
    i = 0
    for user in list_user:
        write_to_log(f"Đang check user: {user}")
        if i >= len(list_acc_check):
            i = 0
        acc_check = list_acc_check[i]
        # Lấy link media
        while True:
            try:
                # Lấy thông tin user
                user_id = get_info_user(user, acc_check)
                time.sleep(1)
                list_link_per_user = get_all_link_media(user_id, user, acc_check, maximum_scroll)
                if(list_link_per_user is not None):
                    all_links = "\n".join(list_link_per_user)
                    write_to_file(f'result.txt', all_links)
                    i += 1
                    time.sleep(time_sleep)
                    write_to_log(f"Đã check xong user: {user}")
                    break
                else:
                    delete_acc_check(acc_check)
                    list_acc_check.remove(acc_check)
                    acc_check = random.choice(list_acc_check)
                    write_to_log(f"Acc lỗi, đang chuyển sang acc khác...")
                    
            except Exception as e:
                delete_acc_check(acc_check)
                list_acc_check.remove(acc_check)
                acc_check = random.choice(list_acc_check)
                write_to_log(f"Acc lỗi, đang chuyển sang acc khác...")
            
# xử lí main
load_settings_from_yml('settings.yml')

with open('acc_check.json', 'r') as file:
    list_acc_check = json.load(file)

with open('user.txt', 'r') as file:
    list_user = file.read().splitlines()

threads = []

number_acc_check_per_thread = len(list_acc_check) // number_of_threads
number_user_per_thread = len(list_user) // number_of_threads
for i in range(number_of_threads):
    start_acc_check = i * number_acc_check_per_thread
    end_acc_check = start_acc_check + number_acc_check_per_thread
    start_user = i * number_user_per_thread
    end_user = start_user + number_user_per_thread

    if i == number_of_threads - 1:
        end_acc_check = len(list_acc_check)
        end_user = len(list_user)
    
    thread = threading.Thread(target=get_all_link_media_multi_user, args=(list_acc_check[start_acc_check:end_acc_check], list_user[start_user:end_user], maximum_scroll,time_sleep))
    threads.append(thread)

for thread in threads:
    thread.start()