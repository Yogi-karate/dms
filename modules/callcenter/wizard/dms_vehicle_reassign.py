# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ReassignVehicleLead(models.TransientModel):
    """
        Merge opportunities together.
        If we're talking about opportunities, it's just because it makes more sense
        to merge opps than leads, because the leads are more ephemeral objects.
        But since opportunities are leads, it's also possible to merge leads
        together (resulting in a new lead), or leads and opps together (resulting
        in a new opp).
    """

    _name = 'dms.vehicle.lead.assign'
    _description = 'reassign calls to another user'
    member_values = fields.One2many('res.users', string='Team',
                                               compute='compute_member_values')

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        record_ids = self._context.get('active_ids')
        result = super(ReassignVehicleLead, self).default_get(fields)

        if record_ids:
            if 'enquiry_ids' in fields:
                opp_ids = self.env['dms.vehicle.lead'].browse(record_ids).ids
                result['enquiry_ids'] = opp_ids
        print("________________")
        print(result)
        return result

    @api.onchange('team_id')
    def compute_member_values(self):
        self.user_id = False
        team = self.sudo().env['crm.team'].search([('id', '=', self.team_id.id)])
        print("****************************************************************************************")
        member_values = team.mapped('member_ids')
        manager_values = team.mapped('manager_user_ids')
        print(member_values,"___________________________________________________________",manager_values)
        self.member_values = manager_values + member_values + team.user_id
        print(self.team_id.manager_user_ids)

    enquiry_ids = fields.Many2many('dms.vehicle.lead', 'reassign_vehicle_lead_rel', 'reassign_id', 'lead_id', string='Calls')
    user_id = fields.Many2one('res.users', 'Telecaller', index=True, required=True)
    team_id = fields.Many2one('crm.team', 'Business Team', oldname='section_id', index=True,required=True)

    @api.multi
    def action_reassign_team(self):
        self.ensure_one()
        print("Hello from reassign")
        reassign_enquiries = self.enquiry_ids.reassign_users(self.user_id.id, self.team_id.id)
