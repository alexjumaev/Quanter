from strategy.base_strategy import AbsStrategy
import api.user_position as user_position
import api.core as api
import data.ui_data as ui_data
import data.bitmex_data as bitmex_data
import const, variable

RATIO = 10


def get_cal_amount(position):
    if position.amount <= 0:
        target_amount = 0
    else:
        if position.side == const.BUY:
            target_amount = position.amount
        else:
            target_amount = -position.amount
    return target_amount


class HedgeStrategy(AbsStrategy):
    bitmex_buy_1_price = -1
    bitmex_sell_1_price = -1

    def check_need_close(self):
        if self.bitmex_buy_1_price <= 0 or self.bitmex_sell_1_price <= 0:
            return
        target_position = user_position.get_target_position()
        bm_position = user_position.get_bm_position()
        target_amount = get_cal_amount(target_position) * RATIO
        bm_amount = get_cal_amount(bm_position)
        available_amount = target_amount + bm_amount
        if available_amount == 0:
            return
        if available_amount < 0:
            side = const.SELL
        else:
            side = const.BUY
        available_amount = abs(available_amount)

        if side == const.BUY:
            if (self.bitmex_sell_1_price - sell_1_price <= variable.CLOSE_THRESHOLD) \
                    and (sell_1_price - buy_1_price <= variable.CLOSE_DIFF):
                buy_1_amount = ui_data.get_buy_amount(1)
                if buy_1_amount < 0:
                    buy_1_amount = 999999
                api.get_site_api().close_order_async(buy_1_price, min(available_amount, buy_1_amount),
                                                     const.SELL, position.position_id)
        elif position.side == const.SELL:
            if (buy_1_price - self.bitmex_buy_1_price <= variable.CLOSE_THRESHOLD) \
                    and (sell_1_price - buy_1_price <= variable.CLOSE_DIFF):
                sell_1_amount = ui_data.get_sell_amount(1)
                if sell_1_amount < 0:
                    sell_1_amount = 999999
                    api.get_site_api().close_order_async(sell_1_price, min(sell_1_amount, available_amount),
                                                         const.BUY, position.position_id)

    def check_need_open(self, sell_2_price, buy_2_price):
        result = False
        if self.bitmex_sell_1_price - sell_2_price >= variable.THRESHOLD:
            sell_3_price = ui_data.get_sell_price(3)
            if sell_3_price > 0 and self.bitmex_sell_1_price - sell_3_price >= variable.THRESHOLD:
                api.get_site_api().open_order_async(sell_3_price, variable.MAX_AMOUNT, const.BUY)
            else:
                api.get_site_api().open_order_async(sell_2_price, variable.MAX_AMOUNT, const.BUY)
            result = True
        elif buy_2_price - self.bitmex_buy_1_price >= variable.THRESHOLD:
            buy_3_price = ui_data.get_buy_price(3)
            if buy_3_price > 0 and buy_3_price - self.bitmex_buy_1_price >= variable.THRESHOLD:
                api.get_site_api().open_order_async(buy_3_price, variable.MAX_AMOUNT, const.SELL)
            else:
                api.get_site_api().open_order_async(buy_2_price, variable.MAX_AMOUNT, const.SELL)
            result = True
        return result

    def on_price_change(self, sell_2, buy_2):
        if variable.THRESHOLD < 0 or variable.CLOSE_THRESHOLD < 0:
            print('threshold need init')
            return

        self.bitmex_sell_1_price, self.bitmex_buy_1_price = bitmex_data.get_quote_1()
        if not self.check_need_open(sell_2, buy_2):
            self.check_need_close()