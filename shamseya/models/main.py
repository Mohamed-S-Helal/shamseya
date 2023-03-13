# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class ResUsers(models.Model):
    _inherit = 'res.users'

    seq = fields.Many2one('ir.sequence', string=_('Sequence'))
    next_code = fields.Integer(readonly=0, related='seq.number_next_actual')



class Case(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']
    _description = 'Cases'

    name1 = fields.Char(required=1, string="First Name", compute='split_name', readonly=0)
    name2 = fields.Char(required=1, string="Middle Name", compute='split_name', readonly=0)
    name3 = fields.Char(required=1, string="Last Name", compute='split_name', readonly=0)
    name4 = fields.Char(required=1, string="Last Name", compute='split_name', readonly=0)

    name = fields.Char(compute='set_name', store=1, default='_new', readonly=0)

    @api.depends('name1', 'name2', 'name3', 'name4')
    def set_name(self):
        for rec in self:
            rec.name = (
                    (f'{rec.name1}' if rec.name1 else '_new') +
                    (f' {rec.name2}' if rec.name2 else '') +
                    (f' {rec.name3}' if rec.name3 else '') +
                    (f' {rec.name4}' if rec.name4 else '')
            )

    @api.depends('name')
    def split_name(self):
        for rec in self:
            ns = rec.name.split(' ')
            rec.name1 = rec.name1 or ns[0]
            if len(ns) > 1:
                rec.name2 = rec.name2 or ns[1]
            if len(ns) > 2:
                rec.name3 = rec.name3 or ns[2]
            if len(ns) > 3:
                rec.name4 = rec.name4 or ' '.join(ns[3:])

    def get_code(self):
        serial = self.env.user.next_code
        prefix = self.env.user.prefix or '_'
        return f'{prefix}/{serial}'

    code = fields.Char(default=get_code, readonly=1)

    is_case = fields.Boolean()
    created_by = fields.Many2one('res.partner', default=lambda self: self.create_uid.partner_id,
                                 domain="[('is_case', '=', False)]")

    date_of_birth = fields.Date(string='Date of Birth')

    # compute age from date of birth
    age = fields.Integer(string='Age', compute="compute_age", store=1)
    age_m = fields.Integer(string='Age', compute="compute_age", store=1)

    @api.depends('date_of_birth')
    def compute_age(self):
        for rec in self:
            today = fields.Date.today()
            age_y = 0
            age_m = 0
            if rec.date_of_birth and rec.date_of_birth < today:
                age = relativedelta(today, rec.date_of_birth)
                age_y = age.years
                age_m = age.months
            rec.age = age_y
            rec.age_m = age_m

    phone = fields.Char(string='رقم الموبايل', required=1)
    phone2 = fields.Char(string='رقم الواتساب')

    @api.onchange('phone')
    def onchange_phone(self):
        if self.phone and (not self.phone.isdigit() or not self.phone.startswith('01') or len(self.phone) != 11):
            raise UserError('Wrong phone format: phone must be 11 digits in the format 01xxxxxxxxx')

    @api.onchange('phone2')
    def onchange_phone2(self):
        if self.phone2 and (not self.phone2.isdigit() or not self.phone2.startswith('01') or len(self.phone2) != 11):
            raise UserError('Wrong phone format: phone must be 11 digits in the format 01xxxxxxxxx')

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Gender")

    marital_status = fields.Selection([
        ('single', 'أعزب/عزباء'),
        ('married', 'متزوج/ـة'),
        ('divorced', 'مطلق/ـة'),
        ('widow', 'أرمل/ـة'),
        ('abandoned', 'هجر'),
        ('under_age', 'تحت السن'),
    ], string='Marital Status')

    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 default=lambda self: self.env.user.country_id)
    area = fields.Many2one('area', domain="[('state_id', '=?', state_id)]")

    @api.onchange('area')
    def onchange_area(self):
        if not self.area.state_id:
            self.area.state_id = self.state_id

    create_uid = fields.Many2one('res.users', string='Created By', readonly=0)
    referral = fields.Many2one('referral', string='Refered By')
    income_resource = fields.Many2one('income.resource', string="Family Income Resource")
    pension_type = fields.Many2one('pension.type')
    currency_id = fields.Many2one('res.currency', related='country_id.currency_id')
    average_income = fields.Monetary('Average Income', currency_field='currency_id')
    # has_health_insurance = fields.Boolean()
    health_insurance_id = fields.Many2one('health.insurance')

    health_coverage = fields.Selection([
        ('1', 'تأمين صحي'),
        ('2', 'علاج على نفقة الدولة'),
        ('3', 'مبادرات وحملات رئاسية'),
        ('4', 'تأمين صحي شامل'),
        ('5', 'تأمين صحي لطلبة الجامعات'),
        ('6', 'كارت خدمات متكاملة'),
    ], default='1', string='نوع التغطية الصحية')

    social_insurance_id = fields.Many2one('social.insurance', string='نوع التأمين الاجتماعي')
    know_social_insurance_code = fields.Boolean(string="الرقم التأميني")
    social_insurance_code = fields.Char()
    mother_name = fields.Char()
    personal_id_number = fields.Char(required=1)

    personal_id_card = fields.Many2many('ir.attachment', 'personal_id_card_rel')
    insurance_card = fields.Many2many('ir.attachment', 'insurance_card_rel')
    health_card = fields.Many2many('ir.attachment', 'health_card_rel')
    other_attachments = fields.Many2many('ir.attachment', 'other_attachments_rel')

    # health_coverage = fields.Boolean()
    # health_coverage_type = fields.Many2one('health.coverage')


    requests = fields.One2many('case.request', 'case_id')

    medical_history_lines = fields.One2many('medical.history.line', 'case_id')

    requests_count = fields.Integer(compute='_compute_requests_count', string='Requests Count')

    def _compute_requests_count(self):
        for rec in self:
            rec.requests_count = len(rec.requests)

    def open_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('shamseya.action_request')
        action['domain'] = [('case_id', '=', self.id)]
        # action['context'] = {'search_default_case_id': 'asas'}
        return action

    def action_create_request(self):
        vals = {
            'case_id': self.id,
        }

        context = dict(self.env.context or {})
        # states = self.env['request.state'].search([]).sorted('order_')
        # if states:
        #     vals.update(status=states[0].id)
        # print(states)
        # print(vals)
        request = self.env['case.request'].sudo().create(vals)

        action = {
            'view_mode': 'form',
            'res_model': 'case.request',
            'view_id': self.env.ref('shamseya.view_request_form').id,
            'type': 'ir.actions.act_window',
            'res_id': request.id,
            'context': context,
            'target': 'self'
        }
        return action

    @api.model
    def create(self, vals):
        res = super().create(vals)
        serial = self.env.user.seq.next_by_id()
        prefix = self.env.user.prefix or '_'
        res.code = f'{prefix}/{serial}'
        return res

    def unlink(self):
        seq = str(self.env.user.next_code-1).zfill(self.env.user.seq.padding)
        print(seq)
        print(self.code)
        if self.code.endswith(seq):
            print('un')
            self.env.user.next_code -= 1
        return super().unlink()


