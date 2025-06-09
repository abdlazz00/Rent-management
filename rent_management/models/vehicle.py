from odoo import models, fields, api


class VehicleBrand(models.Model):
    _name = "vehicle.brand"
    _description = "Brand"

    name = fields.Char("Brand")
    code = fields.Char("Brand Code")
    image = fields.Char("Brand Image")


class Vehicle(models.Model):
    _name = 'vehicle.vehicle'
    _description = 'Vehicle'
    _inherit = ['mail.thread', 'mail.render.mixin']

    name = fields.Char(string='Name', required=True)
    license_plate = fields.Char('License Plate')
    full_name = fields.Char("Full Name", compute="_compute_full_name", store=True)
    year = fields.Integer("Year")
    vehicle_type = fields.Selection([
        ('mobil', 'Mobil'),
        ('motor', 'Motor'),
    ], "Vehicle Type", required=True, default="mobil", tracking=True)
    brand_id = fields.Many2one('vehicle.brand', 'Brand', required=True)
    price_per_day = fields.Float("Rental Price")
    company_id = fields.Many2one(
        'res.company', 'Company', compute='_compute_get_company_id')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency', readonly=True)
    image = fields.Binary('Image')
    state = fields.Selection(
        [("available", "Available"),
                  ("book", "Booked"),("rent", "Rented"),
        ],"Status", default="available", index=True, required=True, readonly=True,
        copy=False, tracking=True,)

    @api.depends('license_plate', 'name')
    def _compute_full_name(self):
        for record in self:
            lp = record.license_plate or ''
            nm = record.name or ''
            if lp and nm:
                record.full_name = f"{lp} - {nm}"
            else:
                record.full_name = lp or nm

    @api.depends('company_id')
    def _compute_get_company_id(self):
        current_company_id = self.env.company.id
        for record in self:
            record.company_id = current_company_id
