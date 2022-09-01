# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

from datetime import datetime
from dateutil import relativedelta

_logger = logging.getLogger(__name__)


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.onchange('holiday_status_id')
    def _onchange_user_employees(self):
        res = {}
        if self.user_has_groups('hr_holidays.group_hr_holidays_user') is False:
            user_employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            employee_ids = user_employee.child_ids.ids + [user_employee.id]
            res['domain'] = {'employee_id': [('id', 'in', employee_ids)]}
        return res


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    remaining_leaves = fields.Float(
        # compute="_compute_leaves",
        string="Remaining leaves",
        readonly=True,
        store=True
    )

    @api.onchange('holiday_status_id', 'employee_id')
    def _compute_leaves(self):
        data_days = {}
        employee_id = self.employee_id.id

        if employee_id:
            data_days = (
                self.holiday_status_id.get_employees_days(employee_id)[employee_id[0]] if isinstance(employee_id,
                                                                                                     list) else
                self.holiday_status_id.get_employees_days([employee_id])[employee_id])

        for leave in self:
            result = data_days.get(leave.holiday_status_id.id, {})
            leave.remaining_leaves = result.get('remaining_leaves', 0)
            # import pdb
            # pdb.set_trace()

    @api.onchange('holiday_status_id')
    def _onchange_user_employees(self):
        res = {}
        if self.user_has_groups('hr_holidays.group_hr_holidays_user') is False:
            user_employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            employee_ids = user_employee.child_ids.ids + [user_employee.id]
            res['domain'] = {'employee_id': [('id', 'in', employee_ids)]}
        return res
