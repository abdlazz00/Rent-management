# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryBorrow(models.Model):
    _name = 'library.borrow'
    _description = 'LibraryBorrow'

    name = fields.Char(string='Borrowing Reference', required=True)
    active = fields.Boolean(default=True)
    member_id = fields.Many2one('res.partner', string='Member', required=True)
    borrow_date = fields.Date(string='Borrow Date', required=True, default=fields.Date.today)
    return_due_date = fields.Date(string='Return Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('borrowed', 'Dipinjam'),
        ('returned', 'Dikembalikan'),
        ('overdue', 'Terlambar'),
        ('cancelled', 'Dibatalkan'),
    ], default='draft', string='Status')
    is_overdue = fields.Boolean(string='Is Overdue', default=False)
    total_books = fields.Integer(string='Total Books', default=0)
    total_fine = fields.Float('Total Fine', default=0.0)
    borrow_line_ids = fields.One2many('library.borrow.lines', 'borrow_id', string='Lines')


class LibraryBorrowLines(models.Model):
    _name = 'library.borrow.lines'
    _description = 'LibraryBorrowLines'

    borrow_id = fields.Many2one('library.borrow', required=True)
    book_id = fields.Many2one('library.book', required=True)
    is_returned = fields.Boolean(string='Is Returned', default=False)
