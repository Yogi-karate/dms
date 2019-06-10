from odoo import api, fields, models, _


class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                  index=True)

    @api.model
    def create(self, vals):
        result = super(VehicleLead, self).create(vals)
        return result