class CaseRequest(models.Model):
    _name = 'case.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _rec_name = 'basic_service'

    case_id = fields.Many2one('res.partner', required=1, domain=[('is_case', '=', True)])
    name = fields.Char(related='basic_service.name', store=1, readonly=1)

    @api.onchange('case_id')
    def onchange_area(self):
        self.case_id.is_case = True

    created_by = fields.Many2one('res.partner', default=lambda self: self.create_uid.partner_id,
                                 domain="[('is_case', '=', False)]")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Starred", tracking=True)

    basic_service = fields.Many2one('basic.service', required=1)
    description = fields.Text()
    medicine_type = fields.Many2many('medicine.type', relation='request_type_rel')
    medicine = fields.Many2many('medicine', relation='request_medicine_rel')
    operation = fields.Many2one('service.operation')
    monthly_follow_up = fields.One2many('monthly.follow.up', 'request_id')

    currency_id = fields.Many2one('res.currency', related='case_id.currency_id')
    cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost', store=1)

    @api.depends('operation', 'medicine', 'monthly_follow_up', 'basic_service')
    def _compute_cost(self):
        for rec in self:
            service = rec.basic_service.type
            if service == 'operation':
                rec.cost = rec.operation.price
            elif service == 'medicine_once':
                rec.cost = sum(rec.medicine.mapped('price'))
            elif service == 'medicine_monthly':
                rec.cost = sum(rec.medicine.mapped('price')) * len(rec.monthly_follow_up)
            else:
                rec.cost = 0

    @api.onchange('medicine_type')
    def onchange_medicine_type(self):
        medicines = self.medicine_type.mapped('medicines').ids
        self.medicine = [(6, 0, medicines)]
        return {'domain': {'medicine': [('id', 'in', medicines)]}}

    complaint = fields.Text()

    status = fields.Many2one('request.state', string="Status", group_expand='_read_group_status_ids',
                             default=lambda self: self.env['request.state'].search([]).sorted('order_')[0].id if
                             self.env['request.state'].search([]) else None)

    @api.onchange('status', 'basic_service')
    def onchange_status(self):
        if self.status.type == 'monthly' and self.basic_service.type != 'medicine_monthly':
            raise UserError('Monthly Follow Up is only available for "Medicine Monthly" service')

    @api.model
    def _read_group_status_ids(self, stages, domain, order):
        return self.env['request.state'].search([], order=order)

    kanban_state = fields.Selection([
        ('done', 'In Progress'),
        ('blocked', 'On Hold')], string='Progress',
        copy=False, default='done', required=True, tracking=1)

    # show_service_monthly = fields.Selection(related='basic_service.monthly')
    service_type = fields.Selection(related='basic_service.type')

    health_coverage = fields.Selection([
        ('1', 'تأمين صحي'),
        ('2', 'علاج على نفقة الدولة'),
        ('3', 'مبادرات وحملات رئاسية'),
        ('4', 'تأمين صحي شامل'),
        ('5', 'تأمين صحي لطلبة الجامعات'),
        ('6', 'كارت خدمات متكاملة'),
    ], default='1', string='نوع التغطية الصحية المستحقة')

    health_insurance = fields.Selection([
        ('1', 'تأمين صحي للمواليد'),
        ('2', 'تأمين صحي لطلبة المدارس'),
        ('3', 'تأمين صحي للموظفين'),
        ('4', 'تأمين صحي للمعاشات'),
        ('5', 'تأمين صحي للأرامل'),
        ('6', 'تأمين صحي للمرأة المعيلة'),
        ('7', 'تأمين صحي للفلاحين'),
        ('6', 'تأمين صحي للعمالة غير المنتظمة'),
    ], default='1', string='نوع التأمين الصحي')

    initiative = fields.Selection([
        ('1', 'مبادرة علاج غير القادرين'),
        ('2', 'مبادرة صحة المرأة'),
        ('3', 'مبادرة 100 مليون صحة'),
        ('4', 'أخرى'),
    ], default='1', string='نوع المبادرة')

    issues = fields.One2many('follow.up.issue', 'request_id')

    issues_count = fields.Integer(compute='_compute_issues_count', string='Issues Count')

    def _compute_issues_count(self):
        for rec in self:
            rec.issues_count = len(rec.issues)

    def open_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('shamseya.issue_action')
        action['domain'] = [('request_id', '=', self.id)]
        # action['context'] = {'search_default_case_id': 'asas'}
        return action


class MonthlyFollowUp(models.Model):
    _name = 'monthly.follow.up'

    request_id = fields.Many2one('case.request')
    name = fields.Char(related='request_id.name')
    date = fields.Date()
    m_status = fields.Selection([('in_process', 'In Process'), ('done', 'Done'), ('problem', 'Problem')],
                                string='Status', default='in_process')

    # month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    #                           (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    #                           (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
    #                          string='Month', )
    # year = fields.Selection(get_years(), string='Year', default=datetime.now().year)
    # medicine = fields.Many2one('medicine')
    issues = fields.One2many('follow.up.issue', 'follow_up_id')

    def open_issue(self):
        [action] = self.env.ref('shamseya.issue_action').read()

        if action:
            action['domain'] = [('follow_up_id', '=', self.id)]
            action['context'] = {
                'default_follow_up_id': self.id,
                'default_case_id': self.request_id.case_id.id,
                'default_request_id': self.request_id.id,
                'default_applier_id_no': self.request_id.case_id.personal_id_number, }
            # action['view_mode'] = 'tree,form'
            # action['views'] = [(k, v) for k, v in action['views'] if v in ['tree', 'form']]
            return action
