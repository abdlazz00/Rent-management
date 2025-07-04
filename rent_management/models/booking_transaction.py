from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BookingTransaction(models.Model):
    _name = 'booking.transaction'
    _description = 'Booking Transaction'
    _inherit = ['mail.thread', 'mail.render.mixin']

    name = fields.Char('Booking Number', default='New Booking Number')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    from_date = fields.Datetime('From')
    to_date = fields.Datetime('To')
    rent_guarantee = fields.Boolean('Rent Guarantee')
    documents_type = fields.Many2many(comodel_name="document.type", string="Documents")
    state = fields.Selection([
                                ("draft", "Draft"),
                                ("rented", "Rented"),
                                ("done", "Done"),
                                ("cancel", "Cancelled"),
                            ],"Status", default="draft", copy=False, tracking=True)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency', readonly=True)
    total_amount = fields.Float('Total Amount', compute='_compute_total_amount', store=True)
    line_ids = fields.One2many("booking.transaction.line", "booking_transaction_id", string="Booking Lines",
                               ondelete='cascade')
    payment_count = fields.Integer(
        string="Payment Count", compute="_compute_payment_count"
    )
    payment_ids = fields.One2many(
        "booking.payment", "booking_transaction_id", string="Payments"
    )
    paid_amount = fields.Float("Paid Amount", compute='_compute_paid_amount', store=True)
    remaining_amount = fields.Float("Remaining Amount", compute='_compute_remaining_amount', store=True)

    @api.depends('payment_ids.amount')
    def _compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = sum(payment.amount for payment in rec.payment_ids)

    @api.depends('total_amount', 'paid_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.total_amount - rec.paid_amount

    @api.model
    def create(self, vals):
        if vals.get('name', 'New Booking Number') == 'New Booking Number':
            vals['name'] = self.env['ir.sequence'].next_by_code('booking.booking') or 'New Booking Number'
        record = super(BookingTransaction, self).create(vals)
        return record

    def write(self, vals):
        result = super(BookingTransaction, self).write(vals)
        for record in self:
            if record.state == 'draft' and record.line_ids:
                for line in record.line_ids:
                    if line.vehicle_id:
                        line.vehicle_id.state = 'book'
        return result

    # @api.depends('company_id')
    # def _compute_get_company_id(self):
    #     current_company_id = self.env.company.id
    #     for record in self:
    #         record.company_id = current_company_id

    @api.depends('from_date', 'to_date', 'line_ids.price')
    def _compute_total_amount(self):
        for record in self:
            total = 0.0
            if record.from_date and record.to_date:
                days = (record.to_date - record.from_date).days + 1
                for line in record.line_ids:
                    total += days * line.price
            record.total_amount = total

    def button_confirm(self):
        for record in self:
            record.state = 'rented'
            for line in record.line_ids:
                if line.vehicle_id:
                    line.vehicle_id.state = 'rent'
            record.create_payment()

    def button_reset(self):
        for record in self:
            record.state = 'draft'
            for line in record.line_ids:
                if line.vehicle_id:
                    line.vehicle_id.state = 'book'

    def button_cancel(self):
        for record in self:
            record.state = 'cancel'
            for line in record.line_ids:
                if line.vehicle_id:
                    line.vehicle_id.state = 'available'

    def button_done(self):
        for record in self:
            if record.remaining_amount > 0:
                raise ValidationError("Pembayaran harus lunas sebelum transaksi dapat diselesaikan (Done).\n"
                                      "Sisa pembayaran: %s %s" % (record.remaining_amount, record.currency_id.symbol))

            record.state = 'done'
            for line in record.line_ids:
                if line.vehicle_id:
                    line.vehicle_id.state = 'available'

    def create_payment(self):
        for record in self:
            # Hitung jumlah hari
            days = 0
            if record.from_date and record.to_date:
                days = (record.to_date - record.from_date).days + 1

            # Siapkan payment line
            payment_lines = []
            for line in record.line_ids:
                if line.vehicle_id:
                    price = line.price or 0.0
                    payment_lines.append(
                        (0,0,
                            {
                                "vehicle_id": line.vehicle_id.id,
                                "license_plate": line.vehicle_id.license_plate,
                                "brand_id": line.vehicle_id.brand_id.id,
                                "days": days,
                                "currency_id":line.vehicle_id.currency_id.id,
                                "price": line.vehicle_id.price_per_day,
                                "total_amount": days * price,
                            },))

            # Buat payment draft
            self.env["booking.payment"].create(
                {
                    "customer_id": record.customer_id.id,
                    "booking_transaction_id": record.id,
                    "amount": record.total_amount,
                    "state": "draft",
                    "payment_line_ids": payment_lines,
                }
            )

    def _compute_payment_count(self):
        for record in self:
            record.payment_count = self.env["booking.payment"].search_count(
                [("booking_transaction_id", "=", record.id)]
            )

    def action_view_payments(self):
        self.ensure_one()
        return {
            "name": "Payments",
            "type": "ir.actions.act_window",
            "res_model": "booking.payment",
            "view_mode": "list,form",
            "domain": [("booking_transaction_id", "=", self.id)],
            "context": {"default_booking_transaction_id": self.id},
            "target": "current",
        }


class BookingTransactionLine(models.Model):
    _name = 'booking.transaction.line'
    _description = 'Booking Transaction Line'

    name = fields.Char("name", compute="_compute_name", store=True)
    booking_transaction_id = fields.Many2one("booking.transaction", string="Booking Transaction")
    vehicle_id = fields.Many2one('vehicle.vehicle', string='Vehicle')
    license_plate = fields.Char(related='vehicle_id.license_plate' ,string='Licence Plate')
    brand = fields.Many2one('vehicle.brand',related='vehicle_id.brand_id' , string='Brand')
    rent_from = fields.Datetime(string='Rent From', related='booking_transaction_id.from_date', store=True)
    rent_to = fields.Datetime(string='Rent To', related='booking_transaction_id.to_date', store=True)
    currency_id = fields.Many2one('res.currency', related='vehicle_id.currency_id',string='Currency', readonly=True)
    price = fields.Float(related='vehicle_id.price_per_day' , string='Price')

    @api.depends('vehicle_id.full_name')
    def _compute_name(self):
        for rec in self:
            if rec.vehicle_id and rec.vehicle_id.full_name:
                rec.name = rec.vehicle_id.full_name
            else:
                rec.name = "New Booking Line"

class DocumentType(models.Model):
    _name = 'document.type'
    _description = 'Document Type'

    name = fields.Char(string="Document Name", required=True)
