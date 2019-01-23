from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class VehicleType(models.Model):
    _name = "vehicle.type"
    _description = "Vehicle Type"
    _order = 'sequence, id'

    name = fields.Char('Vehicle Type', required=True, translate=True)
    color = fields.Integer('Color')
    sequence = fields.Integer('Sequence', help="Used to order the 'All Operations' kanban view")
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence', required=True)
    default_location_src_id = fields.Many2one(
        'stock.location', 'Default Source Location',
        help="This is the default source location when you create a picking manually with this operation type. It is possible however to change it or that the routes put another location. If it is empty, it will check for the supplier location on the partner. ")
    default_location_dest_id = fields.Many2one(
        'stock.location', 'Default Destination Location',
        help="This is the default destination location when you create a picking manually with this operation type. It is possible however to change it or that the routes put another location. If it is empty, it will check for the customer location on the partner. ")
    code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')], 'Type of Operation', required=True)
    return_picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type for Returns')
    show_entire_packs = fields.Boolean('Move Entire Packages', help="If ticked, you will be able to select entire packages to move")
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse', ondelete='cascade',
        default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1))
    active = fields.Boolean('Active', default=True)
    use_create_lots = fields.Boolean(
        'Create New Lots/Serial Numbers', default=True,
        help="If this is checked only, it will suppose you want to create new Lots/Serial Numbers, so you can provide them in a text field. ")
    use_existing_lots = fields.Boolean(
        'Use Existing Lots/Serial Numbers', default=True,
        help="If this is checked, you will be able to choose the Lots/Serial Numbers. You can also decide to not put lots in this operation type.  This means it will create stock with no lot or not put a restriction on the lot taken. ")
    show_operations = fields.Boolean(
        'Show Detailed Operations', default=False,
        help="If this checkbox is ticked, the pickings lines will represent detailed stock operations. If not, the picking lines will represent an aggregate of detailed stock operations.")
    show_reserved = fields.Boolean(
        'Show Reserved', default=True, help="If this checkbox is ticked, Odoo will show which products are reserved (lot/serial number, source location, source package).")

    # Statistics for the kanban view
    # last_done_picking = fields.Char('Last 10 Done Pickings', compute='_compute_last_done_picking')
    # count_picking_draft = fields.Integer(compute='_compute_picking_count')
    # count_picking_ready = fields.Integer(compute='_compute_picking_count')
    # count_picking = fields.Integer(compute='_compute_picking_count')
    # count_picking_waiting = fields.Integer(compute='_compute_picking_count')
    # count_picking_late = fields.Integer(compute='_compute_picking_count')
    # count_picking_backorders = fields.Integer(compute='_compute_picking_count')
    # rate_picking_late = fields.Integer(compute='_compute_picking_count')
    # rate_picking_backorders = fields.Integer(compute='_compute_picking_count')
    # barcode = fields.Char('Barcode', copy=False)

    @api.one
    def _compute_last_done_picking(self):
        # TDE TODO: true multi
        tristates = []
        for picking in self.env['stock.picking'].search([('picking_type_id', '=', self.id), ('state', '=', 'done')], order='date_done desc', limit=10):
            if picking.date_done > picking.date:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Late'), 'value': -1})
            elif picking.backorder_id:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Backorder exists'), 'value': 0})
            else:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('OK'), 'value': 1})
        self.last_done_picking = json.dumps(tristates)

    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0

    def name_get(self):
        """ Display 'Warehouse_name: PickingType_name' """
        # TDE TODO remove context key support + update purchase
        res = []
        for picking_type in self:
            if self.env.context.get('special_shortened_wh_name'):
                if picking_type.warehouse_id:
                    name = picking_type.warehouse_id.name
                else:
                    name = _('Customer') + ' (' + picking_type.name + ')'
            elif picking_type.warehouse_id:
                name = picking_type.warehouse_id.name + ': ' + picking_type.name
            else:
                name = picking_type.name
            res.append((picking_type.id, name))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('warehouse_id.name', operator, name)]
        picking_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(picking_ids).name_get()

    @api.onchange('code')
    def onchange_picking_code(self):
        if self.code == 'incoming':
            self.default_location_src_id = self.env.ref('stock.stock_location_suppliers').id
            self.default_location_dest_id = self.env.ref('stock.stock_location_stock').id
        elif self.code == 'outgoing':
            self.default_location_src_id = self.env.ref('stock.stock_location_stock').id
            self.default_location_dest_id = self.env.ref('stock.stock_location_customers').id

    @api.onchange('show_operations')
    def onchange_show_operations(self):
        if self.show_operations is True:
            self.show_reserved = True

    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action

    def get_action_picking_tree_late(self):
        return self._get_action('stock.action_picking_tree_late')

    def get_action_picking_tree_backorder(self):
        return self._get_action('stock.action_picking_tree_backorder')

    def get_action_picking_tree_waiting(self):
        return self._get_action('stock.action_picking_tree_waiting')

    def get_action_picking_tree_ready(self):
        return self._get_action('stock.action_picking_tree_ready')

    def get_stock_picking_action_picking_type(self):
        return self._get_action('stock.stock_picking_action_picking_type')
