from email.policy import default

from odoo import models,fields,api,_


class RentExpense(models.Model):
    _name = 'rent.expense'
    _description = 'Rental Operational Expense'
    _inherit = ['mail.thread', 'mail.render.mixin']

    name = fields.Char(
        'Expense Reference', required=True, copy=False, readonly=True, index=True, default='New'
                       )
    expense_date = fields.Date(
                                'Expense Date', default=fields.Date.today(), required=True
                              )
    type = fields.Selection([
                                ('general','General Expense'),('vehicle_maintenance','Vehicle Maintenance'),
                                ('other','Other')
                            ], string='Expense Type', default='general', required=True, tracking=True)
    vehicle_id = fields.Many2one('vehicle.vehicle', string='Vehicle',
                                 help='Select the vehicle if this is a maintenance expense.')
    total_amount = fields.Float('Total Amount',  compute='_compute_total_amount', store=True, readonly=True)
    currency_id = fields.Many2one(
                                "res.currency", string="Currency",
                                 default=lambda self: self.env.company.currency_id.id, required=True,
                                 )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    state = fields.Selection([
        ('draft','Draft'),
        ('confirmed','Confirmed'),
        ('cancelled','Cancelled'),
    ], string='Status', default='draft', tracking=True)
    expense_line_ids = fields.One2many(
        "rent.expense.line", "expense_id", string="Expense Details", ondelete="cascade",
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('rental.expense') or 'New'
        return super(RentExpense, self).create(vals)

    def button_confirm(self):
        for rec in self:
            rec.state = "confirmed"

    def button_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def button_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.depends('expense_line_ids.amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(line.amount for line in rec.expense_line_ids)


class RentalExpenseLine(models.Model):
    _name = 'rent.expense.line'
    _description = 'Rental Expense Line'

    expense_id = fields.Many2one('rent.expense', string='Expense Reference', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True, readonly=True)
    currency_id = fields.Many2one(related='expense_id.currency_id', string='Currency', readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.unit_price
