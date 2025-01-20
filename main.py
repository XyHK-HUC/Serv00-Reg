import os
import re
import json
import time
import pytz
import string
import random
import ddddocr
import inspect
import hashlib
import asyncio
import requests
from faker import Faker
from telegram import Bot
from loguru import logger
from datetime import datetime
from urllib.parse import quote
from fake_headers import Headers
from urllib.parse import urlencode
from requests.exceptions import JSONDecodeError

os.makedirs("static", exist_ok=True)
global enable, input_token, input_chatid
config_file = 'static/config.json'

def get_input_prompt():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.') + str(datetime.now().microsecond // 1000).zfill(3)
    frame = inspect.stack()[1]
    module_name = inspect.getmodule(frame[0]).__name__
    module_info = f'{module_name}:<module>'
    caller_line = frame.lineno
    return f'\033[32m{current_time}\033[0m | \033[1;94mINPUT\033[0m    | \033[36m{module_info}:{caller_line}\033[0m - '

def input_option_menu():
    input_option = get_valid_input("\033[1;94m请输入选项:\033[0m", lambda x: x in ['1', '2'], "无效的选择,请重新输入.")
    return input_option

async def send_message(message):
    global input_token, input_chatid
    bot = Bot(token=input_token)
    try:
        await bot.send_message(chat_id=input_chatid, text=message)
    except Exception as e:
        logger.error(f"发送失败: {e}")

def get_user_name():
    url = "https://www.ivtool.com/random-name-generater/uinames/api/index.php?region=united%20states&gender=male&amount=5&="
    resp = requests.get(url, verify=False)
    if resp.status_code != 200:
        print(resp.status_code, resp.text)
        raise Exception("获取名字出错")
    data = resp.json()
    return data

