# -*- coding: utf-8 -*-
from odoo import api, fields, models
import base64
from random import choice
from string import digits
import itertools
from werkzeug import url_encode
import pytz
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from odoo.addons.resource.models.resource_mixin import timezone_datetime

import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import itemgetter

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date


class account_move(models.Model):
	_inherit = "account.move"
	
	def _post(self, soft=True):
		"""Post/Validate the documents.

		Posting the documents will give it a number, and check that the document is
		complete (some fields might not be required if not posted but are required
		otherwise).
		If the journal is locked with a hash table, it will be impossible to change
		some fields afterwards.

		:param soft (bool): if True, future documents are not immediately posted,
			but are set to be auto posted automatically at the set accounting date.
			Nothing will be performed on those documents before the accounting date.
		:return Model<account.move>: the documents that have been posted
		"""
		if soft:
			future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
			future_moves.auto_post = True
			for move in future_moves:
				msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
				move.message_post(body=msg)
			to_post = self - future_moves
		else:
			to_post = self

		# `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
		#if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
			#raise AccessError(_("You don't have the access rights to post an invoice."))
		for move in to_post:
			if move.partner_bank_id and not move.partner_bank_id.active:
				raise UserError(_("The recipient bank account link to this invoice is archived.\nSo you cannot confirm the invoice."))
			if move.state == 'posted':
				raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
			if not move.line_ids.filtered(lambda line: not line.display_type):
				raise UserError(_('You need to add a line before posting.'))
			if move.auto_post and move.date > fields.Date.context_today(self):
				date_msg = move.date.strftime(get_lang(self.env).date_format)
				raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
			if not move.journal_id.active:
				raise UserError(_(
					"You cannot post an entry in an archived journal (%(journal)s)",
					journal=move.journal_id.display_name,
				))

			if not move.partner_id:
				if move.is_sale_document():
					raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
				elif move.is_purchase_document():
					raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

			if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
				raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

			if move.display_inactive_currency_warning:
				raise UserError(_("You cannot validate an invoice with an inactive currency: %s",
								  move.currency_id.name))

			# Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
			# lines are recomputed accordingly.
			# /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
			# environment.
			if not move.invoice_date:
				if move.is_sale_document(include_receipts=True):
					move.invoice_date = fields.Date.context_today(self)
					move.with_context(check_move_validity=False)._onchange_invoice_date()
				elif move.is_purchase_document(include_receipts=True):
					raise UserError(_("The Bill/Refund date is required to validate this document."))

			# When the accounting date is prior to the tax lock date, move it automatically to today.
			# /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
			# environment.
			if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tax_tag_ids):
				move.date = move._get_accounting_date(move.invoice_date or move.date, True)
				move.with_context(check_move_validity=False)._onchange_currency()

		# Create the analytic lines in batch is faster as it leads to less cache invalidation.
		to_post.mapped('line_ids').create_analytic_lines()
		to_post.write({
			'state': 'posted',
			'posted_before': True,
		})

		for move in to_post:
			move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

			# Compute 'ref' for 'out_invoice'.
			if move._auto_compute_invoice_reference():
				to_write = {
					'payment_reference': move._get_invoice_computed_reference(),
					'line_ids': []
				}
				for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
					to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
				move.write(to_write)

		for move in to_post:
			if move.is_sale_document() \
					and move.journal_id.sale_activity_type_id \
					and (move.journal_id.sale_activity_user_id or move.invoice_user_id).id not in (self.env.ref('base.user_root').id, False):
				move.activity_schedule(
					date_deadline=min((date for date in move.line_ids.mapped('date_maturity') if date), default=move.date),
					activity_type_id=move.journal_id.sale_activity_type_id.id,
					summary=move.journal_id.sale_activity_note,
					user_id=move.journal_id.sale_activity_user_id.id or move.invoice_user_id.id,
				)

		customer_count, supplier_count = defaultdict(int), defaultdict(int)
		for move in to_post:
			if move.is_sale_document():
				customer_count[move.partner_id] += 1
			elif move.is_purchase_document():
				supplier_count[move.partner_id] += 1
		for partner, count in customer_count.items():
			(partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
		for partner, count in supplier_count.items():
			(partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

		# Trigger action for paid invoices in amount is zero
		to_post.filtered(
			lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
		).action_invoice_paid()

		# Force balance check since nothing prevents another module to create an incorrect entry.
		# This is performed at the very end to avoid flushing fields before the whole processing.
		to_post._check_balanced()
		return to_post