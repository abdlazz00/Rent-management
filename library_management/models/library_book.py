# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'LibraryBook'
    _inherit = ['mail.thread', 'mail.render.mixin', 'mail.activity.mixin']

    name = fields.Char(string='Book Name', required=True)
    active = fields.Boolean(default=True)
    image_1920 = fields.Image('Book Image')
    isbn = fields.Char('ISBN')
    publication_year = fields.Char('Publication Year')
    stock = fields.Integer('Stock')
    is_available = fields.Boolean('Is Available')
    author_ids = fields.Many2many('library.author', string='Authors')
    genre_ids = fields.Many2many('library.genre', string='Genres')
    publisher_id = fields.Many2one('library.publisher', string='Publisher')
    category_id = fields.Many2one('library.category', string='Category')



class LibraryAuthorBook(models.Model):
    _name = 'library.author'
    _description = 'LibraryAuthor'

    name = fields.Char('Author Name', required=True)


class LibraryPublisherBook(models.Model):
    _name = 'library.publisher'
    _description = 'LibraryPublisher'

    name = fields.Char('Publisher Name', required=True)

class LibraryCategory(models.Model):
    _name = 'library.category'
    _description = 'LibraryCategory'

    name = fields.Char('Category Name', required=True)

class LibraryGenre(models.Model):
    _name = 'library.genre'
    _description = 'LibraryGenre'

    name = fields.Char('Genre Name', required=True)