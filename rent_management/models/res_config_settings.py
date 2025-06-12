from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    twilio_account_sid = fields.Char(string="Twilio Account SID", config_parameter='rent_management.twilio_account_sid')
    twilio_auth_token = fields.Char(string="Twilio Auth Token", config_parameter='rent_management.twilio_auth_token')
    twilio_whatsapp_number = fields.Char(string="Twilio WhatsApp Number", config_parameter='rent_management.twilio_whatsapp_number',
                                         help="Nomor WhatsApp Twilio Anda, harus dalam format E.164 (misal: +1234567890)")
    whatsapp_invoice_template_name = fields.Char(string="WhatsApp Invoice Template Name", config_parameter='rent_management.whatsapp_invoice_template_name',
                                                 help="Nama template WhatsApp yang sudah disetujui untuk tagihan (misal: 'invoice_notification')")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('rent_management.twilio_account_sid', self.twilio_account_sid)
        self.env['ir.config_parameter'].set_param('rent_management.twilio_auth_token', self.twilio_auth_token)
        self.env['ir.config_parameter'].set_param('rent_management.twilio_whatsapp_number', self.twilio_whatsapp_number)
        self.env['ir.config_parameter'].set_param('rent_management.whatsapp_invoice_template_name', self.whatsapp_invoice_template_name)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            twilio_account_sid=ICPSudo.get_param('rent_management.twilio_account_sid'),
            twilio_auth_token=ICPSudo.get_param('rent_management.twilio_auth_token'),
            twilio_whatsapp_number=ICPSudo.get_param('rent_management.twilio_whatsapp_number'),
            whatsapp_invoice_template_name=ICPSudo.get_param('rent_management.whatsapp_invoice_template_name'),
        )
        return res