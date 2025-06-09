from odoo import models, fields, api

class BookingPayment(models.Model):
    _name = 'booking.payment'
    _description = 'Booking Payment'
    _inherit = ['mail.thread', 'mail.render.mixin']

    name = fields.Char('Payment Reference', required=True, copy=False, readonly=True, default='New')
    active = fields.Boolean('Active', default=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    booking_transaction_id = fields.Many2one('booking.transaction', string='Booking Transaction', required=True)
    payment_date = fields.Date('Payment Date', default=fields.Date.context_today, required=True)
    amount = fields.Float('Amount', required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='booking_transaction_id.currency_id', readonly=True)
    # Relasi ke payment lines
    payment_line_ids = fields.One2many('booking.payment.line', 'payment_id', string='Payment Lines', ondelete='cascade')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('booking.payment') or 'New'
        record = super(BookingPayment, self).create(vals)
        return record

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'


class BookingPaymentLine(models.Model):
    _name = 'booking.payment.line'
    _description = 'Booking Payment Line'

    payment_id = fields.Many2one('booking.payment', string='Payment Reference', required=True, ondelete='cascade')
    vehicle_id = fields.Many2one('vehicle.vehicle', string='Vehicle', required=True)
    license_plate = fields.Char(string='License Plate', related='vehicle_id.license_plate', store=True, readonly=True)
    brand_id = fields.Many2one('vehicle.brand', related='vehicle_id.brand_id', string='Brand', readonly=True)
    days = fields.Integer('Days')
    currency_id = fields.Many2one('res.currency', related='vehicle_id.currency_id', string='Currency', readonly=True)
    price = fields.Float(string='Price', related='vehicle_id.price_per_day', readonly=True, store=True)
    total_amount = fields.Float(string='Total Price', required=True, store=True)
