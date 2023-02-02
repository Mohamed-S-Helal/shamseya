# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class Case(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']
    _description = 'Cases'

    name = fields.Char(required=1, string="First Name")
    name2 = fields.Char(required=1, string="Middle Name")
    name3 = fields.Char(required=1, string="Last Name")
    code = fields.Char(readonly=0)
    is_case = fields.Boolean()
    created_by = fields.Many2one('res.partner', default=lambda self: self.create_uid.partner_id,
                                 domain="[('is_case', '=', False)]")

    date_of_birth = fields.Date(string='Date of Birth')

    # compute age from date of birth
    age = fields.Integer(string='Age', compute="compute_age", store=1)

    @api.onchange('phone')
    def onchange_phone(self):
        if self.phone and (not self.phone.isdigit() or not self.phone.startswith('01') or len(self.phone)!=11):
            raise UserError('Wrong phone format: phone must be 11 digits in the format 01xxxxxxxxx')

    @api.depends('date_of_birth')
    def compute_age(self):
        for rec in self:
            today = fields.Date.today()
            age = 0
            if rec.date_of_birth and rec.date_of_birth <= today:
                age = relativedelta(today, rec.date_of_birth).years
            rec.age = age

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
    has_health_insurance = fields.Boolean()
    health_insurance_type = fields.Many2one('health.insurance.type')

    social_insurance_type = fields.Many2one('social.insurance.type')
    know_social_insurance_code = fields.Boolean(string="Social Insurance Code")
    social_insurance_code = fields.Integer()
    mother_name = fields.Char()
    personal_id_number = fields.Integer()

    personal_id_card = fields.Many2many('ir.attachment', 'personal_id_card_rel')
    insurance_card = fields.Many2many('ir.attachment', 'insurance_card_rel')
    health_card = fields.Many2many('ir.attachment', 'health_card_rel')
    other_attachments = fields.Many2many('ir.attachment', 'other_attachments_rel')

    health_coverage = fields.Boolean()
    health_coverage_type = fields.Many2one('health.coverage')

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

        request = self.env['case.request'].sudo().create(vals)
        context = dict(self.env.context or {})
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
    @api.depends('name','name2','name3')
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name + (f' {rec.name2}' if rec.name2 else 0) +
            res.append((rec.id, name))
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        serial = self.env['ir.sequence'].next_by_code('case.seq')
        prefix = self.env.user.prefix or '_'
        res.code = f'{prefix}-{serial}'
        return res


class CaseRequest(models.Model):
    _name = 'case.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    case_id = fields.Many2one('res.partner', required=1, domain=[('is_case', '=', True)])

    @api.onchange('case_id')
    def onchange_area(self):
        self.case_id.is_case = True

    created_by = fields.Many2one('res.partner', default=lambda self: self.create_uid.partner_id,
                                 domain="[('is_case', '=', False)]")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Starred", tracking=True)

    basic_service = fields.Many2one('basic.service')
    description = fields.Text()
    medicine = fields.Many2one('medicine')
    complaint = fields.Text()

    # state = fields.Selection([
    #     ('new', 'طلب جديد'),
    #     ('collected', 'تم تجميع البيانات الأساسية'),
    #     ('directed', 'تم التوجيه'),
    #     ('done', 'تم الحصول على الخدمة'),
    #     ('follow_up', 'متابعة شهرية'),
    # ], default='new', group_expand='_group_expand_states')
    #
    #
    # def _group_expand_states(self, states, domain, order):
    #     # return [key for key, val in type(self).state.selection]
    #     return ['new', 'collected', 'directed', 'done', 'follow_up']

    status = fields.Many2one('request.state', string="Status", group_expand='_read_group_status_ids')

    @api.onchange('status','basic_service')
    def onchange_status(self):
        if self.status.monthly and self.basic_service.type != 'medicine_monthly':
            raise UserError('Monthly Follow Up is only available for "Medicine Monthly" service')

    @api.model
    def _read_group_status_ids(self, stages, domain, order):
        return self.env['request.state'].search([], order=order)

    kanban_state = fields.Selection([
        ('done', 'In Progress'),
        ('blocked', 'On Hold')], string='Progress',
        copy=False, default='done', required=True)

    monthly_follow_up = fields.One2many('monthly.follow.up', 'request_id')

    show_status_monthly = fields.Boolean(related='status.monthly')
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

