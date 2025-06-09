from odoo import models, fields, api

class Company(models.Model):
    _inherit = 'res.company'

class Partner(models.Model):
    _inherit = 'res.partner'