import json
import time
import argparse
import os
import logging
import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 日志记录配置 ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- 从 utils 导入必要的模块 ---
from utils import reserve, get_user_credentials

# --- 全局配置 ---
SLEEPTIME = 0.2  # 每次抢座的间隔
LOGIN_TIME = "21:29:30" # 开始登录的时间
RESERVE_TIME = "22:00:00" # 开始预约的时间
ENDTIME = "22:01:00"  # 结束预约的时间
ENABLE_SLIDER = True  # 是否有滑块验证
MAX_ATTEMPT = 5  # 最大尝试次数
RESERVE_NEXT_DAY = False  # 预约明天而不是今天的

# --- 时间处理函数 (使用pytz确保时区正确) ---
def get_current_time():
    """获取当前北京时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime("%H:%M:%S")

def get_current_dayofweek():
    """获取当前星期几（英文）"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime("%A")

def wait_until(target_time_str):
    """等待直到指定的北京时间"""
    logging.info(f"等待直到 {target_time_str}...")
    tz = pytz.timezone('Asia/Shanghai')
    while True:
        now_str = datetime.datetime.now(tz).strftime("%H:%M:%S")
        if now_str >= target_time_str:
            logging.info(f"到达指定时间 {target_time_str}，继续执行。")
            break
        time.sleep(0.5)

# --- 核心逻辑函数 ---

def login_user(username, password):
    """登录单个用户并返回会话对象"""
    logging.info(f"----------- 正在登录用户 {username} -----------")
    try:
        s = reserve(
            sleep_time=SLEEPTIME,
            max_attempt=MAX_ATTEMPT,
            enable_slider=ENABLE_SLIDER,
            reserve_next_day=RESERVE_NEXT_DAY,
        )
        s.get_login_status()
        login_result = s.login(username, password)
        if not login_result[0]:
            logging.error(f"用户 {username} 登录失败: {login_result[1]}")
            return None
        
        s.requests.headers.update({"Host": "office.chaoxing.com"})
        logging.info(f"用户 {username} 登录成功。")
        return s
    except Exception as e:
        logging.error(f"用户 {username} 登录过程中发生异常: {str(e)}")
        return None

def login_all_users(users, usernames_env, passwords_env, action):
    """并发登录所有用户并缓存会话"""
    session_cache = {}
    usernames_list = usernames_env.split(',') if action else []
    passwords_list = passwords_env.split(',') if action else []

    with ThreadPoolExecutor(max_workers=len(users)) as executor:
        future_to_user_config_name = {}
        for index, user_config in enumerate(users):
            # 始终使用 config.json 中的 username 作为内部唯一标识符
            config_username = user_config["username"]
            
            # 根据模式确定实际用于登录的用户名和密码
            login_username = ""
            login_password = ""
            if action:
                if index < len(usernames_list) and index < len(passwords_list):
                    login_username = usernames_list[index]
                    login_password = passwords_list[index]
                else:
                    logging.error(f"环境变量中的用户凭证数量与配置文件不匹配，跳过索引 {index}。")
                    continue
            else:
                login_username = user_config["username"]
                login_password = user_config["password"]
            
            future = executor.submit(login_user, login_username, login_password)
            # 将 future 映射到 config.json 中的用户名
            future_to_user_config_name[future] = config_username

        for future in as_completed(future_to_user_config_name):
            # 获取 config.json 中的用户名
            config_username = future_to_user_config_name[future]
            session = future.result()
            if session:
                # 使用 config.json 中的用户名作为 key 来存储 session
                session_cache[config_username] = session
    
    logging.info(f"登录流程结束，共 {len(session_cache)} 个用户成功登录。")
    return session_cache


def process_single_task(session, username, task, action):
    """使用已登录的会话处理单个预约任务"""
    times, roomid, seatid, daysofweek = task.values()
    current_dayofweek = get_current_dayofweek()

    if current_dayofweek not in daysofweek:
        # 当天不是预约日，直接返回成功以跳过此任务
        return True 

    logging.info(f"----------- {username} -- {times} -- {seatid} 尝试预约 -----------")
    try:
        # 修复：将 action 参数正确传递给 submit 函数
        suc = session.submit(times, roomid, seatid, action)
        if suc:
            logging.info(f"用户 {username} 任务 {times} 预约成功!")
        else:
            logging.warning(f"用户 {username} 任务 {times} 预约失败。")
        return suc
    except Exception as e:
        logging.error(f"用户 {username} 任务 {times} 预约时发生异常: {str(e)}")
        return False

