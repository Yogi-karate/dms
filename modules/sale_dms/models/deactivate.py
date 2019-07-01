# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class DeactivateSource(models.TransientModel):
    """
        Merge opportunities together.
        If we're talking about opportunities, it's just because it makes more sense
        to merge opps than leads, because the leads are more ephemeral objects.
        But since opportunities are leads, it's also possible to merge leads
        together (resulting in a new lead), or leads and opps together (resulting
        in a new opp).
    """

    _name = 'dms.deactivate.source'
    _description = 'reassign enquiries to another user'

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        record_ids = self._context.get('active_ids')
        print(record_ids)
        result = super(DeactivateSource, self).default_get(fields)
        vals ={
            'active': False
        }
        for record in record_ids:
            ne = self.env['utm.source'].browse(record)
            print(ne,"(((",ne.name,"::::",ne.active)
            ne.write(vals)
        print()
        print("????????????????????????????????????????????????????????????????????????????????",fields)
        if record_ids:
            if 'enquiry_ids' in fields:
                opp_ids = self.env['utm.source'].browse(record_ids).ids
                print(".......")
                print(opp_ids)
                result['enquiry_ids'] = opp_ids
        print("________________")
        print(result)
        return result

    #enquiry_ids = fields.Many2many('utm.source')

    @api.multi
    def action_deactivate(self):
        print("üuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
        print(self)
        # self.ensure_one()
        # print("Hello from reassign")
        # reassign_enquiries = self.enquiry_ids.reassign_enquiry(self.user_id.id, self.team_id.id)
        # merge_opportunity = self.opportunity_ids.merge_opportunity(self.user_id.id, self.team_id.id)
        #
        # # The newly created lead might be a lead or an opp: redirect toward the right view
        # if merge_opportunity.type == 'opportunity':
        #     return merge_opportunity.redirect_opportunity_view()
        # else:
        #     return merge_opportunity.redirect_lead_view()

    # @api.onchange('user_id')
    # def _onchange_user(self):
    #     """ When changing the user, also set a team_id or restrict team id
    #         to the ones user_id is member of. """
    #     team_id = False
    #     if self.user_id:
    #         user_in_team = False
    #         if self.team_id:
    #             user_in_team = self.env['crm.team'].search_count([('id', '=', self.team_id.id), '|', ('user_id', '=', self.user_id.id), ('member_ids', '=', self.user_id.id)])
    #         if not user_in_team:
    #             team_id = self.env['crm.team'].search(['|', ('user_id', '=', self.user_id.id), ('member_ids', '=', self.user_id.id)], limit=1)
    #     self.team_id = team_id
