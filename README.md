# s2ubasev8
I was facing problems with the catchall principles on Odoo v8. Mailclients on android phones are not that clever to work with "References" and ""In-Reply-To".

Many replies did not come back into Odoo because of this, resulting in the following error:
"Routing: posting a message without model should be with a parent_id (private mesage)"

What I did is adding the message_id to the subject from every mail sent out by Odoo, also checking the "email_from" address to set on the aliasname when this is defined in the mail group (explicity set). This assures that mailclients will reply on this mail address and not the mailaddress from the user who sends the mail.

It's just a work arround- it's not the solution - but it work's for me and can be handy for other people. Feel free to cantact me if you have any questions.

