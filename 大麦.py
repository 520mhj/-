# encoding: utf-8
 
from datetime import datetime
import os
import pickle
 
import selenium.webdriver.remote.webelement
from selenium import webdriver
from selenium.webdriver import ActionChains
 
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
 
import json
 
 
class Book_TicketH5(object):
    def __init__(self):
        self.update_cfg()
        self.chrome_options = webdriver.ChromeOptions()
        # 如果选座已经登陆过 或者不选座 则默认关闭图片
        if self.imagesEnabled:
            self.chrome_options.add_argument("--blink-settings=imagesEnabled=true")
        else:
            self.chrome_options.add_argument("--blink-settings=imagesEnabled=false")
 
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-setuid-sandbox")
        self.chrome_options.add_argument("--disable-web-security")
        # self.chrome_options.add_argument('--user-data-dir=请填写绝对路径')
        # 禁用GPU加速
        self.chrome_options.page_load_strategy = 'eager'
 
        # self.chrome_options.add_argument('--proxy-server=127.0.0.1:proxy=7890')
        # 设置无头浏览器 无界面浏览器
        self.driver = webdriver.Chrome(executable_path=self.driver_path, options=self.chrome_options)  # 此项稳定版打开
        #self.driver = webdriver.Chrome(executable_path="C:\Program Files\Google\Chrome\Application\chromedriver.exe",
                                       #options=self.chrome_options)  # 默认谷歌浏览器, 指定下驱动的位置
        # self.driver = webdriver.Chrome()  # 默认谷歌浏览器
        self.driver.maximize_window()
 
    def update_cfg(self):
        with open("C:\\Users\\DELL\\Desktop\\configh5.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # 首页
            self.damai_url = cfg["damai_url"]
            # 登录界面
            self.login_url = cfg["login_url"]
            # 购票界面url
            self.book_url = cfg['book_url']
 
            self.price = cfg['price']
            self.name_num = cfg['name_num']
            self.buy_num = cfg['buy_num']
            self.session = cfg['session']
 
            self.driver_path = cfg['driver_path']
 
            self.status = 0  # 是否登录的状态 0是未登录，1是登录
 
            self.current_num = 1  # 当前第几次抢票
            self.playering = 1  # 可以抢票
            self.num = cfg['num']
 
            self.rush_time = cfg['date_time']
 
            self.xuanzuo = cfg['xuanzuo'] == 1  # 选座信息 演出界面会写能不能选座
            self.shiming = cfg['shiming'] == 1  # 实名信息 购买须知会写实名限制 如果是不需要实名的会写无需实名
            self.imagesEnabled = cfg['imagesEnabled'] == 1  # 1=显示图片 0 = 不显示图片
            self.jianlou = cfg["jianlou"] == 1
            self.gpu = cfg["gpu"] == 1
 
    def get_cookie(self):
        try:
            # 先进入登录页面进行登录
            print("------开始登录------")
            self.driver.get(self.login_url)
            time.sleep(60)  # 不加好像也可以
 
            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
            print("------Cookie保存成功------")
        except Exception as e:
            raise e
 
    def set_cookie(self):
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))  # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.damai.cn',  # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print('------载入Cookie------')
        except Exception as e:
            print(f"------cookie 设置失败，原因：{str(e)}------")
 
    def login(self):
        if not os.path.exists('cookies.pkl'):  # 如果不存在cookie.pkl,就登录获取一下
            self.get_cookie()
        else:  # 存在就设置下cookie
            self.driver.get(self.damai_url)
            self.set_cookie()
 
 
 
 
    def select_session(self):
        # 场次选择
        buy = self.driver.find_element(By.XPATH, '//*[@id="bottom"]/div[2]/div[1]/div[1]/div/div')
        buy.click()
        bui_dm_sku_modules = self.driver.find_elements(By.CLASS_NAME, 'bui-dm-sku-module')
        try:
            while len(bui_dm_sku_modules) == 0:
                time.sleep(0.1)
                buy.click()
                bui_dm_sku_modules = self.driver.find_elements(By.CLASS_NAME, 'bui-dm-sku-module')
        except Exception as e:
            print(e)
            return
        bui_dm_sku_module = bui_dm_sku_modules[0]
        times_list = WebDriverWait(bui_dm_sku_module, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, './div[2]/div[2]/div')))
        print("时间数量:{}".format(len(times_list)))
        if len(self.session) == 1:
            try:
                ActionChains(self.driver).move_to_element_with_offset(times_list[self.session[0] - 1], 5,
                                                                      5).click().perform()
            except Exception as e:
                print(e)
            self.select_price(bui_dm_sku_module)
        else:
            for s in self.session:
                times_list[s - 1].click()
                if self.select_price(bui_dm_sku_module):
                    return
                    # 票价选择
 
    def select_price(self, bui_dm_sku_module: webdriver.remote.webelement.WebElement):
        try:
            """
            选择票价挡位
            :return:
            """
            price_list = WebDriverWait(bui_dm_sku_module, 10, 0.01).until(
                EC.presence_of_all_elements_located((By.XPATH, './div[3]/div[2]/div')))
            # price_list = bui_dm_sku_module.find_elements(By.XPATH,'./div[3]/div[2]/div')
            # 根据优先级选择一个可行票价
            # 获取场次
            print(f"------票价档次数量：{len(price_list)}------")
            num = 0
            for i in self.price:
                print(f"------正在抢购第 {str(i)} 挡位票------")
                try:
                    quehuo = price_list[i - 1].find_elements(By.XPATH, "./div/div/div/div[1]")
                    if len(quehuo) > 0:
                        print(f"------第 {str(i)} 档票已经售完------")
                        num += 1
                        if num < len(self.price):
                            continue
                        else:
                            raise Exception("你想抢的票已售完")
                    if self.xuanzuo:
                        # 选座
                        try:
                            # ActionChains(self.driver).move_to_element_with_offset(price_list[i - 1], 5,
                            #                                                       5).click().perform()
                            js = 'document.getElementsByClassName("sku-pop-wrapper")[0].scrollTop = document.getElementsByClassName("sku-pop-wrapper")[0].scrollHeight'
                            self.driver.execute_script(js)
                            price_list[i - 1].click()                      
                        except Exception as e:
                            print(e)
                        button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, 'number-edit-bg')))
 
                        while int(self.driver.find_elements(By.CLASS_NAME, 'total')[0].text[0]) < int(self.buy_num):
                            button[1].click()
                        button2 = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, 'sku-footer-buy-button')))
                        button2[0].click()
                    else:
                        # 确定
                        price_list[i - 1].click()
                        bui_dm_sku_module.find_element(By.XPATH, "./div[4]/div[2]/div[2]").click()
                    return True
                except:
                    raise Exception("你想抢的票已售完")
        except:
            raise Exception("你想抢的票已售完")
 
    def select_buy_name(self):
        try:
            if self.driver.title == "登录":
                raise Exception("cookie 过期")
 
            if not self.shiming:
                return
            viewer = WebDriverWait(self.driver, 10, 0.001).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'viewer')))
            # 获取选中按钮
            tog_divs = WebDriverWait(viewer, 10, 0.001).until(
                EC.presence_of_all_elements_located((By.XPATH, "./div/div")))
            print("开始选择观演人")
            click_1 = True
            while click_1:
                try:
                    # 循环遍历数量默认从上到下
                    for i in range(self.buy_num):
                        tog: webdriver.remote.webelement.WebElement = tog_divs[self.name_num[i] - 1]
                        self.driver.execute_script("arguments[0].click();", tog)
                        print(f"选择{self.name_num[i] - 1}号观演人")
                    click_1 = False
                except Exception as e:
                    raise e
        except Exception as e:
            raise e
 
    def submit(self):
        try:
            submit_click = WebDriverWait(self.driver, 5, 0.001).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="dmOrderSubmitBlock_DmOrderSubmitBlock"]/div[2]/div/div[2]/div[3]/div[2]')))
            click_2 = True
            while click_2:
                try:
                    submit_click.click()
                    click_2 = False
                except Exception as e:
                    pass
        except Exception as e:
            print(e)
            raise e
 
    def quit(self):
        while self.driver.title != "支付宝 - 网上支付 安全快速！":
            time.sleep(1)
        self.driver.quit()
 
    def rush_ticket(self):
        try:
            # 直接来到演唱会购票界面
            self.driver.get(self.book_url)
            # 如果是缺货登记 或者是 开枪 则继续刷新
            buy = self.driver.find_element(By.XPATH, '//*[@id="bottom"]/div[2]/div[1]/div[1]/div/div')
            strs = ["缺货登记", "即将开抢", "即将开抢 预选场次", ]
            while buy.text in strs:
                time.sleep(0.1)
                self.driver.get(self.book_url)
 
            # 选择档和票价
            self.select_session()
 
            # 手动选座
            #self.select_sear()
 
            print("开始选择购买人")
            # 选择购买人
            self.select_buy_name()
 
            # 座位
 
            print("提交订单")
            # 点击提交订单
            self.submit()
 
        except Exception as e:
            raise e
 
    def run(self):
        try:
            # 登录
            self.login()
            # 判断抢票时间是否到达
            print("------等待抢票时间点到来，进行抢票------")
            while self.rush_time - time.time() > 0.5:  # 提前0.2-0.5秒开始抢
                time.sleep(0.5)
                print(f"剩余时间:{self.rush_time - time.time()}秒")
 
            start_time = time.time()
            print(f"------开始抢票，时间点：{str(datetime.now())}------")
 
            # 抢票
            loop = 1
            for i in range(self.num):
                try:
                    print(f"------正在进行第 {str((i + 1))} 轮抢票------")
                    self.rush_ticket()
                    break
                except Exception as e:
                    if loop == self.num:
                        raise e
                    loop += 1
                    pass
            # self.rush_ticket()
 
            end_time = time.time()
            print(f"抢票结束，时间点：{str(datetime.now())}")
            print(f"抢票总时长：{str((end_time - start_time))}， 此时长不包括登录时间")
            print("抢票成功，抓紧去订单中付款！！")
 
            time.sleep(999)
 
        except Exception as e:
            if self.jianlou:
                self.start_jianlou()
            else:
                print(f"******抢票失败，原因：{str(e)}******")
 
    def start_jianlou(self):
        # 判断抢票时间是否到达
        print("------开始捡漏------")
        # 每隔5秒 进行一次抢票
        index = 0
        while True:
            index += 1
            print(f"-----第{index}次捡漏-----")
            time.sleep(5)
            try:
                self.rush_ticket()
            except Exception as e:
                print(f"******抢票失败，原因：{str(e)}******")
                continue
        print(f"抢票结束，时间点：{str(datetime.now())}")
        print("请尽快付款")
 
 
if __name__ == '__main__':
    book = Book_TicketH5()
    book.run()
