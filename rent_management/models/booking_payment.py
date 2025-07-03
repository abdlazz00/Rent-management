from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class BookingPayment(models.Model):
    _name = "booking.payment"
    _description = "Booking Payment"
    _inherit = ["mail.thread", "mail.render.mixin"]

    name = fields.Char("Payment Number", default="New Payment Number", readonly=True)
    sanitized_name = fields.Char(
        string="Sanitized Name", compute="_compute_sanitized_name", store=False
    )
    active = fields.Boolean("Active", default=True)
    customer_id = fields.Many2one("res.partner", string="Customer", required=True)
    booking_transaction_id = fields.Many2one(
        "booking.transaction", string="Booking Reference"
    )
    amount = fields.Float("Amount", required=True)
    payment_date = fields.Date("Payment Date", default=fields.Date.today())
    payment_date_str = fields.Char(
        string="Formatted Payment Date", compute="_compute_payment_date_str", store=False
    )
    payment_method = fields.Selection(
        [
            ("cash", "Cash"), ("bank_transfer", "Bank Transfer"),
            ("credit_card", "Credit Card"), ("debit_card", "Debit Card"),
            ("other", "Other"),],string="Payment Method", default="cash", required=True)
    payment_method_display = fields.Char(string="Payment Method Display", compute="_compute_payment_method_display")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("paid", "Paid"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="booking_transaction_id.currency_id",
        string="Currency",
        readonly=True,
    )
    payment_line_ids = fields.One2many(
        "booking.payment.line",
        "booking_payment_id",
        string="Payment Lines",
        ondelete="cascade",
    )

    @api.depends("payment_method")
    def _compute_payment_method_display(self):
        for rec in self:
            rec.payment_method_display = rec.payment_method = dict(
                rec._fields["payment_method"].selection
            ).get(rec.payment_method, " ")

    @api.depends("name")
    def _compute_sanitized_name(self):
        for rec in self:
            rec.sanitized_name = (rec.name or "").replace("/", "_")

    @api.depends("payment_date")
    def _compute_payment_date_str(self):
        for rec in self:
            rec.payment_date_str = rec.payment_date.strftime("%d-%m-%Y") if rec.payment_date else ""

    @api.model
    def create(self, vals):
        if vals.get("name", "New Payment Number") == "New Payment Number":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("booking.payment")
                or "New Payment Number"
            )
        record = super(BookingPayment, self).create(vals)
        return record

    def button_confirm(self):
        for rec in self:
            rec.state = "confirmed"

    def button_paid(self):
        for rec in self:
            rec.state = "paid"

    def button_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def button_reset(self):
        for rec in self:
            rec.state = "draft"



class BookingPaymentLine(models.Model):
    _name = "booking.payment.line"
    _description = "Booking Payment Line"

    booking_payment_id = fields.Many2one("booking.payment", string="Booking Payment")
    vehicle_id = fields.Many2one("vehicle.vehicle", string="Vehicle")
    license_plate = fields.Char(string="Licence Plate")
    brand_id = fields.Many2one("vehicle.brand", string="Brand")
    days = fields.Integer(string="Days")
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    price = fields.Float(string="Price")
    total_amount = fields.Float(string="Total Amount")
