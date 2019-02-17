import datetime

import time
import data.ui_data as ui
from selenium import webdriver
import variable
import data.bitmex_data as bitmex_data
import wechat_notifier as wechat
import strategy.strategy_core as strategy
import api.user_position as position
import api.core as api
import traceback

THRESHOLD_SHIFT = 0


def init_browser():
    browser = webdriver.Firefox()
    browser.get(variable.TARGET_SITE_URL)
    print(variable.TARGET_SITE_URL)
    ui.init(browser)


def start_monitor():
    temp_bitmex_sell_1 = 0
    temp_bitmex_buy_1 = 0
    temp_buy_2_price = 0
    temp_sell_2_price = 0
    while True:
        if bitmex_data.last_price < 0:
            wechat.send_message('bitmex掉线了')
            break
        elif bitmex_data.last_price == 0:
            print('bitmex暂时没有数据')
            time.sleep(3)
            continue
        start_time = time.time()
        buy_2_price = ui.get_buy_price(2)
        sell_2_price = ui.get_sell_price(2)
        if buy_2_price < 0 or sell_2_price < 0:
            continue
        ui_time = time.time() - start_time
        bitmex_sell_1, bitmex_buy_1 = bitmex_data.get_quote_1()
        data_time = time.time() - start_time - ui_time
        if temp_bitmex_sell_1 != bitmex_sell_1 or temp_bitmex_buy_1 != bitmex_buy_1 \
                or temp_buy_2_price != buy_2_price or temp_sell_2_price != sell_2_price:
            strategy.receive_price_change(buy_2_price, sell_2_price)
            print(datetime.datetime.now(), 'ws:('+str([bitmex_buy_1, bitmex_sell_1])+')',
                  # 'web:'+str([bitmex_last_price, bitmex_sell_1, bitmex_buy_1]),
                  'target卖买二:'+str([buy_2_price, sell_2_price]), position.get_target_position().print(),
                  '耗时:', int((time.time() - start_time)*1000), int(ui_time*1000), int(data_time*1000))

        temp_bitmex_sell_1 = bitmex_sell_1
        temp_bitmex_buy_1 = bitmex_buy_1
        temp_buy_2_price = buy_2_price
        temp_sell_2_price = sell_2_price


def ready():
    init_browser()
    while True:
        input_text = input('开始监控:')
        if input_text == 'y':
            pass
        elif input_text == 'biex':
            try:
                position.set_target_position(api.get_site_api().get_user_position())
                bitmex_data.open_bitmex_asyn()
                start_monitor()
            except Exception as e:
                traceback.print_exc()
                wechat.send_message(str(e))