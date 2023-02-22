# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


def get_years():
    year_list = []
    for i in range(2016, 2036):
        year_list.append((i, str(i)))
    return year_list


class ResUser(models.Model):
    _inherit = 'res.users'

    prefix = fields.Char()


class Area(models.Model):
    _name = 'area'

    name = fields.Char(required=1)
    country_id = fields.Many2one('res.country', default=lambda self: self.env.user.country_id)
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', country_id)]")
    partner_ids = fields.One2many('res.partner', 'area')

    @api.model
    def create(self, vals):
        print(self.env.context)
        return super().create(vals)


class Referral(models.Model):
    _name = 'referral'

    name = fields.Char(required=1)


class IncomeResource(models.Model):
    _name = 'income.resource'

    name = fields.Char(required=1)


class PensionType(models.Model):
    _name = 'pension.type'
    name = fields.Char(required=1)


class HealthInsurance(models.Model):
    _name = 'health.insurance'
    name = fields.Char(required=1)
    partner_ids = fields.One2many('res.partner', 'health_insurance_id')


class SocialInsurance(models.Model):
    _name = 'social.insurance'
    name = fields.Char(required=1)
    partner_ids = fields.One2many('res.partner', 'social_insurance_id')


class Diagnosis(models.Model):
    _name = 'diagnosis'
    name = fields.Char(required=1)


class MedicalHistoryLine(models.Model):
    _name = 'medical.history.line'

    case_id = fields.Many2one('res.partner', store=1)
    diagnosis = fields.Many2one('diagnosis', required=1)
    start_date = fields.Date()
    duration_y = fields.Integer()
    duration_m = fields.Integer()
    duration = fields.Char(compute='_calculate_duration')
    medicine = fields.Many2one('medicine')

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


class Medicine(models.Model):
    _name = 'medicine'

    name = fields.Char()
    price = fields.Float()
    types = fields.Many2many('medicine.type', relation='medicine_type_rel')
    requests = fields.Many2many(comodel_name='case.request', relation='request_medicine_rel', readonly=1)


class MedicineType(models.Model):
    _name = 'medicine.type'

    name = fields.Char()
    medicines = fields.Many2many('medicine', relation='medicine_type_rel')


class RequestOperation(models.Model):
    _name = 'service.operation'

    name = fields.Char()
    price = fields.Float()
    requests = fields.One2many(comodel_name='case.request', inverse_name='operation', readonly=1)


class BasicService(models.Model):
    _name = 'basic.service'

    name = fields.Char(required=1)
    medicine = fields.Boolean()
    type = fields.Selection([
        ('insurance_request', _('Insurance Request')),
        ('examination', _('Examination')),
        ('medicine_once', _('Medicine One Time')),
        ('medicine_monthly', _('Medicine Monthly')),
        ('operation', _('Operation')),
        ('inquiry', _('Inquiry')),
        ('other', _('Other')),
    ], default='insurance_request')
    # monthly = fields.Selection([
    #     ('one_time', 'One Time'),
    #     ('monthly', 'Monthly'),
    # ], default='one_time')
    description = fields.Text()


class RequestState(models.Model):
    _name = 'request.state'
    _order = "order_ asc"

    order_ = fields.Integer()

    name = fields.Char()
    description = fields.Text()
    monthly = fields.Boolean()
    type = fields.Selection([
        ('monthly', _('Monthly')),
        ('problem', _('Problem')),
        ('other', _('Other')),
    ], default='other')




class FollowUpIssue(models.Model):
    _name = 'follow.up.issue'

    name = fields.Char(required=True, string="اسم الشكوى")
    number = fields.Char(required=True, string="رقم الشكوى")
    reason = fields.Text(string="سبب/وصف الشكوى")
    against = fields.Char(string="الشكوى ضد")
    applied_to = fields.Char(string="الجهة المقدم لها الشكوى")
    applier = fields.Char(string="اسم مقدم الشكوى")
    case_relation = fields.Char(string="اسم مقدم الشكوى")
    applier_id_no = fields.Char(string="رقم بطاقة مقدم الشكوى")
    phone_follow_up = fields.Char(string="رقم تليفون للمتابعة")
    attachments = fields.Many2many('ir.attachment', relation='issue_attachment_rel')
    date = fields.Date(string="تاريخ تقديم الشكوى", default=fields.Date.context_today)
    follow_up_id = fields.Many2one('monthly.follow.up')
    request_id = fields.Many2one('case.request', default=lambda self:self.follow_up_id.request_id)
    case_id = fields.Many2one('res.partner', domain=[('is_case', '=', True)], related='request_id.case_id')

    kanban_state = fields.Selection([
        ('done', 'In Progress'),
        ('blocked', 'On Hold')], string='Progress',
        copy=False, default='done', required=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Starred", tracking=True)

    m_status = fields.Selection([('open', 'Open'), ('close', 'Closed')], group_expand='_group_expand_states',
                                string='Status', default='open')

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).m_status.selection]


class Specialization(models.Model):
    _name = 'specialization'
    name = fields.Char(required=1)


class WorkingHours(models.Model):
    _name = 'working.hours'
    name = fields.Char(required=1)


class Emergency(models.Model):
    _name = 'emergency'
    name = fields.Char(required=1)


class Hospital(models.Model):
    _name = 'hospital'

    name = fields.Char(required=1)

    country_id = fields.Many2one('res.country', default=lambda self: self.env.user.country_id)

    # state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
    #                            domain="[('country_id', '=?', country_id)]")

    state_id = fields.Many2one("res.country.state", string='State')

    # area = fields.Many2one('area', domain="[('state_id', '=?', state_id)]")
    area = fields.Many2one('area')

    phone = fields.Char()
    address = fields.Text()
    specializations = fields.Many2many('specialization')
    working_hours = fields.Many2one('working.hours')
    currency_id = fields.Many2one('res.currency', related='country_id.currency_id')
    price = fields.Monetary(currency_field='currency_id')
    emergency = fields.Many2one('emergency')


class CaseDocument(models.Model):
    _name = 'case.document'

    name = fields.Char(required=1)

    document = fields.Html()
