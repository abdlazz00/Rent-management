from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
from twilio.rest import Client

_logger = logging.getLogger(__name__)


class BookingPayment(models.Model):
    _name = "booking.payment"
    _description = "Booking Payment"
    _inherit = ["mail.thread", "mail.render.mixin"]

    name = fields.Char("Payment Number", default="New Payment Number", readonly=True)
    active = fields.Boolean("Active", default=True)
    customer_id = fields.Many2one("res.partner", string="Customer", required=True)
    booking_transaction_id = fields.Many2one(
        "booking.transaction", string="Booking Reference"
    )
    amount = fields.Float("Amount", required=True)
    payment_date = fields.Date("Payment Date", default=fields.Date.today())
    payment_method = fields.Selection(
        [  # TAMBAHKAN FIELD INI
            ("cash", "Cash"),
            ("bank_transfer", "Bank Transfer"),
            ("credit_card", "Credit Card"),
            ("debit_card", "Debit Card"),
            ("other", "Other"),
        ],
        string="Payment Method",
        default="cash",
        required=True,
    )
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

    def action_send_whatsapp_invoice(self):
        self.ensure_one()

        ICPSudo = self.env["ir.config_parameter"].sudo()
        account_sid = ICPSudo.get_param("rent_management.twilio_account_sid")
        auth_token = ICPSudo.get_param("rent_management.twilio_auth_token")
        twilio_whatsapp_number = ICPSudo.get_param(
            "rent_management.twilio_whatsapp_number"
        )
        template_name = ICPSudo.get_param(
            "rent_management.whatsapp_invoice_template_name"
        )

        if not (
            account_sid and auth_token and twilio_whatsapp_number and template_name
        ):
            raise ValidationError(
                "Konfigurasi Twilio belum lengkap. Mohon lengkapi di Pengaturan > Rental Management."
            )

        customer_whatsapp_number = (
            self.customer_id.mobile
        )  # Asumsi menggunakan field 'mobile'
        if not customer_whatsapp_number:
            raise ValidationError(
                "Nomor WhatsApp pelanggan tidak ditemukan. Mohon lengkapi data pelanggan."
            )

        # Bersihkan nomor dan format ke E.164
        # Contoh: +628123456789
        customer_whatsapp_number = customer_whatsapp_number.replace(" ", "").replace(
            "-", ""
        )
        if not customer_whatsapp_number.startswith("+"):
            if customer_whatsapp_number.startswith("0"):
                customer_whatsapp_number = "+62" + customer_whatsapp_number[1:]
            else:
                customer_whatsapp_number = (
                    "+" + customer_whatsapp_number
                )  # Asumsi ada kode negara jika tidak diawali 0

        # Ambil display name untuk payment_method
        payment_method_display = dict(self._fields["payment_method"].selection).get(
            self.payment_method
        )

        template_data = {
            "1": self.customer_id.name or "",  # Nama Customer
            "2": self.name or "",  # Nomor Payment
            "3": (
                f"{self.amount:,.0f} {self.currency_id.symbol}"
                if self.currency_id
                else f"{self.amount:,.0f}"
            ),
            "4": (
                self.payment_date.strftime("%d-%m-%Y") if self.payment_date else ""
            ),
            "5": self.payment_method or "",
        }

        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                from_=f"whatsapp:{twilio_whatsapp_number}",
                to=f"whatsapp:{customer_whatsapp_number}",
                content_sid=template_name,  # Terkadang Twilio menggunakan Content SID atau Template SID
                # Jika template_name tidak berfungsi, coba cari Content SID
                content_variables=template_data,
            )
            _logger.info(f"WhatsApp message sent successfully: {message.sid}")
            self.message_post(
                body=f"WhatsApp tagihan berhasil dikirim. SID: {message.sid}"
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Sukses",
                    "message": "Pesan WhatsApp tagihan berhasil dikirim!",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            _logger.error(f"Failed to send WhatsApp message: {e}")
            self.message_post(
                body=f"Gagal mengirim WhatsApp tagihan: {e}",
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
            raise ValidationError(
                f"Gagal mengirim pesan WhatsApp. Pastikan konfigurasi Twilio dan nomor WhatsApp benar. Error: {e}"
            )


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