def generate_random_username():
    length = random.randint(7, 10)
    characters = string.ascii_letters
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def generate_random_headers():
    return {
        "Accept-Language": random.choice(["en-US,en;q=0.9", "ja-JP,ja;q=0.9", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9", "es-ES,es;q=0.9"]),
        "User-Agent": Headers(os="random").generate()["User-Agent"],
        "X-Forwarded-For": Faker().ipv4(),
        "X-Network-Type": random.choice(["Wi-Fi", "4G", "5G"]),
        "X-Timezone": random.choice(pytz.all_timezones)
    }

def generate_random_data():
    screen_resolution = f"{random.choice([1280, 1366, 1440, 1600, 1920])}x{random.choice([720, 768, 900, 1080, 1200])}"
    fonts = ["Arial", "Times New Roman", "Verdana", "Helvetica", "Georgia", "Courier New"]
    webgl_info = {
        "vendor": random.choice(["Google Inc. (NVIDIA)", "Intel Inc.", "AMD Inc."]),
        "renderer": random.choice([
            "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)", "Intel(R) HD Graphics 630",
            "AMD Radeon RX 580", "NVIDIA GeForce RTX 3090", "Intel(R) Iris Plus Graphics 655",
            "AMD Radeon RX 5700 XT", "NVIDIA GeForce GTX 1660 Ti",
            "Intel(R) UHD Graphics 630 (Coffeelake)", "AMD Radeon RX 5600 XT",
            "NVIDIA Quadro RTX 8000", "Intel(R) HD Graphics 520",
            "AMD Radeon RX 480", "NVIDIA GeForce GTX 1050 Ti", "Intel(R) UHD Graphics 620", "NVIDIA GeForce RTX 3080", "AMD Radeon Vega 64",
            "NVIDIA Titan V", "AMD Radeon RX 6800 XT", "NVIDIA GeForce GTX 980 Ti", "Intel(R) Iris Xe Graphics"
        ])
    }
    return {
        "screen_resolution": screen_resolution,
        "color_depth": random.choice([16, 24, 32]),
        "fonts": random.sample(fonts, k=random.randint(3, len(fonts))),
        "webgl_info": webgl_info,
        "canvas_fingerprint": hashlib.md5(os.urandom(16)).hexdigest(),
        "plugins": random.sample(["Chrome PDF Viewer", "Google Docs Offline", "AdBlock", "Grammarly", "LastPass"], k=random.randint(2, 5))
    }

def start_userconfig():
    input_enable = None; input_token = None; input_chatid = None
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if config: return config['enable'], config['token'], config['chatid']
        except (json.JSONDecodeError, IOError):
            pass
    input_enable = get_valid_input("\033[1;94m是否启用 Telegram Bot [y/n]:\033[0m", lambda x: x.lower() in ['y', 'n'], "无效的输入,请输入 'y' 或 'n'.")
    input_token = input(f"{get_input_prompt()}\033[1;94m请输入Telegram Bot Token [默认使用 @Serv00Reg_Bot]:\033[0m")
    if input_token == "": input_token = '7594103635:AAEoQKB_ApJgDbfoVJm-gwW6e0VVS_a5Dl4'
    input_chatid = get_valid_input("\033[1;94m请输入Telegram Chat ID:\033[0m", lambda x: x.isdigit() and int(x) > 0, "无效的ChatID,请输入一个正整数.")
    with open(config_file, 'w') as f:
        json.dump({'enable': input_enable.strip(), 'token': input_token.strip(), 'chatid': input_chatid.strip()}, f)
        logger.success("配置文件配置成功!")
    return input_enable, input_token, input_chatid

def get_valid_input(prompt, validation_func, error_msg):
    while True:
        user_input = input(f"{get_input_prompt()}{prompt}")
        if validation_func(user_input):
            return user_input
        logger.error(f"\033[1;93m{error_msg}\033[0m")

def get_target_url():
    return get_valid_input("\033[1;94m请输入目标网站 URL (请以 https:// 开头):\033[0m", 
                           lambda x: x.startswith("https://"), 
                           "无效的 URL, 请重新输入以 'https://' 开头的有效地址.")

def start_task(input_email: str, target_url: str):
    id_retry = 1
    while True:
        try:
            random_headers = generate_random_headers()
            random_data = generate_random_data()
            User_Agent = random_headers["User-Agent"]
            Cookie = "csrftoken={}"
            url1 = f"{target_url}/offer/create_new_account"  # 使用用户提供的目标 URL
            headers = {"User-Agent": User_Agent, **random_headers}
            captcha_url = f"{target_url}/captcha/image/{{}}/"
            url3 = f"{target_url}/offer/create_new_account.json"
            header3 = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": f"{target_url}/offer/create_new_account",
                "Cookie": Cookie,
                "User-Agent": User_Agent,
                **random_headers
            }
            email = input_email
            usernames = get_user_name()
            _ = usernames.pop()
            first_name = _["name"]
            last_name = _["surname"]
            username = generate_random_username().lower()
            print(""), logger.info(f"{email} {first_name} {last_name} {username}")
            with requests.Session() as session:
                logger.info(f"获取网页信息 - 尝试次数: \033[1;94m{id_retry}\033[0m.")
                resp = session.get(url=url1, headers=headers, verify=False)
                headers = resp.headers
                content = resp.text
                csrftoken = re.findall(r"csrftoken=(\w+);", headers.get("set-cookie"))[0]
                header3["Cookie"] = header3["Cookie"].format(csrftoken)
                captcha_0 = re.findall(r'id=\"id_captcha_0\" name=\"captcha_0\" value=\"(\w+)\">', content)[0]
                captcha_retry = 1
                while True:
                    time.sleep(random.uniform(0.5, 1.2))
                    logger.info("获取验证码")
                    resp = session.get(url=captcha_url.format(captcha_0), headers=random_headers, verify=False)
                    time.sleep(random.uniform(0.5, 2))
                    content = resp.content
                    with open("static/image.jpg", "wb") as f:
                        f.write(content)
                    captcha_1 = ddddocr.DdddOcr(show_ad=False).classification(content).upper()
                    if bool(re.match(r'^[a-zA-Z0-9]{4}$', captcha_1)):
                        logger.info(f"识别验证码成功: \033[1;92m{captcha_1}\033[0m")
                    else:
                        logger.warning("\033[7m验证码识别失败,正在重试...\033[0m")
                        captcha_retry += 1
                        if captcha_retry > 200:
                            logger.error("验证码识别失败次数过多,退出重试.")
                            return
                        continue
                    data = f"csrfmiddlewaretoken={csrftoken}&first_name={first_name}&last_name={last_name}&username={username}&email={quote(email)}&captcha_0={captcha_0}&captcha_1={captcha_1}&question=free&tos=on{urlencode(random_data)}"
                    time.sleep(random.uniform(0.5, 1.2))
                    logger.info("请求信息")
                    resp = session.post(url=url3, headers=header3, data=data, verify=False)
                    logger.info(f'请求状态码: \033[1;93m{resp.status_code}\033[0m')
                    try:
                        content = resp.json()
                        if resp.status_code == 200 and len(content.keys()) == 2:
                            logger.success(f"\033[1;92m🎉 账户 {username} 已成功创建!\033[0m")
                            if enable == True: asyncio.run(send_message(f"Success!\nEmail: {input_email}\nUserName: {username}"))
                            return
                        else:
                            first_key = next(key for key in content if key not in ['__captcha_key', '__captcha_image_src'])
                            first_content = re.search(r"\['(.+?)'\]", str(content[first_key])).group(1)
                            logger.info(f"\033[36m{first_key.capitalize()}: {first_content}\033[0m")
                            if first_content == "An account has already been registered to this e-mail address.":
                                logger.warning(f"\033[1;92m该邮箱已存在,或账户 {username} 已成功创建🎉!")
                                if enable == True: asyncio.run(send_message(f"Success!\nEmail: {input_email}\nUserName: {username}"))
                                return
                    except JSONDecodeError:
                        logger.error("\033[7m获取信息错误,正在重试...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        continue
                    if content.get("captcha") and content["captcha"][0] == "Invalid CAPTCHA":
                        captcha_0 = content["__captcha_key"]
                        logger.warning("\033[7m验证码错误,正在重新获取...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        continue
                    if content.get("username") and content["username"][0] == "Maintenance time. Try again later.":
                        id_retry += 1
                        logger.error("\033[7m系统维护中,正在重试...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        break
                    if content.get("email") and content["email"][0] == "Enter a valid email address.":
                        logger.error("\033[7m无效的邮箱,请重新输入.\033[0m")
                        if enable == True: asyncio.run(send_message(f"Error!\nEmail: {input_email}\nMessage: 无效的邮箱,请重新输入."))
                        time.sleep(random.uniform(0.5, 1.2))
                        return
                    else:
                        if enable == True: asyncio.run(send_message(f"Success!\nEmail: {input_email}\nUserName: {username}"))
                        return
        except Exception as e:
            logger.error(f"\033[7m发生异常:{e},正在重新开始任务...\033[0m")
            time.sleep(random.uniform(0.5, 1.2))

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    target_url = get_target_url()  # 获取目标网站 URL
    resp = requests.get(target_url, verify=False)
    response = requests.get('https://ping0.cc/geo', verify=False)
    print(f"=============================\n\033[96m{response.text[:200]}\033[0m=============================")
    match = re.search(r'(\d+)\s*/\s*(\d+)', resp.text).group(0).replace(' ', '') if resp.status_code == 200 and re.search(r'(\d+)\s*/\s*(\d+)', resp.text) else (logger.error('请求失败,请检查代理IP是否封禁!'), exit())
    logger.info(f"\033[1;95m1. 启动任务\033[0m | \033[1;93m2. 编辑配置\033[0m | \033[1;5;32m当前注册量:{match}\033[0m")
    while True:
        input_option = input_option_menu()
        if input_option == '1':
            logger.info("\033[91m输入邮箱开始自动任务,退出快捷键Ctrl+C.\033[0m"); enable = False
            while True:
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        if config['enable'] == 'y':
                            input_token, input_chatid = config['token'], config['chatid']; enable = True; break
                        else: break
                except (FileNotFoundError, json.JSONDecodeError): break
            while True:
                input_email = get_valid_input("\033[1;94m请输入邮箱:\033[0m", lambda x: '@' in x, "无效的邮箱,请重新输入.")
                if '@' not in input_email:
                    logger.error("\033[1;93m无效的邮箱,请重新输入.\033[0m")
                    continue
                start_task(input_email, target_url)  # 将 target_url 传递给 start_task
        elif input_option == '2':
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_content = f.read()
                if config_content.startswith("{") and config_content.endswith("}"):
                    try:
                        config = json.loads(config_content)
                    except json.JSONDecodeError:
                        logger.error("\033[1;92m初始化运行未检测到配置文件.\033[0m")
                os.remove(config_file)
            else:
                logger.error("\033[1;92m初始化运行未检测到配置文件.\033[0m")
            input_enable, input_token, input_chatid = start_userconfig();
            continue