def reserve_all_tasks(session_cache, users, action):
    """并发处理所有用户的预约任务"""
    with ThreadPoolExecutor(max_workers=min(len(users) * 4, 16)) as executor:
        future_to_task_info = {}
        for user_config in users:
            username = user_config["username"]
            session = session_cache.get(username)

            if not session:
                # 这个警告现在只会在登录真正失败时出现
                logging.warning(f"用户 {username} 没有有效的登录会话，跳过其所有任务。")
                continue

            for task in user_config["tasks"]:
                # 修复：将 action 参数传递给 process_single_task
                future = executor.submit(process_single_task, session, username, task, action)
                future_to_task_info[future] = f"用户 {username} - 时间 {task['time']}"
        
        # 检查所有任务的结果
        all_successful = True
        for future in as_completed(future_to_task_info):
            task_info = future_to_task_info[future]
            try:
                result = future.result()
                if not result:
                    all_successful = False
                    logging.error(f"任务 {task_info} 未能成功完成。")
            except Exception as e:
                all_successful = False
                logging.error(f"任务 {task_info} 执行时出现严重错误: {str(e)}")
        
        return all_successful

# --- 主函数和调试函数 ---

def main(users, action=False):
    logging.info("程序启动...")
    
    # 步骤 1: 等待到登录时间
    wait_until(LOGIN_TIME)
    
    # 步骤 2: 登录所有用户
    usernames_env, passwords_env = get_user_credentials(action) if action else ("", "")
    session_cache = login_all_users(users, usernames_env, passwords_env, action)

    if not session_cache:
        logging.error("没有任何用户登录成功，程序终止。")
        return

    # 步骤 3: 等待到预约时间
    wait_until(RESERVE_TIME)

    # 步骤 4: 开始循环预约
    logging.info("开始执行预约任务...")
    current_time = get_current_time()
    attempt_times = 0
    while current_time < ENDTIME:
        attempt_times += 1
        logging.info(f"--- 第 {attempt_times} 轮预约尝试 ---")
        
        # 修复：将 action 参数传递给 reserve_all_tasks
        all_done = reserve_all_tasks(session_cache, users, action)
        
        current_time = get_current_time()
        logging.info(f"当前时间 {current_time}，预约结束时间 {ENDTIME}")

        if all_done:
            logging.info("所有已配置的当日任务均已成功预约！程序结束。")
            return
        
        time.sleep(SLEEPTIME)
    
    logging.info("已到达结束时间，程序终止。")


def debug(users, action=False):
    logging.info("--- 调试模式启动 ---")
    logging.info(
        f"全局设置: \nSLEEPTIME: {SLEEPTIME}\nLOGIN_TIME: {LOGIN_TIME}\nRESERVE_TIME: {RESERVE_TIME}\nENDTIME: {ENDTIME}\nENABLE_SLIDER: {ENABLE_SLIDER}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}"
    )
    
    # 在调试模式下，我们直接登录并执行一次预约
    usernames_env, passwords_env = get_user_credentials(action) if action else ("", "")
    session_cache = login_all_users(users, usernames_env, passwords_env, action)

    if not session_cache:
        logging.error("调试模式下没有任何用户登录成功，请检查配置和凭证。")
        return
        
    logging.info("登录成功，现在开始执行一次预约流程...")
    # 修复：将 action 参数传递给 reserve_all_tasks
    reserve_all_tasks(session_cache, users, action)
    logging.info("--- 调试模式结束 ---")


def get_roomid(args1, args2):
    username = input("请输入用户名：")
    password = input("请输入密码：")
    s = reserve(
        sleep_time=SLEEPTIME,
        max_attempt=MAX_ATTEMPT,
        enable_slider=ENABLE_SLIDER,
        reserve_next_day=RESERVE_NEXT_DAY,
    )
    session = login_user(username, password)
    if session:
        encode = input("请输入deptldEnc：")
        session.roomid(encode)

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    parser = argparse.ArgumentParser(prog="Chao Xing seat auto reserve")
    parser.add_argument("-u", "--user", default=config_path, help="user config file")
    parser.add_argument(
        "-m",
        "--method",
        default="reserve",
        choices=["reserve", "debug", "ro    om"],
        help="for debug",
    )
    parser.add_argument(
        "-a",
        "--action",
        action="store_true",
        help="use --action to enable in github action",
    )
    args = parser.parse_args()
    func_dict = {"reserve": main, "debug": debug, "room": get_roomid}
    try:
        with open(args.user, "r", encoding="utf-8") as data:
            usersdata = json.load(data)["reserve"]
    except FileNotFoundError:
        logging.error(f"错误：找不到配置文件 {args.user}")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"错误：配置文件 {args.user} 格式不正确。")
        exit(1)

    func_dict[args.method](usersdata, args.action)
