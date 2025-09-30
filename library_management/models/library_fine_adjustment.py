# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryFineAdjustment(models.Model):
    _name = 'library.fine.adjustment'
    _description = 'LibraryFineAdjustment'

    name = fields.Char(string='Customer Name', required=True)
    active = fields.Boolean(default=True)
    borrow_id = fields.Many2one('library.borrow', 'Borrow Reference')
    adjustment_date = fields.Date(string='Adjustment Date', default=fields.Date.today)
    reason = fields.Char(string='Reason')
    amount = fields.Float(string='Amount', default=0.0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], default='draft', string='Status')

