# -*- coding: utf-8 -*-
import time
import datetime
import re

from email.message import Message
from email.utils import formataddr

from openerp.addons.mail.mail_message import decode
from openerp.osv import fields, orm, osv
from openerp.tools.translate import _
from openerp.tools import append_content_to_html
from openerp import SUPERUSER_ID

import openerp.addons.decimal_precision as dp

def decode_header(message, header, separator=' '):
    return separator.join(map(decode, filter(None, message.get_all(header, []))))
    
class MailThread(orm.AbstractModel):

    _inherit = 'mail.thread'       
        
    def message_route(self, cr, uid, message, message_dict, model=None, thread_id=None,
                      custom_values=None, context=None):
            
        if not isinstance(message, Message):
            raise TypeError('message must be an email.message.Message at this point')
            
        subject = decode_header(message, 'Subject')
        references = decode_header(message, 'References')
        in_reply_to = decode_header(message, 'In-Reply-To')
        thread_references = references or in_reply_to
        
        if not thread_references:                              
            t = re.compile(r'^.*\#(?P<message_id>\<.+\>)\#.*', re.MULTILINE)
            t_parsed = [n.groups() for n in t.finditer(subject)]                       
            if t_parsed:     
                message_id = t_parsed[0][0]                             
                message['References'] = message_id
                message['In-Reply-To'] = message_id
                            
        route = super(MailThread, self).message_route(cr, uid, message, message_dict, 
                                                      model=model, thread_id=thread_id,
                                                      custom_values=custom_values, 
                                                      context=context)
                                                      
        return route
    
class MailMessage(orm.Model):

    _inherit = 'mail.message'   
        
    def create(self, cr, uid, vals, context=None):
        
        this = self.pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context)
        
        if vals.get('type', False) == 'comment':
            catchall_alias = self.pool['ir.config_parameter'].\
                                get_param(cr, uid, "mail.catchall.alias", context=context)
            alias_domain = self.pool['ir.config_parameter'].\
                               get_param(cr, uid, "mail.catchall.domain", context=context)                                
            if alias_domain:
                if vals.get('model', False) == 'mail.group' and \
                             vals.get('res_id', False):
                    group_model = self.pool['mail.group']
                    group = group_model.browse(cr, SUPERUSER_ID, vals.get('res_id'))            
                    if group.alias_id and group.alias_id.alias_name:
                        vals['email_from'] = formataddr((group.name, '%s@%s' % \
                                               (group.alias_id.alias_name, alias_domain)))
                elif catchall_alias:
                    print "yes"
                    vals['email_from'] = formataddr((this.name, '%s@%s' % \
                                                          (catchall_alias, alias_domain)))
                    print vals['email_from']
                
            
        
        # We willen binnenkomenden berichten toekennen aan de res.partner
        # die het bericht heeft verzonden (mits aanwezig)
        if vals.get('model', None) == False and \
           vals.get('res_id', None) == False and \
           vals.get('type', False) == 'email' and \
           vals.get('email_from', False):
            match = re.search(r'[\w\.-]+@[\w\.-]+', vals.get('email_from'))
            partner_id = False
            if match:
                partner_model = self.pool.get('res.partner')
                partner = partner_model.search(cr, 
                                               SUPERUSER_ID, 
                                               [('email', '=', match.group(0))])
                if partner:
                    vals['model'] = 'res.partner'
                    vals['res_id'] = partner[0]

        return super(MailMessage, self).create(cr, uid, vals, context=context)           

class MailMail(orm.Model):

    _inherit = 'mail.mail'

    def create(self, cr, uid, values, context=None):
        # Als het nodig is dat het afzendadres niet van de gebruiker mag zijn
        # maar een vast email adres, dan hier inrichtingen 
        #        if context and context.get('default_model', False) == 'crm.helpdesk':
        #            values['email_from'] = """<plaats hier het mail adres wat zichtbaar
        # moet zijn voor de ontvanger>"""
                
        return super(MailMail, self).create(cr, uid, values, context=context)

    def send_get_mail_subject(self, cr, uid, mail, force=False, partner=None, context=None):
                       
        if mail.mail_message_id and mail.mail_message_id.message_id:
            message_id = ' #%s#'%(mail.mail_message_id.message_id)
        else:
            message_id = False
            
        subject = super(MailMail, self).\
            send_get_mail_subject(cr, uid, mail, 
                                  force=force, 
                                  partner=partner, 
                                  context=context)        
        if subject and message_id:
            # als message_id nog niet in het subject is te vinden
            # deze dan toevoegen
            
            t = re.compile(r'^.*\#(?P<message_id>\<.+\>)\#.*', re.MULTILINE)
            t_parsed = [n.groups() for n in t.finditer(subject)]                       
            if not t_parsed:                                
                subject = '%s%s'%(subject, message_id)
            
        return subject
 