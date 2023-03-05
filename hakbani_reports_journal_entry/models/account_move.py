# -*- coding: utf-8 -*-

from odoo import models


class AccMoveReport(models.Model):
    _inherit = 'account.move'

    def print_journal_entry(self):
        return self.env.ref('hakbani_payment_receipt.action_report_journal_entry').report_action(self)