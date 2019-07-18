from odoo import api, fields, models, _

class account_payment(models.Model):
    _name = "account.payment"
    _inherit = ['account.payment']

    remarks = fields.Char('Remarks')