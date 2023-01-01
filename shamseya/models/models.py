# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ResUser(models.Model):
    _inherit = 'res.users'

    prefix = fields.Char()


class Case(models.Model):
    _inherit = 'res.partner'
    _description = 'Cases'

    name = fields.Char(required=1)
    code = fields.Char(readonly=0)
    is_case = fields.Boolean(string='Is Patient?')
    date_of_birth = fields.Date(string='Date of Birth')

    # compute age from date of birth
    age = fields.Integer(string='Age', compute="compute_age", store=1)

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
        ('abandoned', 'هجر')
    ], string='Marital Status')

    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 default=lambda self: self.env.user.country_id)
    area = fields.Many2one('area', domain="[('state_id', '=?', country_id)]")

    # request_ids = fields.One2many('plusone.case', 'patient_id', string='Request History')
    create_uid = fields.Many2one('res.users', string='Created By', readonly=0)
    referral = fields.Many2one('referral', string='Refered By')
    income_resource = fields.Many2one('income.resource')
    pension_type = fields.Many2one('pension.type')
    currency_id = fields.Many2one('res.currency', related='country_id.currency_id')
    average_income = fields.Monetary('Average Income', currency_field='currency_id')
    has_insurance = fields.Boolean()
    insurance_type = fields.Many2one('insurance.type')
    insurance_code = fields.Char()

    personal_id_card = fields.Many2many('ir.attachment', 'personal_id_card_rel')
    insurance_card = fields.Many2many('ir.attachment', 'insurance_card_rel')
    health_card = fields.Many2many('ir.attachment', 'health_card_rel')
    other_attachments = fields.Many2many('ir.attachment', 'other_attachments_rel')

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


    @api.model
    def create(self, vals):
        res = super().create(vals)
        serial = self.env['ir.sequence'].next_by_code('case.seq')
        prefix = self.env.user.prefix or '_'
        res.code = f'{prefix}-{serial}'
        return res


class Area(models.Model):
    _name = 'area'

    name = fields.Char(required=1)
    country_id = fields.Many2one('res.country', default=lambda self: self.env.user.country_id)
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', country_id)]")


class Referral(models.Model):
    _name = 'referral'

    name = fields.Char(required=1)


class IncomeResource(models.Model):
    _name = 'income.resource'

    name = fields.Char(required=1)


class PensionType(models.Model):
    _name = 'pension.type'

    name = fields.Char(required=1)


class InsuranceType(models.Model):
    _name = 'insurance.type'

    name = fields.Char(required=1)


class Diagnosis(models.Model):
    _name = 'diagnosis'

    name = fields.Char(required=1)


class MedicalHistoryLine(models.Model):
    _name = 'medical.history.line'

    case_id = fields.Many2one('res.partner',  store=1)
    diagnosis = fields.Many2one('diagnosis', required=1)
    start_date = fields.Date()
    duration_y = fields.Integer()
    duration_m = fields.Integer()
    duration = fields.Char(compute='_calculate_duration')
    medicine = fields.Char()

    @api.depends("start_date")
    def _calculate_duration(self):
        for rec in self:
            if rec.start_date:
                date_format = '%Y-%m-%d'
                current_date = (datetime.today()).strftime(date_format)
                d1 = rec.start_date
                d2 = datetime.strptime(current_date, date_format).date()
                r = relativedelta(d2, d1)
                rec.duration_y = r.years
                rec.duration_m = r.months
                rec.duration = f"{r.years} years, {r.months} months"
            else:
                rec.duration = ""


class CaseRequest(models.Model):
    _name = 'case.request'

    case_id = fields.Many2one('res.partner', domain=[('is_case','=',True)])

    basic_service = fields.Many2one('basic.service')
    description = fields.Text(related='basic_service.description')

    complaint = fields.Text()


class BasicService(models.Model):
    _name = 'basic.service'

    name = fields.Char(required=1)
    description = fields.Text()


