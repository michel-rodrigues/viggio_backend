from decimal import Decimal

from .models import AgencyProfit, TalentProfit


# TODO: criar um factory de Order


class TalentProfitFactory:

    def __init__(self, view_profit_percentage, view_default_profit_percentage):
        self.view_profit_percentage = view_profit_percentage
        self.view_default_profit_percentage = view_default_profit_percentage

    def _get_profit_percentage_value(self, order):
        profit_percentage = self.view_profit_percentage(order.talent_id)
        if not profit_percentage:
            profit_percentage = self.view_default_profit_percentage()
        return profit_percentage.value

    def _calculate_profit(self, shoutout_price, profit_percentage):
        return (shoutout_price * profit_percentage).quantize(Decimal('1.00'))

    def __call__(self, order):
        shoutout_price = order.charge.amount_paid
        profit_percentage = self._get_profit_percentage_value(order)
        profit = self._calculate_profit(shoutout_price, profit_percentage)
        profit = TalentProfit(
            talent_id=order.talent_id,
            order_id=order.id,
            shoutout_price=shoutout_price,
            profit_percentage=profit_percentage,
            profit=profit,
            paid=False,
        )
        return profit


class AgencyProfitFactory:

    def __init__(self, view_profit_percentage):
        self.view_profit_percentage = view_profit_percentage

    def _get_profit_percentage_value(self, agency_id):
        profit_percentage = self.view_profit_percentage(agency_id)
        return profit_percentage.value

    def _calculate_profit(self, shoutout_price, profit_percentage):
        return (shoutout_price * profit_percentage).quantize(Decimal('1.00'))

    def __call__(self, order, agency_id):
        shoutout_price = order.charge.amount_paid
        profit_percentage = self._get_profit_percentage_value(agency_id)
        profit = self._calculate_profit(shoutout_price, profit_percentage)
        profit = AgencyProfit(
            agency_id=agency_id,
            order_id=order.id,
            shoutout_price=shoutout_price,
            profit_percentage=profit_percentage,
            profit=profit,
            paid=False,
        )
        return profit
